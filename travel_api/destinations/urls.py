from django.urls import path
from . import views
app_name = 'destinations'
urlpatterns = [
    path('<int:destination_id>/photos/add/', views.DestinationPhotoUploadView.as_view(), name='photo_upload'),
]
