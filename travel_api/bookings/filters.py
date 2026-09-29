import django_filters
from .models import Accommodation, Activity, AccommodationBooking, ActivityBooking

class AccommodationFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price_per_night', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price_per_night', lookup_expr='lte')
    destination = django_filters.NumberFilter(field_name='destination__id')
    class Meta:
        model = Accommodation
        fields = ['destination', 'accommodation_type', 'is_available', 'min_price', 'max_price']

class ActivityFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    destination = django_filters.NumberFilter(field_name='destination__id')
    class Meta:
        model = Activity
        fields = ['destination', 'activity_type', 'is_available', 'min_price', 'max_price']

class AccommodationBookingFilter(django_filters.FilterSet):
    class Meta:
        model = AccommodationBooking
        fields = ['itinerary', 'status', 'check_in']

class ActivityBookingFilter(django_filters.FilterSet):
    class Meta:
        model = ActivityBooking
        fields = ['itinerary', 'status', 'date']
