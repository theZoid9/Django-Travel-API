from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'travel_style', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Travel Info', {'fields': ('phone', 'avatar', 'date_of_birth', 'travel_style')}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_currency', 'home_country')
