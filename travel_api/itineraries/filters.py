import django_filters
from .models import Itinerary

class ItineraryFilter(django_filters.FilterSet):
    min_start_date = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    max_start_date = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    class Meta:
        model = Itinerary
        fields = ['status', 'owner', 'min_start_date', 'max_start_date']
