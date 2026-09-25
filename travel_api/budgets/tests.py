"""
budgets/tests.py

Model tests for Budget's total/spend calculations, plus API tests for the
budget detail and expense list/create/delete endpoints.
"""
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from destinations.models import Destination
from itineraries.models import Itinerary
from .models import Budget, Expense

User = get_user_model()


def make_destination():
    return Destination.objects.create(
        name='Cairo', country='Egypt', description='Ancient wonders',
        category=Destination.CategoryChoices.CULTURAL, climate=Destination.ClimateChoices.DRY,
        avg_daily_cost=80,
    )


class BudgetModelTests(APITestCase):
    """Tests for the Budget model's computed totals."""

    def setUp(self):
        self.user = User.objects.create_user(username='budgeter', password='StrongPass123')
        self.destination = make_destination()
        self.itinerary = Itinerary.objects.create(
            title='Egypt Trip', destination=self.destination, owner=self.user,
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 10), budget=1200,
        )

    def test_total_budget_sums_categories(self):
        """total_budget should sum all category allocations."""
        budget = Budget.objects.create(
            itinerary=self.itinerary, accommodation_budget=400, food_budget=200,
            activities_budget=150, transport_budget=100,
        )
        self.assertEqual(budget.total_budget, 850)


class BudgetAPITests(APITestCase):
    """API tests for the budget and expense endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(username='apibudgeter', password='StrongPass123')
        self.client.force_authenticate(user=self.user)
        self.destination = make_destination()
        self.itinerary = Itinerary.objects.create(
            title='Egypt Trip', destination=self.destination, owner=self.user,
            start_date=date(2026, 3, 1), end_date=date(2026, 3, 10), budget=1200,
        )

    def test_get_budget_detail_auto_creates_budget(self):
        """GET on the budget detail endpoint should auto-create a Budget if missing."""
        response = self.client.get(f'/api/v1/budgets/{self.itinerary.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Budget.objects.filter(itinerary=self.itinerary).exists())

    def test_create_expense(self):
        """POST to the expense list-create endpoint should create an Expense."""
        data = {
            'itinerary': self.itinerary.id, 'category': 'food',
            'description': 'Dinner', 'amount': 45, 'date': '2026-03-02',
        }
        response = self.client.post(f'/api/v1/budgets/{self.itinerary.id}/expenses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)

    def test_delete_expense(self):
        """DELETE on the expense detail endpoint should remove the expense."""
        expense = Expense.objects.create(
            itinerary=self.itinerary, category='food', description='Lunch', amount=20, date=date(2026, 3, 2),
        )
        response = self.client.delete(f'/api/v1/budgets/expenses/{expense.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)

    def test_other_user_cannot_view_expenses(self):
        """A non-owner, non-collaborator user should get an empty expense list."""
        other = User.objects.create_user(username='otherbudgeter', email='otherbudgeter@example.com', password='pass123456')
        self.client.force_authenticate(user=other)
        response = self.client.get(f'/api/v1/budgets/{self.itinerary.id}/expenses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
