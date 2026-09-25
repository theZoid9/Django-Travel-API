"""
reviews/tests.py

Model tests for Review's single-target validation, plus API tests for
creating reviews and the helpful custom action.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from destinations.models import Destination
from .models import Review

User = get_user_model()


def make_destination():
    return Destination.objects.create(
        name='Barcelona', country='Spain', description='Gaudi city',
        category=Destination.CategoryChoices.CITY, climate=Destination.ClimateChoices.TEMPERATE,
        avg_daily_cost=110,
    )


class ReviewModelTests(APITestCase):
    """Tests for the Review model's single-target validation."""

    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='StrongPass123')
        self.destination = make_destination()

    def test_clean_requires_exactly_one_target(self):
        """clean() should raise when no target (destination/accommodation/activity) is set."""
        review = Review(
            user=self.user, rating=5, title='Great', content='Loved it', visit_date=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            review.clean()

    def test_clean_accepts_single_target(self):
        """clean() should pass when exactly one target is set."""
        review = Review(
            user=self.user, destination=self.destination, rating=5,
            title='Great', content='Loved it', visit_date=date(2026, 1, 1),
        )
        review.clean()  # should not raise


class ReviewAPITests(APITestCase):
    """API tests for review creation and the helpful custom action."""

    def setUp(self):
        self.user = User.objects.create_user(username='apireviewer', password='StrongPass123')
        self.client.force_authenticate(user=self.user)
        self.destination = make_destination()

    def test_create_review(self):
        """Creating a review should auto-assign the requesting user."""
        data = {
            'destination': self.destination.id, 'rating': 4, 'title': 'Nice trip',
            'content': 'Had a great time', 'visit_date': '2026-01-15',
        }
        response = self.client.post('/api/v1/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.first().user, self.user)

    def test_helpful_action_increments_count(self):
        """The helpful custom action should increment helpful_count."""
        review = Review.objects.create(
            user=self.user, destination=self.destination, rating=5,
            title='Amazing', content='Best trip ever', visit_date=date(2026, 1, 1),
        )
        response = self.client.post(f'/api/v1/reviews/{review.id}/helpful/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['helpful_count'], 1)

    def test_non_owner_cannot_delete_review(self):
        """A user who didn't write the review should not be able to delete it."""
        other = User.objects.create_user(username='otherreviewer', email='otherreviewer@example.com', password='pass123456')
        review = Review.objects.create(
            user=other, destination=self.destination, rating=3,
            title='Ok', content='It was fine', visit_date=date(2026, 1, 1),
        )
        response = self.client.delete(f'/api/v1/reviews/{review.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
