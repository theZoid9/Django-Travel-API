"""
destinations/models.py

Destination model: the browsable catalog of tourist destinations that
itineraries, accommodations, activities and reviews all hang off of.
"""
from django.core.validators import MinValueValidator
from django.db import models

from accounts.validators import validate_image_extension, validate_image_file_size


class Destination(models.Model):
    """A tourist destination that can be searched, filtered and booked around."""

    class ClimateChoices(models.TextChoices):
        TROPICAL = 'tropical', 'Tropical'
        DRY = 'dry', 'Dry'
        TEMPERATE = 'temperate', 'Temperate'
        CONTINENTAL = 'continental', 'Continental'
        POLAR = 'polar', 'Polar'

    class CategoryChoices(models.TextChoices):
        BEACH = 'beach', 'Beach'
        MOUNTAIN = 'mountain', 'Mountain'
        CITY = 'city', 'City'
        CULTURAL = 'cultural', 'Cultural'
        ADVENTURE = 'adventure', 'Adventure'
        RELAXATION = 'relaxation', 'Relaxation'

    name = models.CharField(max_length=200, unique=True, help_text='Destination display name.')
    slug = models.SlugField(max_length=220, unique=True, blank=True, help_text='URL-friendly identifier.')
    country = models.CharField(max_length=100, help_text='Country this destination is in.')
    description = models.TextField(help_text='Long-form description shown on the detail page.')
    category = models.CharField(max_length=20, choices=CategoryChoices.choices, help_text='Primary destination category.')
    climate = models.CharField(max_length=20, choices=ClimateChoices.choices, help_text='Dominant climate type.')
    best_time_to_visit = models.CharField(max_length=200, blank=True, help_text='E.g. "April - June".')
    avg_daily_cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
        help_text='Average daily cost in USD, used for budget filtering.',
    )
    image = models.ImageField(
        upload_to='destinations/', null=True, blank=True,
        validators=[validate_image_file_size, validate_image_extension],
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text='Inactive destinations are hidden from search.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['country', 'category']),
            models.Index(fields=['climate']),
            models.Index(fields=['avg_daily_cost']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country}"

    def save(self, *args, **kwargs):
        """Auto-generate a slug from the name if one wasn't supplied."""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        """Model-level validation: latitude/longitude must be provided together."""
        from django.core.exceptions import ValidationError
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError('Both latitude and longitude must be provided together, or neither.')

    @property
    def average_rating(self):
        """Business-logic method: compute the mean review rating for this destination."""
        result = self.reviews.aggregate(models.Avg('rating'))
        return round(result['rating__avg'] or 0, 2)

    def budget_tier(self):
        """Business-logic method: classify the destination by average daily cost."""
        if self.avg_daily_cost < 100:
            return 'budget'
        elif self.avg_daily_cost < 250:
            return 'moderate'
        return 'luxury'
