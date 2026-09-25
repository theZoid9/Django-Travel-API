"""
destinations/viewsets.py

ReadOnlyModelViewSet for browsing destinations (public read access), with
custom actions for popular activities and weather info.
"""
from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .filters import DestinationFilter
from .models import Destination
from .serializers import DestinationDetailSerializer, DestinationListSerializer


class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Browse destinations (read-only for regular users; admins manage data
    via the Django admin). Supports filtering, search, ordering and two
    custom detail actions.
    """
    queryset = Destination.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DestinationFilter
    search_fields = ['name', 'description', 'country']
    ordering_fields = ['name', 'avg_daily_cost', 'created_at']

    def get_queryset(self):
        """Query optimization: annotate review/itinerary counts up front."""
        return (
            Destination.objects.filter(is_active=True)
            .annotate(
                review_count=Count('reviews', distinct=True),
                itinerary_count=Count('itineraries', distinct=True),
            )
            .prefetch_related('activities', 'accommodations')
            .order_by('name')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return DestinationListSerializer
        return DestinationDetailSerializer

    @extend_schema(description='Return the top 5 available activities for this destination, ranked by booking count.')
    @action(detail=True, methods=['get'])
    def popular_activities(self, request, pk=None):
        """Custom action: most popular activities for a destination, ranked by bookings."""
        from bookings.serializers import ActivitySerializer
        destination = self.get_object()
        activities = (
            destination.activities.filter(is_available=True)
            .annotate(booking_count=Count('bookings'))
            .order_by('-booking_count')[:5]
        )
        serializer = ActivitySerializer(activities, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(description='Return static seasonal weather guidance for this destination based on its climate.')
    @action(detail=True, methods=['get'])
    def weather_info(self, request, pk=None):
        """Custom action: seasonal weather guidance derived from the climate field."""
        destination = self.get_object()
        weather_by_climate = {
            'tropical': {'season': 'Warm & humid year-round', 'avg_temp_c': '25-32'},
            'dry': {'season': 'Hot days, cool nights', 'avg_temp_c': '20-38'},
            'temperate': {'season': 'Four distinct seasons', 'avg_temp_c': '5-25'},
            'continental': {'season': 'Cold winters, warm summers', 'avg_temp_c': '-10-28'},
            'polar': {'season': 'Cold year-round', 'avg_temp_c': '-30-5'},
        }
        return Response({
            'destination': destination.name,
            'climate': destination.climate,
            'best_time_to_visit': destination.best_time_to_visit,
            **weather_by_climate.get(destination.climate, {}),
        })
