"""
reviews/models.py

Review model: a single review can target exactly one of Destination,
Accommodation, or Activity (enforced via clean()).
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from bookings.models import Accommodation, Activity
from destinations.models import Destination


class Review(models.Model):
    """User review/rating for a destination, accommodation, or activity."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True
    )
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True
    )
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    visit_date = models.DateField()
    images = models.JSONField(default=list, blank=True, help_text='List of image URLs attached to the review.')
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['destination', 'rating']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    def clean(self):
        """Model validation: a review must target exactly one item."""
        review_targets = [self.destination, self.accommodation, self.activity]
        if sum(1 for target in review_targets if target) != 1:
            raise ValidationError('Review must be for exactly one item (destination, accommodation, or activity).')

    def mark_helpful(self):
        """Business-logic method: increment the helpful counter."""
        self.helpful_count = models.F('helpful_count') + 1
        self.save(update_fields=['helpful_count'])

    @property
    def target_name(self):
        """Business-logic method: name of whichever item this review is for."""
        target = self.destination or self.accommodation or self.activity
        return getattr(target, 'name', None)
