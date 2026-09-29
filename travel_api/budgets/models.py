from django.db import models
from django.core.exceptions import ValidationError
from travel_api.validators import validate_image_file, validate_file_size

class Budget(models.Model):
    itinerary = models.ForeignKey('itineraries.Itinerary', on_delete=models.CASCADE, related_name='budgets', help_text='Itinerary')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text='Total budget')
    currency = models.CharField(max_length=3, default='USD', help_text='Currency')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.currency} {self.total_amount} for {self.itinerary.title}'
    def calculate_spent(self):
        r = self.expenses.aggregate(total=models.Sum('amount'))
        return r['total'] or 0
    def calculate_remaining(self):
        return self.total_amount - self.calculate_spent()
    def percentage_used(self):
        if self.total_amount == 0: return 0
        return round((self.calculate_spent() / self.total_amount) * 100, 1)

class Expense(models.Model):
    class ExpenseCategory(models.TextChoices):
        ACCOMMODATION = 'accommodation', 'Accommodation'
        TRANSPORT = 'transport', 'Transport'
        FOOD = 'food', 'Food & Drink'
        ACTIVITY = 'activity', 'Activity'
        SHOPPING = 'shopping', 'Shopping'
        OTHER = 'other', 'Other'
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='expenses', help_text='Budget')
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices, help_text='Category')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='Amount')
    description = models.CharField(max_length=255, help_text='Description')
    date = models.DateField(help_text='Date')
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True, validators=[validate_image_file, validate_file_size], help_text='Receipt')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['budget', 'category'], name='idx_expense_budget_cat'),
            models.Index(fields=['date'], name='idx_expense_date'),
        ]
    def __str__(self):
        return f'{self.get_category_display()}: {self.amount} ({self.date})'
    def clean(self):
        if self.amount and self.amount <= 0:
            raise ValidationError('Amount must be positive.')
