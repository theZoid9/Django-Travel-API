import django_filters
from .models import Destination, Category

class DestinationFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(lookup_expr='icontains')
    city = django_filters.CharFilter(lookup_expr='icontains')
    min_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='lte')
    tag = django_filters.CharFilter(field_name='tags__slug', lookup_expr='iexact')
    class Meta:
        model = Destination
        fields = ['country', 'city', 'is_featured', 'category', 'min_rating', 'max_rating']

class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Category
        fields = ['name']
