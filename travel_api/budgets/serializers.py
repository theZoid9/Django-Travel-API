"""budgets/serializers.py"""
from rest_framework import serializers

from .models import Budget, Expense


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for individual trip expenses."""

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Expense amount must be greater than zero.')
        return value


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for the per-category trip budget, with computed totals."""

    total_budget = serializers.ReadOnlyField()
    total_spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    expenses = ExpenseSerializer(source='itinerary.expenses', many=True, read_only=True)

    class Meta:
        model = Budget
        fields = '__all__'
        read_only_fields = ['id', 'itinerary', 'created_at', 'updated_at']

    def get_total_spent(self, obj):
        from django.db.models import Sum
        return obj.itinerary.expenses.aggregate(total=Sum('amount'))['total'] or 0

    def get_remaining(self, obj):
        return obj.total_budget - self.get_total_spent(obj)
