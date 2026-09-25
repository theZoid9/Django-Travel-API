"""
bookings/models.py

Accommodation and Activity are bookable catalog items tied to a
Destination; Booking ties a user + itinerary to exactly one of them.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from accounts.validators import validate_image_extension, validate_image_file_size
from destinations.models import Destination


class Accommodation(models.Model):
    """Hotels, hostels, vacation rentals and other stays at a destination."""

    class TypeChoices(models.TextChoices):
        HOTEL = 'hotel', 'Hotel'
        HOSTEL = 'hostel', 'Hostel'
        RENTAL = 'rental', 'Vacation Rental'
        RESORT = 'resort', 'Resort'
        BNB = 'bnb', 'B&B'

    name = models.CharField(max_length=200)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='accommodations')
    accommodation_type = models.CharField(max_length=10, choices=TypeChoices.choices)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    max_guests = models.PositiveIntegerField(default=1)
    amenities = models.JSONField(default=list, blank=True)
    address = models.CharField(max_length=300)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(
        upload_to='accommodations/', null=True, blank=True,
        validators=[validate_image_file_size, validate_image_extension],
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['destination', 'accommodation_type'])]

    def __str__(self):
        return f"{self.name} ({self.get_accommodation_type_display()})"

    def nightly_total(self, nights):
        """Business-logic method: total accommodation cost for a stay length."""
        return self.price_per_night * nights


class Activity(models.Model):
    """Tours, attractions, dining and other experiences at a destination."""

    class CategoryChoices(models.TextChoices):
        TOUR = 'tour', 'Tour'
        ATTRACTION = 'attraction', 'Attraction'
        DINING = 'dining', 'Dining'
        SHOPPING = 'shopping', 'Shopping'
        ENTERTAINMENT = 'entertainment', 'Entertainment'
        OUTDOOR = 'outdoor', 'Outdoor'

    name = models.CharField(max_length=200)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='activities')
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    description = models.TextField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    requirements = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='activities/', null=True, blank=True,
        validators=[validate_image_file_size, validate_image_extension],
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Activities'
        indexes = [models.Index(fields=['destination', 'category'])]

    def __str__(self):
        return f"{self.name} - {self.destination.name}"

    def is_full_day(self):
        """Business-logic method: whether this activity spans a full day."""
        return self.duration_hours >= 6


class Booking(models.Model):
    """A user's booking of either an accommodation or an activity for a trip."""

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    itinerary = models.ForeignKey('itineraries.Itinerary', on_delete=models.CASCADE, related_name='bookings')
    accommodation = models.ForeignKey(
        Accommodation, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings'
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings'
    )
    booking_date = models.DateField()
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    guests_count = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    confirmation_code = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['itinerary']),
        ]

    def __str__(self):
        if self.accommodation:
            return f"Booking: {self.accommodation.name}"
        elif self.activity:
            return f"Booking: {self.activity.name}"
        return f"Booking #{self.id}"

    def clean(self):
        """Model validation: booking must reference exactly one bookable item."""
        if not self.accommodation and not self.activity:
            raise ValidationError('Booking must have either accommodation or activity')
        if self.accommodation and self.activity:
            raise ValidationError('Booking cannot have both accommodation and activity')

    def generate_confirmation_code(self):
        """Business-logic method: deterministic-looking confirmation code."""
        import uuid
        self.confirmation_code = uuid.uuid4().hex[:10].upper()
        return self.confirmation_code

    def calculate_refund(self):
        """Business-logic method: simple refund policy (full refund if pending, half if confirmed)."""
        if self.status == self.StatusChoices.PENDING:
            return self.price
        if self.status == self.StatusChoices.CONFIRMED:
            return self.price / 2
        return 0
