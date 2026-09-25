"""reviews/viewsets.py - ModelViewSet for reviews with helpful/most-helpful custom actions."""
from django.db.models import Count
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .filters import ReviewFilter
from .models import Review
from .permissions import IsReviewOwner
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Full CRUD for reviews; anyone can read, only the author can write."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReviewFilter
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'rating', 'helpful_count']

    def get_queryset(self):
        """Query optimization: select_related the possible review targets and the author."""
        return Review.objects.select_related('user', 'destination', 'accommodation', 'activity').all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(description='Increment the helpful-vote counter on a review.')
    @action(detail=True, methods=['post'])
    def helpful(self, request, pk=None):
        """Custom action: mark a review as helpful."""
        review = self.get_object()
        review.mark_helpful()
        review.refresh_from_db()
        return Response({'helpful_count': review.helpful_count}, status=status.HTTP_200_OK)
