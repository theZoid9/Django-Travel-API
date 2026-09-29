from datetime import date
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from destinations.models import Category, Destination
from itineraries.models import Itinerary
from .models import Accommodation, Activity, AccommodationBooking

User = get_user_model()

class AccommodationModelTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Beach')
        self.dest = Destination.objects.create(name='Bali', country='Indonesia', city='Denpasar', category=cat)
        self.accom = Accommodation.objects.create(name='Beach Resort', destination=self.dest, accommodation_type='resort', price_per_night=150)
    def test_str(self):
        self.assertEqual(str(self.accom), 'Beach Resort (Resort)')
    def test_calculate_total_price(self):
        self.assertEqual(self.accom.calculate_total_price(5), 750)

class ActivityModelTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Adventure')
        dest = Destination.objects.create(name='Queenstown', country='NZ', city='Queenstown', category=cat)
        self.act = Activity.objects.create(name='Bungee Jump', destination=dest, activity_type='adventure', price=200, duration_minutes=60)
    def test_str(self):
        self.assertIn('Bungee Jump', str(self.act))
    def test_duration_display(self):
        self.assertEqual(self.act.duration_display(), '1h')
    def test_is_available_for_booking(self):
        self.assertTrue(self.act.is_available_for_booking(5))
        self.assertFalse(self.act.is_available_for_booking(25))

class BookingAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='booker', email='b@e.com', password='pass1234')
        self.client.force_authenticate(self.user)
    def test_list_accommodations(self):
        resp = self.client.get('/api/v1/accommodations/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
    def test_list_activities(self):
        resp = self.client.get('/api/v1/activities/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

class AccommodationBookingValidationTest(TestCase):
    def test_check_out_before_check_in(self):
        user = User.objects.create_user(username='valuser', email='v@e.com', password='pass1234')
        cat = Category.objects.create(name='Test')
        dest = Destination.objects.create(name='TD', country='TC', city='TC', category=cat)
        accom = Accommodation.objects.create(name='Hotel', destination=dest, accommodation_type='hotel', price_per_night=50)
        itin = Itinerary.objects.create(title='Trip', owner=user, start_date=date(2025,1,1), end_date=date(2025,1,10))
        b = AccommodationBooking(itinerary=itin, accommodation=accom, check_in=date(2025,1,5), check_out=date(2025,1,3))
        with self.assertRaises(Exception):
            b.full_clean()
