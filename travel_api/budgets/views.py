from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum
from .models import Budget, Expense
from .serializers import BudgetListSerializer, BudgetDetailSerializer, BudgetCreateUpdateSerializer, ExpenseSerializer
from .filters import BudgetFilter, ExpenseFilter
from travel_api.pagination import SmallPagination

class BudgetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_class = BudgetFilter
    ordering_fields = ['total_amount', 'created_at']
    ordering = ['-created_at']
    def get_queryset(self):
        return Budget.objects.filter(itinerary__owner=self.request.user).select_related('itinerary').prefetch_related('expenses').all()
    def get_serializer_class(self):
        if self.action == 'list': return BudgetListSerializer
        if self.action == 'retrieve': return BudgetDetailSerializer
        if self.action in ('create', 'update', 'partial_update'): return BudgetCreateUpdateSerializer
        return BudgetDetailSerializer
    @action(detail=True, methods=['get'], url_path='summary')
    def budget_summary(self, request, pk=None):
        b = self.get_object()
        bd = dict(b.expenses.values_list('category').annotate(total=Sum('amount')))
        return Response({'total_budget': float(b.total_amount), 'total_spent': float(b.calculate_spent()), 'remaining': float(b.calculate_remaining()), 'percentage_used': b.percentage_used(), 'category_breakdown': {k: float(v) for k, v in bd.items()}})
    @action(detail=True, methods=['get'], url_path='expenses')
    def list_expenses(self, request, pk=None):
        b = self.get_object()
        exps = b.expenses.order_by('-date')
        page = self.paginate_queryset(exps)
        s = ExpenseSerializer(page or exps, many=True)
        return self.get_paginated_response(s.data) if page else Response(s.data)

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ExpenseFilter
    pagination_class = SmallPagination
    ordering_fields = ['amount', 'date', 'category']
    ordering = ['-date']
    def get_queryset(self):
        return Expense.objects.filter(budget__itinerary__owner=self.request.user).select_related('budget').defer('receipt_image', 'updated_at').all()
