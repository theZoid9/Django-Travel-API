"""
bookings/tests.py

Model tests for Booking's validation/business logic, plus API tests for
booking creation, confirm/cancel actions, and bulk update.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from destinations.models import Destination
from itineraries.models import Itinerary
from .models import Accommodation, Activity, Booking

User = get_user_model()


def make_destination():
    return Destination.objects.create(
        name='Tokyo', country='Japan', description='Bright lights',
        category=Destination.CategoryChoices.CITY, climate=Destination.ClimateChoices.TEMPERATE,
        avg_daily_cost=200,
    )


class BookingModelTests(APITestCase):
    """Tests for the Booking model's validation and business logic."""

    def setUp(self):
        self.user = User.objects.create_user(username='booker', password='StrongPass123')
        self.destination = make_destination()
        self.itinerary = Itinerary.objects.create(
            title='Tokyo Trip', destination=self.destination, owner=self.user,
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 5), budget=1500,
        )
        self.accommodation = Accommodation.objects.create(
            name='Shinjuku Hotel', destination=self.destination,
            accommodation_type=Accommodation.TypeChoices.HOTEL,
            description='Central hotel', price_per_night=100, address='Shinjuku',
        )

    def test_clean_requires_one_bookable_item(self):
        """clean() should raise when neither accommodation nor activity is set."""
        booking = Booking(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 1), price=100,
        )
        with self.assertRaises(ValidationError):
            booking.clean()

    def test_clean_rejects_both_items(self):
        """clean() should raise when both accommodation and activity are set."""
        activity = Activity.objects.create(
            name='Sushi Class', destination=self.destination, category=Activity.CategoryChoices.DINING,
            description='Learn to make sushi', duration_hours=2, price=50,
        )
        booking = Booking(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 1),
            price=100, accommodation=self.accommodation, activity=activity,
        )
        with self.assertRaises(ValidationError):
            booking.clean()

    def test_calculate_refund_pending(self):
        """A pending booking should be fully refundable."""
        booking = Booking.objects.create(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 1),
            price=200, accommodation=self.accommodation, status=Booking.StatusChoices.PENDING,
        )
        self.assertEqual(booking.calculate_refund(), 200)

    def test_calculate_refund_confirmed(self):
        """A confirmed booking should be half-refundable."""
        booking = Booking.objects.create(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 1),
            price=200, accommodation=self.accommodation, status=Booking.StatusChoices.CONFIRMED,
        )
        self.assertEqual(booking.calculate_refund(), 100)


class BookingAPITests(APITestCase):
    """API tests for booking creation, custom actions, and bulk update."""

    def setUp(self):
        self.user = User.objects.create_user(username='apibooker', password='StrongPass123')
        self.client.force_authenticate(user=self.user)
        self.destination = make_destination()
        self.itinerary = Itinerary.objects.create(
            title='Tokyo Trip', destination=self.destination, owner=self.user,
            start_date=date(2026, 9, 1), end_date=date(2026, 9, 5), budget=1500,
        )
        self.accommodation = Accommodation.objects.create(
            name='Shinjuku Hotel', destination=self.destination,
            accommodation_type=Accommodation.TypeChoices.HOTEL,
            description='Central hotel', price_per_night=100, address='Shinjuku',
        )

    def test_create_booking(self):
        """Creating a booking should succeed and auto-assign the user."""
        data = {
            'itinerary': self.itinerary.id, 'accommodation': self.accommodation.id,
            'booking_date': '2026-09-01', 'price': 300,
        }
        response = self.client.post('/api/v1/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertTrue(Booking.objects.first().confirmation_code)

    def test_confirm_action(self):
        """The confirm custom action should move a pending booking to confirmed."""
        booking = Booking.objects.create(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 1),
            price=300, accommodation=self.accommodation,
        )
        response = self.client.post(f'/api/v1/bookings/{booking.id}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.StatusChoices.CONFIRMED)

    def test_cancel_action_returns_refund(self):
        """The cancel custom action should report a refund_amount."""
        booking = Booking.objects.create(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 1),
            price=300, accommodation=self.accommodation, status=Booking.StatusChoices.CONFIRMED,
        )
        response = self.client.post(f'/api/v1/bookings/{booking.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['refund_amount'], 150)

    def test_bulk_update_bookings(self):
        """bulk_update_bookings should update multiple bookings atomically."""
        b1 = Booking.objects.create(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 1),
            price=100, accommodation=self.accommodation,
        )
        b2 = Booking.objects.create(
            user=self.user, itinerary=self.itinerary, booking_date=date(2026, 9, 2),
            price=150, accommodation=self.accommodation,
        )
        payload = {'updates': [{'id': b1.id, 'status': 'confirmed'}, {'id': b2.id, 'status': 'cancelled'}]}
        response = self.client.post('/api/v1/bookings/bulk-update/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 2)
        b1.refresh_from_db()
        b2.refresh_from_db()
        self.assertEqual(b1.status, 'confirmed')
        self.assertEqual(b2.status, 'cancelled')

    def test_cannot_access_others_booking(self):
        """A user should not be able to retrieve another user's booking via BookingDetailView."""
        other = User.objects.create_user(username='otherbooker', email='otherbooker@example.com', password='pass123456')
        booking = Booking.objects.create(
            user=other, itinerary=self.itinerary, booking_date=date(2026, 9, 1),
            price=100, accommodation=self.accommodation,
        )
        response = self.client.get(f'/api/v1/bookings/{booking.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
