"""budgets/urls.py"""
from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('<int:trip_id>/', views.BudgetDetailView.as_view(), name='budget-detail'),
    path('<int:trip_id>/expenses/', views.ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view(), name='expense-detail'),
]
