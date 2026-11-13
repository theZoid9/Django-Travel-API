from django.urls import path
from django.shortcuts import get_object_or_404
from destinations.models import Destination
from .views import ReviewViewSet

app_name = 'reviews'

class DestinationReviewsView(ReviewViewSet):
    def get_queryset(self):
        get_object_or_404(Destination, pk=self.kwargs['destination_id'])
        return super().get_queryset().filter(destination_id=self.kwargs['destination_id'])

urlpatterns = [path('destinations/<int:destination_id>/reviews/', DestinationReviewsView.as_view({'get': 'list'}), name='destination_reviews')]
