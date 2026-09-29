from rest_framework import viewsets, status, generics, parsers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django.db.models import Q, Avg, Count
from .models import Category, Tag, Destination, DestinationPhoto
from .serializers import TagSerializer, CategorySerializer, DestinationListSerializer, DestinationDetailSerializer, DestinationCreateUpdateSerializer, DestinationPhotoSerializer
from .filters import DestinationFilter, CategoryFilter

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    search_fields = ['name']

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.prefetch_related('destinations').all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name']

class DestinationViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    filterset_class = DestinationFilter
    search_fields = ['name', 'country', 'city', 'description']
    ordering_fields = ['name', 'avg_rating', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Destination.objects.select_related('category').prefetch_related('tags', 'photos').annotate(review_count=Count('reviews', distinct=True), activity_count=Count('activities', distinct=True)).all()

    def get_serializer_class(self):
        if self.action == 'list': return DestinationListSerializer
        if self.action == 'retrieve': return DestinationDetailSerializer
        if self.action in ('create', 'update', 'partial_update'): return DestinationCreateUpdateSerializer
        return DestinationDetailSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'): return [IsAdminUser()]
        return [AllowAny()]

    @action(detail=True, methods=['get'], url_path='photos')
    def list_photos(self, request, pk=None):
        dest = self.get_object()
        return Response(DestinationPhotoSerializer(dest.photos.all(), many=True).data)

    @action(detail=True, methods=['post'], url_path='upload-photo', parser_classes=[parsers.MultiPartParser])
    def upload_photo(self, request, pk=None):
        dest = self.get_object()
        s = DestinationPhotoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(destination=dest)
        return Response(s.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='featured')
    def featured(self, request):
        qs = self.get_queryset().filter(is_featured=True)
        page = self.paginate_queryset(qs)
        s = DestinationListSerializer(page or qs, many=True)
        return self.get_paginated_response(s.data) if page else Response(s.data)

    @action(detail=False, methods=['get'], url_path='search-advanced')
    def search_advanced(self, request):
        query = request.query_params.get('q', '')
        country = request.query_params.get('country', '')
        min_rating = request.query_params.get('min_rating', 0)
        q_filter = Q()
        if query:
            q_filter |= Q(name__icontains=query) | Q(city__icontains=query) | Q(description__icontains=query)
        if country:
            q_filter &= Q(country__icontains=country)
        if min_rating:
            q_filter &= Q(avg_rating__gte=float(min_rating))
        qs = self.get_queryset().filter(q_filter)
        page = self.paginate_queryset(qs)
        s = DestinationListSerializer(page or qs, many=True)
        return self.get_paginated_response(s.data) if page else Response(s.data)

class DestinationPhotoUploadView(generics.CreateAPIView):
    serializer_class = DestinationPhotoSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [parsers.MultiPartParser]
    def perform_create(self, serializer):
        from .models import Destination
        dest = Destination.objects.get(pk=self.kwargs['destination_id'])
        serializer.save(destination=dest)
