from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from destinations.models import Destination
from .models import Review

User = get_user_model()

class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', email='r@e.com', password='pass1234')
        self.dest = Destination.objects.create(name='Rome', country='Italy', city='Rome')
    def test_review_str(self):
        r = Review.objects.create(user=self.user, destination=self.dest, rating=4, title='Great!')
        self.assertIn('reviewer', str(r))
    def test_rating_validation(self):
        r = Review(user=self.user, destination=self.dest, rating=6, title='Invalid')
        with self.assertRaises(Exception): r.full_clean()

class ReviewSerializerTest(TestCase):
    def test_anonymous_username(self):
        u = User.objects.create_user(username='anon', email='a@e.com', password='pass1234')
        d = Destination.objects.create(name='Berlin', country='Germany', city='Berlin')
        r = Review.objects.create(user=u, destination=d, rating=3, title='OK', is_anonymous=True)
        from .serializers import ReviewSerializer
        self.assertEqual(ReviewSerializer(r).data['username'], 'Anonymous')

class ReviewAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='revapi', email='ra@e.com', password='pass1234')
        self.dest = Destination.objects.create(name='Lisbon', country='Portugal', city='Lisbon')
    def test_create_review_auth(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/v1/reviews/', {'destination': self.dest.pk, 'rating': 5, 'title': 'Amazing!'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    def test_create_review_unauth(self):
        resp = self.client.post('/api/v1/reviews/', {'destination': self.dest.pk, 'rating': 5, 'title': 'Hi'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
    def test_list_reviews(self):
        resp = self.client.get('/api/v1/reviews/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
