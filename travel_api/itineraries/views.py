"""
itineraries/views.py

Function-based views (trip_search, generate_trip_report) and class-based
views (ItineraryListCreateView, TripCollaborationView).
"""
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from accounts.models import SearchPreference
from .models import Collaboration, Itinerary
from .permissions import IsTripOwner
from .serializers import ItineraryDetailSerializer, ItineraryListSerializer

User = get_user_model()


@extend_schema(
    parameters=[
        OpenApiParameter(name='destination', description='Destination id to filter by', type=int),
        OpenApiParameter(name='status', description='Trip status to filter by', type=str),
    ],
    responses={200: ItineraryListSerializer(many=True)},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def trip_search(request):
    """
    GET: search the current user's trips with custom filters and a simple
    relevance ranking (destination/country match first).
    POST: save the current search parameters as a named user preference.
    """
    if request.method == 'GET':
        query = request.query_params.get('q', '').strip()
        destination_id = request.query_params.get('destination')
        trip_status = request.query_params.get('status')

        queryset = Itinerary.objects.filter(
            Q(owner=request.user) | Q(collaborators=request.user)
        ).select_related('destination', 'owner').distinct()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(destination__name__icontains=query)
                | Q(destination__country__icontains=query)
            )
        if destination_id:
            queryset = queryset.filter(destination_id=destination_id)
        if trip_status:
            queryset = queryset.filter(status=trip_status)

        # Ranking: exact title matches first, then most recently created.
        results = sorted(
            queryset,
            key=lambda t: (query.lower() not in t.title.lower() if query else False, -t.id),
        )

        serializer = ItineraryListSerializer(results, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        name = request.data.get('name')
        filters = request.data.get('filters', {})
        if not name:
            return Response({'name': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        preference = SearchPreference.objects.create(user=request.user, name=name, filters=filters)
        return Response(
            {'id': preference.id, 'name': preference.name, 'filters': preference.filters},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(responses={200: dict})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_trip_report(request, trip_id):
    """
    Generate a comprehensive trip report combining budget, bookings and
    itinerary data for a single trip owned by (or shared with) the user.
    """
    itinerary = get_object_or_404(
        Itinerary.objects.select_related('destination').prefetch_related(
            'daily_plans__activities', 'bookings', 'expenses'
        ),
        pk=trip_id,
    )
    if itinerary.owner != request.user and request.user not in itinerary.collaborators.all():
        return Response({'error': 'You do not have access to this itinerary.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        bookings_total = itinerary.bookings.aggregate(total=Sum('price'))['total'] or 0
        expenses_total = itinerary.expenses.aggregate(total=Sum('amount'))['total'] or 0
        expenses_by_category = list(
            itinerary.expenses.values('category').annotate(total=Sum('amount')).order_by('category')
        )
    except Exception as exc:  # noqa: BLE001 - defensive: report generation must not 500
        return Response({'error': f'Could not generate report: {exc}'}, status=status.HTTP_400_BAD_REQUEST)

    report = {
        'trip': {
            'title': itinerary.title,
            'destination': itinerary.destination.name,
            'start_date': itinerary.start_date,
            'end_date': itinerary.end_date,
            'duration_days': itinerary.duration_days,
            'status': itinerary.status,
        },
        'budget': {
            'planned': itinerary.budget,
            'actual_spent': itinerary.actual_spent,
            'remaining': itinerary.budget_remaining,
            'is_over_budget': itinerary.is_over_budget(),
            'expenses_total': expenses_total,
            'expenses_by_category': expenses_by_category,
        },
        'bookings': {
            'count': itinerary.bookings.count(),
            'total_price': bookings_total,
        },
        'daily_plans_count': itinerary.daily_plans.count(),
    }
    return Response(report, status=status.HTTP_200_OK)


class ItineraryListCreateView(generics.ListCreateAPIView):
    """List the current user's itineraries or create a new one (simple flow, no nested writes)."""
    serializer_class = ItineraryListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Query optimization: filter to the current user's own itineraries."""
        return Itinerary.objects.filter(
            owner=self.request.user
        ).select_related('destination').prefetch_related('daily_plans')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TripCollaborationView(APIView):
    """
    Manage trip collaborators - add, update role, or remove.
    Only the trip owner may perform these actions.
    """
    permission_classes = [IsAuthenticated, IsTripOwner]

    def _get_itinerary(self, trip_id, request):
        itinerary = get_object_or_404(Itinerary, pk=trip_id)
        self.check_object_permissions(request, itinerary)
        return itinerary

    def post(self, request, trip_id):
        """Add a collaborator with a specific role."""
        itinerary = self._get_itinerary(trip_id, request)
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'viewer')
        user = get_object_or_404(User, pk=user_id)
        collaboration, created = Collaboration.objects.get_or_create(
            itinerary=itinerary, user=user, defaults={'role': role}
        )
        if not created:
            return Response({'error': 'User is already a collaborator.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {'id': collaboration.id, 'user': user.username, 'role': collaboration.role},
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, trip_id, user_id):
        """Update a collaborator's role."""
        itinerary = self._get_itinerary(trip_id, request)
        collaboration = get_object_or_404(Collaboration, itinerary=itinerary, user_id=user_id)
        role = request.data.get('role')
        if role not in dict(Collaboration.RoleChoices.choices):
            return Response({'role': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)
        collaboration.role = role
        collaboration.save()
        return Response({'id': collaboration.id, 'role': collaboration.role})

    def delete(self, request, trip_id, user_id):
        """Remove a collaborator."""
        itinerary = self._get_itinerary(trip_id, request)
        collaboration = get_object_or_404(Collaboration, itinerary=itinerary, user_id=user_id)
        collaboration.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
