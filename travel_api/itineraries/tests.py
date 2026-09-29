from datetime import date
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Itinerary, TripCollaborator, DailyPlan

User = get_user_model()

class ItineraryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='itinowner', email='i@e.com', password='pass1234')
    def test_create_itinerary(self):
        i = Itinerary.objects.create(title='Paris Trip', owner=self.user, start_date=date(2025,6,1), end_date=date(2025,6,10))
        self.assertEqual(str(i), 'Paris Trip (Planning)')
    def test_calculate_total_days(self):
        i = Itinerary.objects.create(title='Trip', owner=self.user, start_date=date(2025,6,1), end_date=date(2025,6,5))
        self.assertEqual(i.calculate_total_days(), 5)
    def test_end_before_start(self):
        i = Itinerary(title='Bad', owner=self.user, start_date=date(2025,6,10), end_date=date(2025,6,1))
        with self.assertRaises(Exception): i.full_clean()
    def test_is_collaborator(self):
        i = Itinerary.objects.create(title='Trip', owner=self.user, start_date=date(2025,6,1), end_date=date(2025,6,5))
        other = User.objects.create_user(username='other', email='o@e.com', password='pass1234')
        TripCollaborator.objects.create(itinerary=i, user=other, role='viewer')
        self.assertTrue(i.is_collaborator(other))

class ItineraryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiowner', email='a@e.com', password='pass1234')
        self.client.force_authenticate(self.user)
    def test_create_itinerary(self):
        resp = self.client.post('/api/v1/itineraries/', {'title': 'New Trip', 'start_date': '2025-08-01', 'end_date': '2025-08-10', 'budget_estimate': 5000})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    def test_list_itineraries(self):
        Itinerary.objects.create(title='My Trip', owner=self.user, start_date=date(2025,8,1), end_date=date(2025,8,10))
        resp = self.client.get('/api/v1/itineraries/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
    def test_trip_search(self):
        resp = self.client.get('/api/v1/itinerary/search/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
    def test_itinerary_summary(self):
        i = Itinerary.objects.create(title='Summary Trip', owner=self.user, start_date=date(2025,9,1), end_date=date(2025,9,5))
        resp = self.client.get(f'/api/v1/itineraries/{i.pk}/summary/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

class ItineraryPermissionTest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='own', email='ow@e.com', password='pass1234')
        self.other = User.objects.create_user(username='oth', email='ot@e.com', password='pass1234')
        self.itin = Itinerary.objects.create(title='Owned', owner=self.owner, start_date=date(2025,1,1), end_date=date(2025,1,10))
    def test_other_cannot_update(self):
        self.client.force_authenticate(self.other)
        resp = self.client.patch(f'/api/v1/itineraries/{self.itin.pk}/', {'title': 'Hacked'})
        self.assertIn(resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
