"""
itineraries/models.py

Itinerary (the core trip object), Collaboration (through model for the
Itinerary <-> User many-to-many "collaborators" relationship) and
DailyPlan (day-by-day breakdown, linked to bookings.Activity via M2M).
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from destinations.models import Destination


class Itinerary(models.Model):
    """A user's travel itinerary for a trip to a single destination."""

    class StatusChoices(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        BOOKED = 'booked', 'Booked'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    title = models.CharField(max_length=200, help_text='Short trip title, e.g. "Summer in Paris".')
    description = models.TextField(blank=True)
    destination = models.ForeignKey(
        Destination, on_delete=models.PROTECT, related_name='itineraries',
        help_text='Destination this trip is for. Protected from deletion while trips reference it.',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_itineraries',
    )
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='Collaboration',
        related_name='shared_itineraries', blank=True,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    actual_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNING)
    is_public = models.BooleanField(default=False, help_text='Public itineraries can be viewed by anyone.')
    itinerary_pdf = models.FileField(upload_to='itinerary_pdfs/', null=True, blank=True, help_text='Optional exported PDF.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Itineraries'
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.destination.name}"

    def clean(self):
        """Model validation: end date must not precede start date."""
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date must be after start date.')

    @property
    def duration_days(self):
        """Business-logic method: inclusive trip length in days."""
        return (self.end_date - self.start_date).days + 1

    @property
    def budget_remaining(self):
        """Business-logic method: remaining budget after actual spend."""
        return self.budget - self.actual_spent

    def add_collaborator(self, user, role='viewer'):
        """Business-logic method: add a user as a collaborator with a role."""
        collaboration, _ = Collaboration.objects.get_or_create(
            itinerary=self, user=user, defaults={'role': role}
        )
        return collaboration

    def is_over_budget(self):
        """Business-logic method: whether actual spend has exceeded budget."""
        return self.actual_spent > self.budget


class Collaboration(models.Model):
    """Through model connecting an Itinerary to its collaborating users."""

    class RoleChoices(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        EDITOR = 'editor', 'Editor'
        ADMIN = 'admin', 'Admin'

    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='collaborations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaborations')
    role = models.CharField(max_length=10, choices=RoleChoices.choices, default=RoleChoices.VIEWER)
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['itinerary', 'user']
        ordering = ['-invited_at']

    def __str__(self):
        return f"{self.user.username} - {self.itinerary.title} ({self.role})"


class DailyPlan(models.Model):
    """Day-by-day plan within an itinerary, linking to booked activities."""

    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='daily_plans')
    day_number = models.PositiveIntegerField()
    date = models.DateField()
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    activities = models.ManyToManyField('bookings.Activity', related_name='daily_plans', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ['itinerary', 'day_number']
        indexes = [models.Index(fields=['itinerary', 'day_number'])]

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"

    def clean(self):
        """Model validation: date must fall within the itinerary's date range."""
        if self.itinerary_id and self.date:
            if not (self.itinerary.start_date <= self.date <= self.itinerary.end_date):
                raise ValidationError('Daily plan date must fall within the itinerary date range.')
