from django.contrib.auth.models import AbstractUser
from django.db import models
from travel_api.validators import validate_image_file, validate_file_size

class CustomUser(AbstractUser):
    class TravelStyle(models.TextChoices):
        BUDGET = 'budget', 'Budget'
        MID_RANGE = 'mid_range', 'Mid-Range'
        LUXURY = 'luxury', 'Luxury'
        ADVENTURE = 'adventure', 'Adventure'

    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(
        upload_to='avatars/', blank=True, null=True,
        validators=[validate_image_file, validate_file_size],
        help_text='User profile photo (max 5 MB)'
    )
    date_of_birth = models.DateField(blank=True, null=True)
    travel_style = models.CharField(
        max_length=20, choices=TravelStyle.choices,
        blank=True, default='', help_text='Preferred travel style'
    )

    class Meta:
        db_table = 'accounts_custom_user'
        indexes = [models.Index(fields=['email'], name='idx_user_email')]

    def __str__(self):
        return f'{self.username} ({self.email})'

    def get_full_display_name(self):
        return self.get_full_name() or self.username

class UserProfile(models.Model):
    user = models.OneToOneField(
        'CustomUser', on_delete=models.CASCADE,
        related_name='profile', help_text='Linked user account'
    )
    bio = models.TextField(blank=True, default='', help_text='Short biography')
    preferred_currency = models.CharField(max_length=3, default='USD', help_text='ISO 4217 code')
    home_country = models.CharField(max_length=100, blank=True, default='')
    favorite_destinations = models.ManyToManyField(
        'destinations.Destination', blank=True,
        related_name='favorited_by', help_text='Favorite destinations'
    )

    class Meta:
        db_table = 'accounts_user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'Profile of {self.user.username}'

    def favorite_count(self):
        return self.favorite_destinations.count()
