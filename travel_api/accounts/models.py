"""
accounts/models.py

Custom User model extending AbstractUser, plus a SearchPreference model used
by the trip_search function-based view to persist a user's saved search
filters (demonstrates FBV POST + a simple related model).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_image_file_size


class User(AbstractUser):
    """
    Custom user model with travel-specific profile fields.

    Extends AbstractUser so we keep Django's built-in auth/permission
    machinery while adding the fields this API needs.
    """
    email = models.EmailField(unique=True, help_text='Unique email address used for login/notifications.')
    phone = models.CharField(max_length=20, blank=True, help_text='Contact phone number, optional.')
    date_of_birth = models.DateField(null=True, blank=True, help_text='Used for age-appropriate recommendations.')
    bio = models.TextField(max_length=500, blank=True, help_text='Short user biography.')
    profile_picture = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True,
        validators=[validate_image_file_size],
        help_text='Profile photo, max 5MB.',
    )
    travel_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text='Free-form JSON of preferred climates/categories used for recommendations.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        """Return the user's full name, falling back to username."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def total_trips(self):
        """Business-logic helper: count of itineraries this user owns."""
        return self.owned_itineraries.count()


class SearchPreference(models.Model):
    """
    Stores a user's saved trip-search preferences (used by the
    itineraries.trip_search FBV's POST action).
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='search_preferences'
    )
    name = models.CharField(max_length=100, help_text='Label for this saved search.')
    filters = models.JSONField(default=dict, help_text='Serialized filter/query params.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.name}"
