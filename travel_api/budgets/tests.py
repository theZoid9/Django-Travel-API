from datetime import date
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from itineraries.models import Itinerary
from .models import Budget, Expense

User = get_user_model()

class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='budgetuser', email='bu@e.com', password='pass1234')
        self.itin = Itinerary.objects.create(title='Budget Trip', owner=self.user, start_date=date(2025,5,1), end_date=date(2025,5,10))
        self.budget = Budget.objects.create(itinerary=self.itin, total_amount=5000, currency='USD')
    def test_str(self): self.assertIn('5000', str(self.budget))
    def test_spent_empty(self): self.assertEqual(self.budget.calculate_spent(), 0)
    def test_spent_with_expenses(self):
        Expense.objects.create(budget=self.budget, category='food', amount=100, description='Dinner', date=date(2025,5,2))
        self.assertEqual(self.budget.calculate_spent(), Decimal('100'))
    def test_remaining(self):
        Expense.objects.create(budget=self.budget, category='food', amount=200, description='Lunch', date=date(2025,5,3))
        self.assertEqual(self.budget.calculate_remaining(), Decimal('4800'))
    def test_percentage_used(self):
        Expense.objects.create(budget=self.budget, category='accommodation', amount=1000, description='Hotel', date=date(2025,5,1))
        self.assertEqual(self.budget.percentage_used(), 20.0)

class ExpenseModelTest(TestCase):
    def test_str(self):
        u = User.objects.create_user(username='eu', email='eu@e.com', password='pass1234')
        i = Itinerary.objects.create(title='Trip', owner=u, start_date=date(2025,1,1), end_date=date(2025,1,5))
        b = Budget.objects.create(itinerary=i, total_amount=1000)
        e = Expense.objects.create(budget=b, category='food', amount=50, description='Breakfast', date=date(2025,1,2))
        self.assertIn('50', str(e))
    def test_negative_amount(self):
        u = User.objects.create_user(username='nu', email='nu@e.com', password='pass1234')
        i = Itinerary.objects.create(title='Trip', owner=u, start_date=date(2025,1,1), end_date=date(2025,1,5))
        b = Budget.objects.create(itinerary=i, total_amount=1000)
        e = Expense(budget=b, category='other', amount=-10, description='Invalid', date=date(2025,1,2))
        with self.assertRaises(Exception): e.full_clean()

class BudgetAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='budgetapi', email='ba@e.com', password='pass1234')
        self.client.force_authenticate(self.user)
    def test_create_budget(self):
        i = Itinerary.objects.create(title='Trip', owner=self.user, start_date=date(2025,3,1), end_date=date(2025,3,10))
        resp = self.client.post('/api/v1/budgets/', {'itinerary': i.pk, 'total_amount': 3000, 'currency': 'EUR'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
    def test_list_budgets(self):
        resp = self.client.get('/api/v1/budgets/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

class ExpenseSerializerTest(TestCase):
    def test_negative_amount_fails(self):
        from .serializers import ExpenseSerializer
        u = User.objects.create_user(username='su', email='su@e.com', password='pass1234')
        i = Itinerary.objects.create(title='Trip', owner=u, start_date=date(2025,1,1), end_date=date(2025,1,5))
        b = Budget.objects.create(itinerary=i, total_amount=1000)
        s = ExpenseSerializer(data={'budget': b.pk, 'category': 'food', 'amount': -5, 'description': 'Bad', 'date': '2025-01-02'})
        self.assertFalse(s.is_valid())
