"""bookings/filters.py - FilterSets for bookings and accommodations."""
from django_filters import rest_framework as filters

from .models import Accommodation, Booking


class BookingFilter(filters.FilterSet):
    """Filter bookings by status, date range and item type."""

    check_in_after = filters.DateFilter(field_name='check_in', lookup_expr='gte')
    check_in_before = filters.DateFilter(field_name='check_in', lookup_expr='lte')
    has_accommodation = filters.BooleanFilter(field_name='accommodation', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Booking
        fields = ['status', 'itinerary']


class AccommodationFilter(filters.FilterSet):
    """Filter accommodations by type and nightly price range."""

    min_price = filters.NumberFilter(field_name='price_per_night', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price_per_night', lookup_expr='lte')

    class Meta:
        model = Accommodation
        fields = ['destination', 'accommodation_type', 'is_available']
