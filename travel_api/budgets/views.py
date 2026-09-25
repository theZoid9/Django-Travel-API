"""
budgets/views.py

Class-based views for the per-trip Budget (retrieve/update) and its
Expense line items (list/create, retrieve/update/delete).
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from itineraries.models import Itinerary
from .models import Budget, Expense
from .permissions import IsItineraryOwnerOrCollaborator
from .serializers import BudgetSerializer, ExpenseSerializer


class BudgetDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the budget breakdown for a specific itinerary."""

    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated, IsItineraryOwnerOrCollaborator]

    def get_object(self):
        itinerary = get_object_or_404(Itinerary, pk=self.kwargs['trip_id'])
        budget, _ = Budget.objects.get_or_create(itinerary=itinerary)
        self.check_object_permissions(self.request, budget)
        return budget


class ExpenseListCreateView(generics.ListCreateAPIView):
    """List or create expenses for a specific itinerary."""

    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Query optimization: only fetch expenses for the requested, permitted trip."""
        itinerary = get_object_or_404(Itinerary, pk=self.kwargs['trip_id'])
        if itinerary.owner != self.request.user and self.request.user not in itinerary.collaborators.all():
            return Expense.objects.none()
        return Expense.objects.filter(itinerary=itinerary).only('id', 'category', 'description', 'amount', 'date')

    def perform_create(self, serializer):
        itinerary = get_object_or_404(Itinerary, pk=self.kwargs['trip_id'])
        serializer.save(itinerary=itinerary)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a single expense entry."""

    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, IsItineraryOwnerOrCollaborator]

    def get_queryset(self):
        # defer() used to skip the rarely-needed notes field in list-like access patterns
        return Expense.objects.select_related('itinerary').defer('notes')
