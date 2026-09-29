from django.contrib import admin
from .models import Tag, Category, Destination, DestinationPhoto
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(Destination)
admin.site.register(DestinationPhoto)
