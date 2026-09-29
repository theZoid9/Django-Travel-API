from django.urls import path
from . import views
app_name = 'itineraries'
urlpatterns = [
    path('search/', views.trip_search, name='trip_search'),
    path('<int:trip_id>/report/', views.generate_trip_report, name='trip_report'),
]
