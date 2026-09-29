from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Tag, Category, Destination
User = get_user_model()

class TagModelTest(TestCase):
    def test_tag_str(self):
        t = Tag.objects.create(name='Beach')
        self.assertEqual(str(t), 'Beach')
        self.assertEqual(t.slug, 'beach')

class CategoryModelTest(TestCase):
    def test_category_str(self):
        c = Category.objects.create(name='Nature')
        self.assertEqual(str(c), 'Nature')
    def test_verbose_name_plural(self):
        self.assertEqual(Category._meta.verbose_name_plural, 'categories')

class DestinationModelTest(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='City')
        self.dest = Destination.objects.create(name='Paris', country='France', city='Paris', category=self.cat)
    def test_destination_str(self):
        self.assertEqual(str(self.dest), 'Paris, France')
    def test_slug_auto(self):
        self.assertTrue(self.dest.slug)
    def test_update_average_rating(self):
        self.dest.update_average_rating()
        self.dest.refresh_from_db()
        self.assertEqual(self.dest.avg_rating, 0.0)

class DestinationAPITest(APITestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Adventure')
        self.dest = Destination.objects.create(name='Tokyo', country='Japan', city='Tokyo', category=self.cat)
    def test_list_destinations(self):
        resp = self.client.get('/api/v1/destinations/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
    def test_retrieve_destination(self):
        resp = self.client.get(f'/api/v1/destinations/{self.dest.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
    def test_featured_action(self):
        resp = self.client.get('/api/v1/destinations/featured/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
    def test_create_requires_admin(self):
        u = User.objects.create_user(username='normal', email='n@e.com', password='pass1234')
        self.client.force_authenticate(u)
        resp = self.client.post('/api/v1/destinations/', {'name': 'Berlin', 'country': 'Germany', 'city': 'Berlin'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
