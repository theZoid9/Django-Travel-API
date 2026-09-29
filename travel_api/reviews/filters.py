import django_filters
from .models import Review, ActivityReview

class ReviewFilter(django_filters.FilterSet):
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    class Meta:
        model = Review
        fields = ['destination', 'user', 'min_rating', 'max_rating']

class ActivityReviewFilter(django_filters.FilterSet):
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    class Meta:
        model = ActivityReview
        fields = ['activity', 'user', 'min_rating']
