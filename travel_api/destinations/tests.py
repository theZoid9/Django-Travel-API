"""
destinations/tests.py

Model tests for Destination plus API tests for the browse ViewSet and the
custom search CBV.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Destination

User = get_user_model()


def make_destination(**kwargs):
    defaults = dict(
        name='Paris', country='France', description='City of lights',
        category=Destination.CategoryChoices.CITY, climate=Destination.ClimateChoices.TEMPERATE,
        avg_daily_cost=150,
    )
    defaults.update(kwargs)
    return Destination.objects.create(**defaults)


class DestinationModelTests(APITestCase):
    """Tests for the Destination model."""

    def test_str_representation(self):
        destination = make_destination()
        self.assertEqual(str(destination), 'Paris, France')

    def test_slug_auto_generated(self):
        destination = make_destination()
        self.assertEqual(destination.slug, 'paris')

    def test_budget_tier_classification(self):
        """budget_tier() should classify cost into budget/moderate/luxury."""
        cheap = make_destination(name='Hanoi', avg_daily_cost=50)
        mid = make_destination(name='Lisbon', avg_daily_cost=150)
        expensive = make_destination(name='Zurich', avg_daily_cost=300)
        self.assertEqual(cheap.budget_tier(), 'budget')
        self.assertEqual(mid.budget_tier(), 'moderate')
        self.assertEqual(expensive.budget_tier(), 'luxury')

    def test_average_rating_with_no_reviews(self):
        """average_rating should be 0 when there are no reviews yet."""
        destination = make_destination()
        self.assertEqual(destination.average_rating, 0)


class DestinationAPITests(APITestCase):
    """Tests for browsing and searching destinations via the API."""

    def setUp(self):
        self.user = User.objects.create_user(username='browser', password='StrongPass123')
        self.client.force_authenticate(user=self.user)
        self.paris = make_destination(name='Paris', country='France', avg_daily_cost=150)
        self.bali = make_destination(
            name='Bali', country='Indonesia', category=Destination.CategoryChoices.BEACH,
            climate=Destination.ClimateChoices.TROPICAL, avg_daily_cost=60,
        )

    def test_list_destinations(self):
        """The destination list endpoint should return active destinations."""
        response = self.client.get('/api/v1/destinations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_climate(self):
        """DjangoFilterBackend should filter destinations by climate."""
        response = self.client.get('/api/v1/destinations/', {'climate': 'tropical'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [d['name'] for d in response.data['results']]
        self.assertIn('Bali', names)
        self.assertNotIn('Paris', names)

    def test_search_view_free_text(self):
        """The custom DestinationSearchView should match on free-text query."""
        url = reverse('destinations:destination-search')
        response = self.client.get(url, {'q': 'Bali'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Bali')

    def test_weather_info_custom_action(self):
        """The weather_info custom action should return climate-based data."""
        url = f'/api/v1/destinations/{self.bali.id}/weather_info/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['climate'], 'tropical')
