"""
bookings/views.py

FBV: bulk_update_bookings (atomic multi-record update).
CBV: BookingDetailView (RetrieveUpdateDestroyAPIView).
"""
from django.db import transaction
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import Booking
from .permissions import IsBookingOwner
from .serializers import BookingDetailSerializer


@extend_schema(
    request={'application/json': {'type': 'object', 'example': {'updates': [{'id': 1, 'status': 'confirmed'}]}}},
    responses={200: dict},
    examples=[OpenApiExample('Bulk update example', value={'updates': [{'id': 1, 'status': 'confirmed'}, {'id': 2, 'status': 'cancelled'}]})],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_bookings(request):
    """
    Update multiple bookings belonging to the current user in a single
    atomic request. Body: {"updates": [{"id": 1, "status": "confirmed"}, ...]}
    """
    updates = request.data.get('updates', [])
    if not isinstance(updates, list) or not updates:
        return Response({'updates': 'Must be a non-empty list.'}, status=status.HTTP_400_BAD_REQUEST)

    valid_statuses = dict(Booking.StatusChoices.choices)
    succeeded, failed = [], []

    try:
        with transaction.atomic():
            for item in updates:
                booking_id = item.get('id')
                new_status = item.get('status')
                if new_status not in valid_statuses:
                    failed.append({'id': booking_id, 'error': 'Invalid status.'})
                    continue
                try:
                    booking = Booking.objects.get(pk=booking_id, user=request.user)
                except Booking.DoesNotExist:
                    failed.append({'id': booking_id, 'error': 'Not found.'})
                    continue
                booking.status = new_status
                booking.save(update_fields=['status', 'updated_at'])
                succeeded.append(booking_id)
    except Exception as exc:  # noqa: BLE001 - guard the bulk operation as a whole
        return Response({'error': f'Bulk update failed: {exc}'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success_count': len(succeeded),
        'failure_count': len(failed),
        'succeeded_ids': succeeded,
        'failures': failed,
    }, status=status.HTTP_200_OK)


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific booking owned by the current user."""

    serializer_class = BookingDetailSerializer
    permission_classes = [IsAuthenticated, IsBookingOwner]

    def get_queryset(self):
        """Query optimization: select_related the FKs the serializer needs."""
        return Booking.objects.filter(user=self.request.user).select_related(
            'accommodation', 'itinerary', 'activity'
        )
