import django_filters
from .models import Expense, Budget

class ExpenseFilter(django_filters.FilterSet):
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    min_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    max_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    class Meta:
        model = Expense
        fields = ['budget', 'category', 'min_amount', 'max_amount', 'min_date', 'max_date']

class BudgetFilter(django_filters.FilterSet):
    class Meta:
        model = Budget
        fields = ['itinerary', 'currency']
