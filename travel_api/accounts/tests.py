"""
accounts/tests.py

Model tests for the custom User model plus API tests for registration,
login, profile retrieval/update, and password change/reset.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserModelTests(APITestCase):
    """Tests for the custom User model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='alice', email='alice@example.com', password='StrongPass123',
            first_name='Alice', last_name='Doe',
        )

    def test_str_representation(self):
        """__str__ should return the username."""
        self.assertEqual(str(self.user), 'alice')

    def test_full_name_property(self):
        """full_name should combine first and last name."""
        self.assertEqual(self.user.full_name, 'Alice Doe')

    def test_full_name_falls_back_to_username(self):
        """full_name should fall back to username when no first/last name set."""
        user = User.objects.create_user(username='bob', password='StrongPass123')
        self.assertEqual(user.full_name, 'bob')

    def test_email_uniqueness(self):
        """Creating a second user with the same email should fail at the DB level."""
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(username='alice2', email='alice@example.com', password='x')


class AuthenticationAPITests(APITestCase):
    """Tests for the registration and login endpoints."""

    def test_register_creates_user_and_returns_tokens(self):
        """POST /accounts/register/ should create a user and return JWT tokens."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser', 'email': 'new@example.com',
            'password': 'StrongPass123', 'password_confirm': 'StrongPass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data['tokens'])
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_rejects_mismatched_passwords(self):
        """Registration should fail with a 400 when passwords don't match."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser2', 'email': 'new2@example.com',
            'password': 'StrongPass123', 'password_confirm': 'Different123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """POST /accounts/login/ with valid credentials should return tokens."""
        User.objects.create_user(username='loginuser', password='StrongPass123')
        url = reverse('accounts:login')
        response = self.client.post(url, {'username': 'loginuser', 'password': 'StrongPass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['tokens'])

    def test_login_invalid_credentials(self):
        """Login with a wrong password should return 401."""
        User.objects.create_user(username='loginuser2', password='StrongPass123')
        url = reverse('accounts:login')
        response = self.client.post(url, {'username': 'loginuser2', 'password': 'WrongPass'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileAPITests(APITestCase):
    """Tests for the authenticated profile endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='StrongPass123')
        self.client.force_authenticate(user=self.user)

    def test_get_profile_requires_authentication(self):
        """Unauthenticated requests to the profile endpoint should be rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_own_profile(self):
        """An authenticated user should be able to fetch their own profile."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'profileuser')

    def test_update_own_profile(self):
        """PATCH should update the requesting user's own profile fields."""
        response = self.client.patch(reverse('accounts:profile'), {'bio': 'Loves travel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Loves travel')


class PasswordChangeAPITests(APITestCase):
    """Tests for the password-change endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username='pwuser', password='OldPass123')
        self.client.force_authenticate(user=self.user)

    def test_password_change_success(self):
        """A correct old password should allow setting a new one."""
        url = reverse('accounts:password-change')
        response = self.client.post(url, {'old_password': 'OldPass123', 'new_password': 'NewPass456'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass456'))

    def test_password_change_wrong_old_password(self):
        """An incorrect old password should be rejected with 400."""
        url = reverse('accounts:password-change')
        response = self.client.post(url, {'old_password': 'WrongOld', 'new_password': 'NewPass456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
