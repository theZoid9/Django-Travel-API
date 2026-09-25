"""itineraries/urls.py"""
from django.urls import path
from . import views

app_name = 'itineraries'

urlpatterns = [
    path('search/', views.trip_search, name='trip-search'),
    path('<int:trip_id>/report/', views.generate_trip_report, name='trip-report'),
    path('create/', views.ItineraryListCreateView.as_view(), name='itinerary-create'),
    path('<int:trip_id>/collaborators/', views.TripCollaborationView.as_view(), name='trip-collaborators-add'),
    path('<int:trip_id>/collaborators/<int:user_id>/', views.TripCollaborationView.as_view(), name='trip-collaborators-manage'),
]
