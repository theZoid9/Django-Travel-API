from rest_framework import serializers
from .models import Budget, Expense

class ExpenseSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    class Meta:
        model = Expense
        fields = ['id', 'budget', 'category', 'category_display', 'amount', 'description', 'date', 'receipt_image', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    def validate_amount(self, value):
        if value <= 0: raise serializers.ValidationError('Amount must be positive.')
        return value

class BudgetListSerializer(serializers.ModelSerializer):
    itinerary_title = serializers.CharField(source='itinerary.title', read_only=True)
    spent = serializers.SerializerMethodField(help_text='Spent')
    remaining = serializers.SerializerMethodField(help_text='Remaining')
    class Meta:
        model = Budget
        fields = ['id', 'itinerary', 'itinerary_title', 'total_amount', 'currency', 'spent', 'remaining', 'created_at']
        read_only_fields = ['id', 'created_at']
    def get_spent(self, obj): return float(obj.calculate_spent())
    def get_remaining(self, obj): return float(obj.calculate_remaining())

class BudgetDetailSerializer(BudgetListSerializer):
    expenses = ExpenseSerializer(many=True, read_only=True)
    percentage_used = serializers.SerializerMethodField(help_text='Percentage used')
    class Meta(BudgetListSerializer.Meta):
        fields = BudgetListSerializer.Meta.fields + ['expenses', 'percentage_used', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    def get_percentage_used(self, obj): return obj.percentage_used()
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        from django.db.models import Sum
        bd = dict(instance.expenses.values_list('category').annotate(total=Sum('amount')))
        rep['category_breakdown'] = {k: float(v) for k, v in bd.items()}
        return rep

class BudgetCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['itinerary', 'total_amount', 'currency']
    def validate_total_amount(self, value):
        if value < 0: raise serializers.ValidationError('Cannot be negative.')
        return value
    def update(self, instance, validated_data):
        old = instance.total_amount
        instance = super().update(instance, validated_data)
        if 'total_amount' in validated_data:
            from itineraries.models import ActivityLog
            ActivityLog.objects.create(itinerary=instance.itinerary, user=self.context['request'].user, action='budget_updated', details={'old': str(old), 'new': str(instance.total_amount)})
        return instance
