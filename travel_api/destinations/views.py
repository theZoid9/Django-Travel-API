"""
destinations/views.py

Class-based view: DestinationSearchView, an APIView demonstrating custom
Q-object search, ranking and a POST action to save a search as a
preference (in combination with the accounts.SearchPreference model).
"""
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from accounts.models import SearchPreference
from .models import Destination
from .serializers import DestinationListSerializer


class DestinationSearchView(APIView):
    """
    Advanced destination search with custom ranking.

    GET: search destinations by free-text query across several fields,
    ranked with a simple relevance score.
    POST: persist the current search as a named preference for the user.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='q', description='Free text search across name/country/description', type=str),
            OpenApiParameter(name='max_cost', description='Maximum average daily cost', type=float),
        ],
        responses={200: DestinationListSerializer(many=True)},
    )
    def get(self, request):
        """Custom search implementation using Q objects and simple ranking."""
        query = request.query_params.get('q', '').strip()
        max_cost = request.query_params.get('max_cost')

        queryset = Destination.objects.filter(is_active=True)

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(country__icontains=query)
                | Q(description__icontains=query)
                | Q(category__icontains=query)
            )
        if max_cost:
            try:
                queryset = queryset.filter(avg_daily_cost__lte=float(max_cost))
            except ValueError:
                return Response({'max_cost': 'Must be a number.'}, status=status.HTTP_400_BAD_REQUEST)

        # Simple ranking: exact name matches first, then alphabetical.
        results = sorted(
            queryset,
            key=lambda d: (query.lower() not in d.name.lower() if query else False, d.name),
        )

        serializer = DestinationListSerializer(results, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """Save the user's current search parameters as a named preference."""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required to save searches.'}, status=status.HTTP_401_UNAUTHORIZED)

        name = request.data.get('name')
        filters = request.data.get('filters', {})
        if not name:
            return Response({'name': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        preference = SearchPreference.objects.create(user=request.user, name=name, filters=filters)
        return Response(
            {'id': preference.id, 'name': preference.name, 'filters': preference.filters},
            status=status.HTTP_201_CREATED,
        )
