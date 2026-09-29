from django.db import models
from django.conf import settings
from travel_api.validators import validate_rating

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews', help_text='Author')
    destination = models.ForeignKey('destinations.Destination', on_delete=models.CASCADE, related_name='reviews', help_text='Destination')
    rating = models.PositiveSmallIntegerField(help_text='Rating 1-5', validators=[validate_rating])
    title = models.CharField(max_length=200, help_text='Title')
    comment = models.TextField(blank=True, default='')
    is_anonymous = models.BooleanField(default=False, help_text='Anonymous')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'destination')
        indexes = [models.Index(fields=['destination', 'rating'], name='idx_review_dest_rating')]
    def __str__(self):
        a = 'Anonymous' if self.is_anonymous else self.user.username
        return f'{a}: {self.rating}* for {self.destination.name}'
    def clean(self):
        validate_rating(self.rating)

class ActivityReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_reviews', help_text='Author')
    activity = models.ForeignKey('bookings.Activity', on_delete=models.CASCADE, related_name='reviews', help_text='Activity')
    rating = models.PositiveSmallIntegerField(help_text='Rating 1-5', validators=[validate_rating])
    title = models.CharField(max_length=200, help_text='Title')
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'activity')
        indexes = [models.Index(fields=['activity', 'rating'], name='idx_actreview_rating')]
    def __str__(self):
        return f'{self.user.username}: {self.rating}* for {self.activity.name}'
    def clean(self):
        validate_rating(self.rating)
