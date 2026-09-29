from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Prefetch
from django.utils import timezone
from .models import Itinerary, TripCollaborator, DailyPlan, DayActivity, ActivityLog
from .serializers import ItineraryListSerializer, ItineraryDetailSerializer, ItineraryCreateUpdateSerializer, DailyPlanSerializer, DayActivitySerializer, ActivityLogSerializer, AddCollaboratorSerializer, TripCollaboratorSerializer
from .permissions import IsTripOwner, IsTripOwnerOrCollaborator, IsTripParticipant
from .filters import ItineraryFilter
from bookings.serializers import AccommodationBookingSerializer, ActivityBookingSerializer

class ItineraryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_class = ItineraryFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'status', 'budget_estimate']
    ordering = ['-created_at']

    def get_queryset(self):
        u = self.request.user
        return Itinerary.objects.filter(Q(owner=u) | Q(companions=u)).select_related('owner').prefetch_related('companions', Prefetch('daily_plans', queryset=DailyPlan.objects.prefetch_related('day_activities__activity')), Prefetch('collaborators', queryset=TripCollaborator.objects.select_related('user')), 'accommodation_bookings__accommodation', 'activity_bookings__activity').annotate(total_bookings=Count('accommodation_bookings') + Count('activity_bookings')).only('id', 'title', 'description', 'owner__username', 'start_date', 'end_date', 'status', 'budget_estimate', 'cover_image', 'created_at', 'updated_at').distinct()

    def get_serializer_class(self):
        if self.action == 'list': return ItineraryListSerializer
        if self.action == 'retrieve': return ItineraryDetailSerializer
        if self.action in ('create', 'update', 'partial_update'): return ItineraryCreateUpdateSerializer
        return ItineraryDetailSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'): return [IsAuthenticated(), IsTripOwnerOrCollaborator()]
        if self.action == 'retrieve': return [IsAuthenticated(), IsTripParticipant()]
        return [IsAuthenticated()]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.action == 'retrieve': ctx['include_logs'] = True
        return ctx

    @action(detail=True, methods=['post'], url_path='add-collaborator')
    def add_collaborator(self, request, pk=None):
        itin = self.get_object()
        if itin.owner != request.user:
            return Response({'detail': 'Only owner can add collaborators.'}, status=status.HTTP_403_FORBIDDEN)
        s = AddCollaboratorSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        c, created = TripCollaborator.objects.get_or_create(itinerary=itin, user_id=s.validated_data['user_id'], defaults={'role': s.validated_data['role']})
        if not created:
            return Response({'detail': 'Already a collaborator.'}, status=status.HTTP_400_BAD_REQUEST)
        ActivityLog.objects.create(itinerary=itin, user=request.user, action='collaborator_added', details={'user_id': s.validated_data['user_id'], 'role': s.validated_data['role']})
        return Response(TripCollaboratorSerializer(c).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        itin = self.get_object()
        if itin.status != 'planning':
            return Response({'detail': 'Can only publish planning trips.'}, status=status.HTTP_400_BAD_REQUEST)
        itin.status = 'booked'
        itin.save(update_fields=['status', 'updated_at'])
        ActivityLog.objects.create(itinerary=itin, user=request.user, action='status_changed', details={'from': 'planning', 'to': 'booked'})
        return Response(ItineraryDetailSerializer(itin).data)

    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate(self, request, pk=None):
        itin = self.get_object()
        new = Itinerary.objects.create(title=f'{itin.title} (Copy)', description=itin.description, owner=request.user, start_date=itin.start_date, end_date=itin.end_date, budget_estimate=itin.budget_estimate)
        TripCollaborator.objects.create(itinerary=new, user=request.user, role='owner', accepted_at=timezone.now())
        for p in itin.daily_plans.all():
            DailyPlan.objects.create(itinerary=new, day_number=p.day_number, date=p.date, title=p.title, notes=p.notes)
        ActivityLog.objects.create(itinerary=new, user=request.user, action='itinerary_duplicated', details={'source_id': itin.id})
        return Response(ItineraryDetailSerializer(new).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, pk=None):
        itin = self.get_object()
        return Response({'id': itin.id, 'title': itin.title, 'status': itin.get_status_display(), 'total_days': itin.calculate_total_days(), 'total_cost': float(itin.calculate_total_cost()), 'budget_estimate': float(itin.budget_estimate), 'budget_variance': float(itin.budget_estimate - itin.calculate_total_cost()), 'confirmed_accommodations': itin.accommodation_bookings.filter(status='confirmed').count(), 'confirmed_activities': itin.activity_bookings.filter(status='confirmed').count(), 'collaborator_count': itin.collaborators.count()})

class DailyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = DailyPlanSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return DailyPlan.objects.filter(itinerary__owner=self.request.user).prefetch_related('day_activities__activity').order_by('day_number')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def trip_search(request):
    if request.method == 'GET':
        q = request.query_params.get('q', '')
        st = request.query_params.get('status', '')
        qf = Q(owner=request.user) | Q(companions=request.user)
        if q: qf &= (Q(title__icontains=q) | Q(description__icontains=q))
        if st: qf &= Q(status=st)
        itins = Itinerary.objects.filter(qf).select_related('owner').prefetch_related('daily_plans', 'collaborators').order_by('-created_at')
        from rest_framework.pagination import PageNumberPagination
        pag = PageNumberPagination()
        page = pag.paginate_queryset(itins, request)
        s = ItineraryListSerializer(page or itins, many=True)
        if page is not None: return pag.get_paginated_response(s.data)
        return Response(s.data)
    else:
        profile = request.user.profile
        profile.bio = f"Search prefs: {request.data.get('query', '')}"
        profile.save(update_fields=['bio'])
        return Response({'detail': 'Preferences saved.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_trip_report(request, trip_id):
    try:
        itin = Itinerary.objects.select_related('owner').prefetch_related('daily_plans__day_activities__activity', 'accommodation_bookings__accommodation', 'activity_bookings__activity', 'collaborators__user').get(pk=trip_id)
    except Itinerary.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    if not (itin.owner == request.user or itin.is_collaborator(request.user)):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        from budgets.models import Budget
        budget = Budget.objects.get(itinerary=itin)
        total_spent = budget.expenses.aggregate(total=Sum('amount'))['total'] or 0
    except Budget.DoesNotExist:
        total_spent = 0
    return Response({'trip': {'id': itin.id, 'title': itin.title, 'status': itin.get_status_display(), 'total_days': itin.calculate_total_days()}, 'budget': {'estimated': float(itin.budget_estimate), 'total_bookings': float(itin.calculate_total_cost()), 'total_expenses': float(total_spent)}, 'collaborators': TripCollaboratorSerializer(itin.collaborators.all(), many=True).data, 'daily_plans': DailyPlanSerializer(itin.daily_plans.all(), many=True).data})
