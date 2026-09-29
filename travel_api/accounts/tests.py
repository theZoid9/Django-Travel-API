from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import UserProfile
from .permissions import IsOwner, IsOwnerOrReadOnly

User = get_user_model()

class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser (test@example.com)')

    def test_get_full_display_name(self):
        self.assertEqual(self.user.get_full_display_name(), 'testuser')
        self.user.first_name = 'Test'
        self.user.last_name = 'User'
        self.assertEqual(self.user.get_full_display_name(), 'Test User')

    def test_profile_auto_created(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', email='p@e.com', password='pass1234')

    def test_profile_str(self):
        self.assertEqual(str(self.user.profile), 'Profile of profileuser')

    def test_favorite_count_default(self):
        self.assertEqual(self.user.profile.favorite_count(), 0)

class UserRegistrationAPITest(APITestCase):
    def test_register_success(self):
        resp = self.client.post('/api/v1/accounts/register/', {
            'username': 'newuser', 'email': 'new@example.com',
            'password': 'strongpass123', 'password_confirm': 'strongpass123',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_register_password_mismatch(self):
        resp = self.client.post('/api/v1/accounts/register/', {
            'username': 'newuser', 'email': 'new@example.com',
            'password': 'strongpass123', 'password_confirm': 'wrongpass',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

class LoginAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='loginuser', email='l@e.com', password='loginpass123')

    def test_login_success(self):
        resp = self.client.post('/api/v1/accounts/login/', {'username': 'loginuser', 'password': 'loginpass123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_login_wrong_password(self):
        resp = self.client.post('/api/v1/accounts/login/', {'username': 'loginuser', 'password': 'wrong'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

class ProfileAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileapi', email='pa@e.com', password='pass1234')
        self.client.force_authenticate(self.user)

    def test_get_profile(self):
        resp = self.client.get('/api/v1/accounts/profile/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_profile(self):
        resp = self.client.patch('/api/v1/accounts/profile/', {'bio': 'Travel lover!'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

class ChangePasswordAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pwuser', email='pw@e.com', password='oldpass123')
        self.client.force_authenticate(self.user)

    def test_change_password_success(self):
        resp = self.client.post('/api/v1/accounts/change-password/', {
            'old_password': 'oldpass123', 'new_password': 'newpass456', 'new_password_confirm': 'newpass456',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

class PermissionTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='o@e.com', password='pass1234')
        self.other = User.objects.create_user(username='other', email='ot@e.com', password='pass1234')

    def test_is_owner_permission(self):
        perm = IsOwner()
        class MockObj:
            owner = self.owner
        req = type('Request', (), {'user': self.owner})()
        self.assertTrue(perm.has_object_permission(req, None, MockObj()))
        req.user = self.other
        self.assertFalse(perm.has_object_permission(req, None, MockObj()))
