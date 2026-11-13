from django.urls import path
from django.shortcuts import get_object_or_404
from .models import Budget
from .views import ExpenseViewSet

app_name = 'budgets'

class BudgetExpensesView(ExpenseViewSet):
    def get_parent(self):
        return get_object_or_404(Budget, pk=self.kwargs['budget_id'], itinerary__owner=self.request.user)
    def get_queryset(self):
        return super().get_queryset().filter(budget=self.get_parent())
    def create(self, request, *args, **kwargs):
        parent = self.get_parent()
        data = request.data.copy()
        data['budget'] = parent.pk
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        from rest_framework.response import Response
        return Response(serializer.data, status=201)

urlpatterns = [path('budgets/<int:budget_id>/expenses/', BudgetExpensesView.as_view({'get': 'list', 'post': 'create'}), name='budget_expenses')]
