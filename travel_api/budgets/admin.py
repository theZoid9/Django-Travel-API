from django.contrib import admin
from .models import Budget, Expense


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('itinerary', 'total_budget')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('itinerary', 'category', 'description', 'amount', 'date')
    list_filter = ('category',)
