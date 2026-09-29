from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Review, ActivityReview
from .serializers import ReviewSerializer, ActivityReviewSerializer
from .filters import ReviewFilter, ActivityReviewFilter

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    filterset_class = ReviewFilter
    search_fields = ['title', 'comment']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']
    def get_queryset(self):
        return Review.objects.select_related('user', 'destination').all()
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'): return [IsAuthenticated()]
        return [AllowAny()]
    def perform_create(self, serializer):
        review = serializer.save()
        review.destination.update_average_rating()

class ActivityReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ActivityReviewSerializer
    filterset_class = ActivityReviewFilter
    search_fields = ['title', 'comment']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']
    def get_queryset(self):
        return ActivityReview.objects.select_related('user', 'activity').all()
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'): return [IsAuthenticated()]
        return [AllowAny()]
