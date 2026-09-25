"""
itineraries/tests.py

Model tests for Itinerary/Collaboration/DailyPlan, plus API tests for the
ItineraryViewSet covering CRUD, ownership permissions, and collaboration.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from destinations.models import Destination
from .models import Collaboration, Itinerary

User = get_user_model()


def make_destination():
    return Destination.objects.create(
        name='Rome', country='Italy', description='Ancient city',
        category=Destination.CategoryChoices.CULTURAL, climate=Destination.ClimateChoices.TEMPERATE,
        avg_daily_cost=120,
    )


class ItineraryModelTests(APITestCase):
    """Tests for the Itinerary model's business logic."""

    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='StrongPass123')
        self.destination = make_destination()
        self.itinerary = Itinerary.objects.create(
            title='Roman Holiday', destination=self.destination, owner=self.user,
            start_date=date(2026, 6, 1), end_date=date(2026, 6, 7), budget=2000,
        )

    def test_str_representation(self):
        self.assertEqual(str(self.itinerary), 'Roman Holiday - Rome')

    def test_duration_days(self):
        """duration_days should be inclusive of both start and end dates."""
        self.assertEqual(self.itinerary.duration_days, 7)

    def test_budget_remaining(self):
        self.itinerary.actual_spent = 500
        self.assertEqual(self.itinerary.budget_remaining, 1500)

    def test_add_collaborator(self):
        """add_collaborator should create a Collaboration record with the given role."""
        collaborator = User.objects.create_user(username='collab', email='collab@example.com', password='StrongPass123')
        self.itinerary.add_collaborator(collaborator, role='editor')
        self.assertTrue(
            Collaboration.objects.filter(itinerary=self.itinerary, user=collaborator, role='editor').exists()
        )

    def test_clean_rejects_end_before_start(self):
        """clean() should raise a ValidationError when end_date precedes start_date."""
        from django.core.exceptions import ValidationError
        bad = Itinerary(
            title='Bad Trip', destination=self.destination, owner=self.user,
            start_date=date(2026, 6, 10), end_date=date(2026, 6, 1), budget=100,
        )
        with self.assertRaises(ValidationError):
            bad.clean()


class ItineraryAPITestCase(APITestCase):
    """Test itinerary CRUD operations via the ViewSet."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.destination = make_destination()
        self.itinerary = Itinerary.objects.create(
            title='Paris Trip', destination=self.destination, owner=self.user,
            start_date=date(2026, 6, 1), end_date=date(2026, 6, 7), budget=2000,
        )

    def test_list_itineraries(self):
        """Retrieving the list should only include the current user's trips."""
        response = self.client.get('/api/v1/itineraries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_itinerary(self):
        """Creating a new itinerary should succeed and auto-assign the owner."""
        data = {
            'title': 'Rome Adventure', 'destination_id': self.destination.id,
            'start_date': '2026-07-01', 'end_date': '2026-07-10', 'budget': 3000,
        }
        response = self.client.post('/api/v1/itineraries/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Itinerary.objects.count(), 2)

    def test_update_itinerary(self):
        """PATCH should update fields on an itinerary the user owns."""
        response = self.client.patch(f'/api/v1/itineraries/{self.itinerary.id}/', {'budget': 2500})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.itinerary.refresh_from_db()
        self.assertEqual(self.itinerary.budget, 2500)

    def test_delete_itinerary(self):
        """DELETE should remove the itinerary."""
        response = self.client.delete(f'/api/v1/itineraries/{self.itinerary.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Itinerary.objects.count(), 0)

    def test_unauthorized_access(self):
        """Unauthenticated requests should be rejected with 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/itineraries/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_update_others_itinerary(self):
        """A user should not be able to update another user's itinerary."""
        other_user = User.objects.create_user(username='other', email='other@example.com', password='pass123456')
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(f'/api/v1/itineraries/{self.itinerary.id}/', {'budget': 5000})
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

    def test_duplicate_action(self):
        """The duplicate custom action should create a copy owned by the requester."""
        response = self.client.post(f'/api/v1/itineraries/{self.itinerary.id}/duplicate/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Itinerary.objects.count(), 2)

    def test_upcoming_trips_action(self):
        """upcoming_trips should only return trips starting today or later."""
        past = Itinerary.objects.create(
            title='Past Trip', destination=self.destination, owner=self.user,
            start_date=date.today() - timedelta(days=30), end_date=date.today() - timedelta(days=25), budget=500,
        )
        response = self.client.get('/api/v1/itineraries/upcoming/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [t['title'] for t in response.data['results']]
        self.assertNotIn('Past Trip', titles)


class PermissionTestCase(APITestCase):
    """Test role-based permissions on itineraries (owner/collaborator/viewer)."""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner2', email='owner2@example.com', password='pass123456')
        self.collaborator = User.objects.create_user(username='collab2', email='collab2@example.com', password='pass123456')
        self.viewer = User.objects.create_user(username='viewer2', email='viewer2@example.com', password='pass123456')
        self.destination = make_destination()
        self.itinerary = Itinerary.objects.create(
            title='Test Trip', destination=self.destination, owner=self.owner,
            start_date=date(2026, 8, 1), end_date=date(2026, 8, 5), budget=1000,
        )

    def test_owner_can_edit(self):
        """The trip owner should always be able to edit their trip."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(f'/api/v1/itineraries/{self.itinerary.id}/', {'title': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_editor_collaborator_can_edit(self):
        """A collaborator with the 'editor' role should be able to edit."""
        self.itinerary.add_collaborator(self.collaborator, role='editor')
        self.client.force_authenticate(user=self.collaborator)
        response = self.client.patch(f'/api/v1/itineraries/{self.itinerary.id}/', {'title': 'Updated by Collab'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_collaborator_cannot_edit(self):
        """A collaborator with the 'viewer' role should not be able to edit."""
        self.itinerary.add_collaborator(self.viewer, role='viewer')
        self.client.force_authenticate(user=self.viewer)
        response = self.client.patch(f'/api/v1/itineraries/{self.itinerary.id}/', {'title': 'Nope'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_collaborator_can_read(self):
        """A viewer-role collaborator should still be able to read the trip."""
        self.itinerary.add_collaborator(self.viewer, role='viewer')
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(f'/api/v1/itineraries/{self.itinerary.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
