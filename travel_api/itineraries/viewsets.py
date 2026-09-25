"""
itineraries/viewsets.py

ItineraryViewSet: full CRUD ModelViewSet with custom actions (duplicate,
export_pdf, share, upcoming). TripAnalyticsViewSet: a custom viewsets.ViewSet
(not model-backed) exposing aggregate statistics.
"""
from datetime import date

from django.db.models import Avg, Count, F, Q, Sum
from django.http import HttpResponse
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from bookings.models import Booking
from .filters import ItineraryFilter
from .models import Collaboration, Itinerary
from .permissions import CanEditItinerary
from .serializers import ItineraryDetailSerializer, ItineraryListSerializer


class ItineraryViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for itineraries plus custom actions
    (duplicate, PDF export, sharing, upcoming trips).
    """
    permission_classes = [IsAuthenticated, CanEditItinerary]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ItineraryFilter
    search_fields = ['title', 'description', 'destination__name']
    ordering_fields = ['created_at', 'start_date', 'budget']

    def get_queryset(self):
        """
        Query optimization: select_related for FKs, prefetch_related for
        reverse FKs/M2M, and an annotation for total activity count.
        """
        user = self.request.user
        return (
            Itinerary.objects.filter(Q(owner=user) | Q(collaborators=user))
            .select_related('destination', 'owner')
            .prefetch_related('daily_plans__activities', 'bookings__accommodation', 'collaborators')
            .annotate(total_activities=Count('daily_plans__activities', distinct=True))
            .distinct()
            .order_by('-start_date')
        )

    def get_serializer_class(self):
        """Different serializer for list vs retrieve/write."""
        if self.action == 'list':
            return ItineraryListSerializer
        return ItineraryDetailSerializer

    def get_permissions(self):
        """Looser permissions for read-only list/retrieve, stricter for writes."""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), CanEditItinerary()]

    def perform_create(self, serializer):
        """Always attach the current user as owner on create."""
        serializer.save(owner=self.request.user)

    @extend_schema(description='Duplicate an existing itinerary (and its daily plans) as a new draft trip.')
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Custom action: clone an itinerary, its daily plans, and collaborators."""
        original = self.get_object()
        clone = Itinerary.objects.create(
            title=f"{original.title} (Copy)",
            description=original.description,
            destination=original.destination,
            owner=request.user,
            start_date=original.start_date,
            end_date=original.end_date,
            budget=original.budget,
            status=Itinerary.StatusChoices.PLANNING,
        )
        for plan in original.daily_plans.all():
            new_plan = clone.daily_plans.create(
                day_number=plan.day_number, date=plan.date, title=plan.title, notes=plan.notes,
            )
            new_plan.activities.set(plan.activities.all())
        serializer = ItineraryDetailSerializer(clone, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(description='Export a lightweight text-based itinerary summary as a downloadable file.')
    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """
        Custom action: export the itinerary as a downloadable plain-text
        summary (a real PDF library could replace the content generation
        here without changing the endpoint contract).
        """
        itinerary = self.get_object()
        lines = [
            f"Itinerary: {itinerary.title}",
            f"Destination: {itinerary.destination.name}, {itinerary.destination.country}",
            f"Dates: {itinerary.start_date} - {itinerary.end_date} ({itinerary.duration_days} days)",
            f"Budget: {itinerary.budget} (remaining: {itinerary.budget_remaining})",
            "", "Day-by-day plan:",
        ]
        for plan in itinerary.daily_plans.all().order_by('day_number'):
            lines.append(f"  Day {plan.day_number} ({plan.date}): {plan.title}")
        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="itinerary_{itinerary.id}.txt"'
        return response

    @extend_schema(description='Share this itinerary with another user, assigning them a collaboration role.')
    @action(detail=True, methods=['post'], url_path='share')
    def share_with_user(self, request, pk=None):
        """Custom action: add a collaborator with a specified role."""
        itinerary = self.get_object()
        if itinerary.owner != request.user:
            return Response({'error': 'Only the owner can share this itinerary.'}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        role = request.data.get('role', 'viewer')
        if not user_id:
            return Response({'user_id': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            collaboration = itinerary.add_collaborator(target_user, role=role)
        except Exception as exc:  # noqa: BLE001
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'id': collaboration.id, 'user': target_user.username, 'role': collaboration.role},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(description="List the current user's upcoming (future) trips, ordered by start date.")
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming_trips(self, request):
        """Custom action: trips starting today or later, soonest first."""
        queryset = self.get_queryset().filter(start_date__gte=date.today()).order_by('start_date')
        page = self.paginate_queryset(queryset)
        serializer = ItineraryListSerializer(page or queryset, many=True, context={'request': request})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class TripAnalyticsViewSet(viewsets.ViewSet):
    """
    Trip analytics and statistics (custom ViewSet, not model-backed).
    Every action here aggregates data across the current user's trips.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Overall user trip statistics: totals, averages, status breakdown."""
        trips = Itinerary.objects.filter(owner=request.user)
        stats = trips.aggregate(
            total_trips=Count('id'),
            total_budget=Sum('budget'),
            total_spent=Sum('actual_spent'),
            avg_budget=Avg('budget'),
        )
        by_status = trips.values('status').annotate(count=Count('id')).order_by('status')
        return Response({**stats, 'by_status': list(by_status)})

    @extend_schema(description='Spending by budget category across all of the current user’s trips.')
    @action(detail=False, methods=['get'])
    def budget_summary(self, request):
        """Custom action: compare planned budget vs. actual spend per trip."""
        trips = Itinerary.objects.filter(owner=request.user).annotate(
            variance=F('budget') - F('actual_spent')
        ).values('id', 'title', 'budget', 'actual_spent', 'variance')
        over_budget = [t for t in trips if t['variance'] < 0]
        return Response({'trips': list(trips), 'over_budget_count': len(over_budget)})

    @extend_schema(description="Analyze the current user's destination preferences by category/climate.")
    @action(detail=False, methods=['get'])
    def destination_preferences(self, request):
        """Custom action: group the user's trips by destination category/climate."""
        trips = Itinerary.objects.filter(owner=request.user).select_related('destination')
        by_category = trips.values('destination__category').annotate(count=Count('id')).order_by('-count')
        by_climate = trips.values('destination__climate').annotate(count=Count('id')).order_by('-count')
        return Response({'by_category': list(by_category), 'by_climate': list(by_climate)})
