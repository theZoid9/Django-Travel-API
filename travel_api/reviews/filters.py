"""reviews/filters.py - FilterSet for reviews."""
from django_filters import rest_framework as filters

from .models import Review


class ReviewFilter(filters.FilterSet):
    """Filter reviews by rating range and target type."""

    min_rating = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='rating', lookup_expr='lte')

    class Meta:
        model = Review
        fields = ['destination', 'accommodation', 'activity', 'rating']
