"""
bookings/viewsets.py

BookingViewSet: full CRUD with role-aware permissions and confirm/cancel
custom actions. AccommodationViewSet / ActivityViewSet: catalog CRUD,
publicly readable, admin-writable.
"""
import uuid

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .filters import AccommodationFilter, BookingFilter
from .models import Accommodation, Activity, Booking
from .permissions import IsBookingOwner
from .serializers import (
    AccommodationSerializer,
    ActivitySerializer,
    BookingDetailSerializer,
    BookingListSerializer,
    BookingSerializer,
)


class BookingViewSet(viewsets.ModelViewSet):
    """Manage accommodation and activity bookings for the current user."""

    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookingFilter
    search_fields = ['confirmation_code', 'notes']
    ordering_fields = ['created_at', 'price', 'booking_date']

    def get_queryset(self):
        """Query optimization: select_related for all FKs touched by the serializer."""
        return Booking.objects.filter(user=self.request.user).select_related(
            'accommodation', 'activity', 'itinerary'
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListSerializer
        return BookingDetailSerializer

    def get_permissions(self):
        """Different permission classes per action."""
        if self.action in ['create', 'list']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsBookingOwner()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(description='Confirm a pending booking, assigning it a confirmation code.')
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Custom action: move a pending booking to confirmed."""
        booking = self.get_object()
        if booking.status != Booking.StatusChoices.PENDING:
            return Response({'error': 'Only pending bookings can be confirmed.'}, status=status.HTTP_400_BAD_REQUEST)
        booking.status = Booking.StatusChoices.CONFIRMED
        if not booking.confirmation_code:
            booking.generate_confirmation_code()
        booking.save()
        return Response(BookingDetailSerializer(booking, context={'request': request}).data)

    @extend_schema(description='Cancel a booking and report the calculated refund amount.')
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Custom action: cancel a booking and report the refund amount."""
        booking = self.get_object()
        if booking.status == Booking.StatusChoices.CANCELLED:
            return Response({'error': 'Booking is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        refund = booking.calculate_refund()
        booking.status = Booking.StatusChoices.CANCELLED
        booking.save()
        return Response({'status': booking.status, 'refund_amount': refund})


class AccommodationViewSet(viewsets.ModelViewSet):
    """Browse and manage accommodations."""

    queryset = Accommodation.objects.select_related('destination').all()
    serializer_class = AccommodationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AccommodationFilter
    search_fields = ['name', 'address', 'destination__name']
    ordering_fields = ['price_per_night', 'created_at']


class ActivityViewSet(viewsets.ModelViewSet):
    """Browse and manage activities."""

    queryset = Activity.objects.select_related('destination').all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['destination', 'category', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'duration_hours']
