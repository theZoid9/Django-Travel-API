from django.db import models
from django.core.exceptions import ValidationError
from travel_api.validators import validate_image_file, validate_file_size

class Accommodation(models.Model):
    class AccommodationType(models.TextChoices):
        HOTEL = 'hotel', 'Hotel'
        APARTMENT = 'apartment', 'Apartment'
        HOSTEL = 'hostel', 'Hostel'
        VILLA = 'villa', 'Villa'
        RESORT = 'resort', 'Resort'
        GUESTHOUSE = 'guesthouse', 'Guest House'
    name = models.CharField(max_length=200, help_text='Name')
    destination = models.ForeignKey('destinations.Destination', on_delete=models.CASCADE, related_name='accommodations', help_text='Destination')
    accommodation_type = models.CharField(max_length=20, choices=AccommodationType.choices, help_text='Type')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price/night')
    address = models.TextField(blank=True, default='')
    amenities = models.JSONField(blank=True, default=list, help_text='Amenities list')
    rating = models.FloatField(default=0.0)
    image = models.ImageField(upload_to='accommodations/', blank=True, null=True, validators=[validate_image_file])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['destination'], name='idx_accom_dest'),
            models.Index(fields=['price_per_night'], name='idx_accom_price'),
        ]
    def __str__(self):
        return f'{self.name} ({self.get_accommodation_type_display()})'
    def calculate_total_price(self, nights):
        return self.price_per_night * nights

class Activity(models.Model):
    class ActivityType(models.TextChoices):
        ADVENTURE = 'adventure', 'Adventure'
        CULTURAL = 'cultural', 'Cultural'
        NATURE = 'nature', 'Nature'
        FOOD = 'food', 'Food & Drink'
        SHOPPING = 'shopping', 'Shopping'
        ENTERTAINMENT = 'entertainment', 'Entertainment'
        TRANSPORT = 'transport', 'Transport'
    name = models.CharField(max_length=200, help_text='Name')
    destination = models.ForeignKey('destinations.Destination', on_delete=models.CASCADE, related_name='activities', help_text='Destination')
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices, help_text='Type')
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price/person')
    duration_minutes = models.PositiveIntegerField(help_text='Duration (min)')
    description = models.TextField(blank=True, default='')
    rating = models.FloatField(default=0.0)
    image = models.ImageField(upload_to='activities/', blank=True, null=True, validators=[validate_image_file])
    is_available = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'activities'
        indexes = [models.Index(fields=['destination'], name='idx_activity_dest')]
    def __str__(self):
        return f'{self.name} ({self.get_activity_type_display()})'
    def is_available_for_booking(self, participants):
        return self.is_available and participants <= self.max_participants
    def duration_display(self):
        h, m = divmod(self.duration_minutes, 60)
        if h and m: return f'{h}h {m}m'
        if h: return f'{h}h'
        return f'{m}m'

class AccommodationBooking(models.Model):
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
    itinerary = models.ForeignKey('itineraries.Itinerary', on_delete=models.CASCADE, related_name='accommodation_bookings', help_text='Itinerary')
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='bookings', help_text='Accommodation')
    check_in = models.DateField(help_text='Check-in')
    check_out = models.DateField(help_text='Check-out')
    guests_count = models.PositiveIntegerField(default=1, help_text='Guests')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Total price')
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    special_requests = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['itinerary'], name='idx_accombooking_itin')]
    def __str__(self):
        return f'{self.accommodation.name} ({self.check_in} -> {self.check_out})'
    def clean(self):
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError('Check-out must be after check-in.')
    def calculate_total_price(self):
        nights = (self.check_out - self.check_in).days
        return self.accommodation.price_per_night * nights

class ActivityBooking(models.Model):
    class BookingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
    itinerary = models.ForeignKey('itineraries.Itinerary', on_delete=models.CASCADE, related_name='activity_bookings', help_text='Itinerary')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='bookings', help_text='Activity')
    date = models.DateField(help_text='Date')
    participants_count = models.PositiveIntegerField(default=1, help_text='Participants')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Total price')
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    special_requests = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['itinerary'], name='idx_actbooking_itin')]
    def __str__(self):
        return f'{self.activity.name} on {self.date}'
    def calculate_total_price(self):
        return self.activity.price * self.participants_count
    def clean(self):
        if self.activity_id and self.participants_count:
            act = Activity.objects.get(pk=self.activity_id)
            if self.participants_count > act.max_participants:
                raise ValidationError(f'Max participants is {act.max_participants}.')
