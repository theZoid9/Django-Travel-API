from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class Itinerary(models.Model):
    class TripStatus(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        BOOKED = 'booked', 'Booked'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    title = models.CharField(max_length=200, help_text='Trip title')
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='itineraries', help_text='Owner')
    start_date = models.DateField(help_text='Start date')
    end_date = models.DateField(help_text='End date')
    status = models.CharField(max_length=20, choices=TripStatus.choices, default=TripStatus.PLANNING, help_text='Status')
    budget_estimate = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Budget estimate')
    companions = models.ManyToManyField(settings.AUTH_USER_MODEL, through='TripCollaborator', related_name='shared_itineraries', blank=True, help_text='Companions')
    cover_image = models.ImageField(upload_to='itineraries/', blank=True, null=True, help_text='Cover image')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner'], name='idx_itin_owner'),
            models.Index(fields=['status'], name='idx_itin_status'),
            models.Index(fields=['start_date'], name='idx_itin_start'),
        ]
    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'
    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date must be on or after start date.')
    def calculate_total_days(self):
        return (self.end_date - self.start_date).days + 1
    def calculate_total_cost(self):
        a = sum(b.total_price for b in self.accommodation_bookings.filter(status='confirmed'))
        act = sum(b.total_price for b in self.activity_bookings.filter(status='confirmed'))
        return a + act
    def is_collaborator(self, user):
        return self.collaborators.filter(user=user).exists()
    def can_edit(self, user):
        if user == self.owner: return True
        return self.collaborators.filter(user=user, role__in=['owner', 'collaborator']).exists()

class TripCollaborator(models.Model):
    class CollaboratorRole(models.TextChoices):
        OWNER = 'owner', 'Owner'
        COLLABORATOR = 'collaborator', 'Collaborator'
        VIEWER = 'viewer', 'Viewer'
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='collaborators', help_text='Itinerary')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trip_collaborations', help_text='User')
    role = models.CharField(max_length=20, choices=CollaboratorRole.choices, default=CollaboratorRole.VIEWER, help_text='Role')
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('itinerary', 'user')
        indexes = [models.Index(fields=['user', 'role'], name='idx_collab_user_role')]
    def __str__(self):
        return f'{self.user.username} as {self.get_role_display()} on {self.itinerary.title}'

class DailyPlan(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='daily_plans', help_text='Itinerary')
    day_number = models.PositiveIntegerField(help_text='Day number')
    date = models.DateField(help_text='Date')
    title = models.CharField(max_length=200, blank=True, default='', help_text='Day title')
    notes = models.TextField(blank=True, default='')
    class Meta:
        ordering = ['day_number']
        unique_together = ('itinerary', 'day_number')
    def __str__(self):
        return f'Day {self.day_number}: {self.title or self.date}'
    def clean(self):
        if self.day_number and self.day_number < 1:
            raise ValidationError('Day number must be at least 1.')

class DayActivity(models.Model):
    daily_plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, related_name='day_activities', help_text='Daily plan')
    activity = models.ForeignKey('bookings.Activity', on_delete=models.CASCADE, related_name='day_schedules', help_text='Activity')
    start_time = models.TimeField(help_text='Start time')
    end_time = models.TimeField(help_text='End time')
    notes = models.TextField(blank=True, default='')
    order = models.PositiveIntegerField(default=0, help_text='Order')
    class Meta:
        ordering = ['order', 'start_time']
    def __str__(self):
        return f'{self.activity.name} at {self.start_time}'

class ActivityLog(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='activity_logs', help_text='Itinerary')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activity_logs', help_text='User')
    action = models.CharField(max_length=100, help_text='Action')
    details = models.JSONField(blank=True, default=dict, help_text='Details')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.action} by {self.user} on {self.itinerary.title}'
