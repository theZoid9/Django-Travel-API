from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
from .models import Accommodation, Activity, AccommodationBooking, ActivityBooking
from .serializers import AccommodationListSerializer, AccommodationDetailSerializer, ActivityListSerializer, ActivityDetailSerializer, AccommodationBookingSerializer, ActivityBookingSerializer
from .filters import AccommodationFilter, ActivityFilter, AccommodationBookingFilter, ActivityBookingFilter

class AccommodationViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    filterset_class = AccommodationFilter
    search_fields = ['name', 'address', 'destination__name']
    ordering_fields = ['price_per_night', 'rating', 'name']
    ordering = ['name']
    def get_queryset(self):
        return Accommodation.objects.select_related('destination').all()
    def get_serializer_class(self):
        if self.action == 'list': return AccommodationListSerializer
        return AccommodationDetailSerializer
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'): return [IsAuthenticated()]
        return [AllowAny()]

class ActivityViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    filterset_class = ActivityFilter
    search_fields = ['name', 'description', 'destination__name']
    ordering_fields = ['price', 'rating', 'duration_minutes', 'name']
    ordering = ['name']
    def get_queryset(self):
        return Activity.objects.select_related('destination').only('id', 'name', 'destination__name', 'activity_type', 'price', 'duration_minutes', 'rating', 'image', 'is_available', 'max_participants', 'description').all()
    def get_serializer_class(self):
        if self.action == 'list': return ActivityListSerializer
        return ActivityDetailSerializer
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'): return [IsAuthenticated()]
        return [AllowAny()]

class AccommodationBookingListCreateView(generics.ListCreateAPIView):
    serializer_class = AccommodationBookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = AccommodationBookingFilter
    def get_queryset(self):
        return AccommodationBooking.objects.select_related('itinerary', 'accommodation').filter(itinerary__owner=self.request.user).order_by('-created_at')

class ActivityBookingListCreateView(generics.ListCreateAPIView):
    serializer_class = ActivityBookingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ActivityBookingFilter
    def get_queryset(self):
        return ActivityBooking.objects.select_related('itinerary', 'activity').filter(itinerary__owner=self.request.user).order_by('-created_at')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_bookings(request):
    bookings_data = request.data.get('bookings', [])
    if not bookings_data:
        return Response({'detail': 'No bookings provided.'}, status=status.HTTP_400_BAD_REQUEST)
    success_count = 0
    failure_count = 0
    errors = []
    try:
        with transaction.atomic():
            for item in bookings_data:
                btype = item.get('type')
                bid = item.get('id')
                new_status = item.get('status')
                if not all([btype, bid, new_status]):
                    failure_count += 1
                    errors.append({'id': bid, 'error': 'Missing fields.'})
                    continue
                try:
                    if btype == 'accommodation':
                        b = AccommodationBooking.objects.get(pk=bid, itinerary__owner=request.user)
                    elif btype == 'activity':
                        b = ActivityBooking.objects.get(pk=bid, itinerary__owner=request.user)
                    else:
                        failure_count += 1
                        errors.append({'id': bid, 'error': 'Invalid type.'})
                        continue
                    b.status = new_status
                    b.save(update_fields=['status', 'updated_at'])
                    success_count += 1
                except (AccommodationBooking.DoesNotExist, ActivityBooking.DoesNotExist):
                    failure_count += 1
                    errors.append({'id': bid, 'error': 'Not found.'})
                except Exception as e:
                    failure_count += 1
                    errors.append({'id': bid, 'error': str(e)})
    except Exception as e:
        return Response({'detail': 'Bulk op failed.', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({'success_count': success_count, 'failure_count': failure_count, 'errors': errors})
