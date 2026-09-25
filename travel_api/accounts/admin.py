from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SearchPreference, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin config for the custom User model."""
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Travel Profile', {'fields': ('phone', 'date_of_birth', 'bio', 'profile_picture', 'travel_preferences')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')


@admin.register(SearchPreference)
class SearchPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
