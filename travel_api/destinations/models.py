from django.db import models
from django.utils.text import slugify
from travel_api.validators import validate_image_file, validate_file_size

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text='Tag name')
    slug = models.SlugField(max_length=50, unique=True, help_text='URL slug')
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text='Category name')
    slug = models.SlugField(max_length=100, unique=True, help_text='URL slug')
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, validators=[validate_image_file])
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Destination(models.Model):
    name = models.CharField(max_length=200, help_text='Destination name')
    slug = models.SlugField(max_length=200, unique=True, help_text='URL slug')
    country = models.CharField(max_length=100, help_text='Country')
    city = models.CharField(max_length=100, help_text='City')
    region = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text='Latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text='Longitude')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='destinations', help_text='Category')
    tags = models.ManyToManyField(Tag, blank=True, related_name='destinations', help_text='Tags')
    image = models.ImageField(upload_to='destinations/', blank=True, null=True, validators=[validate_image_file, validate_file_size])
    is_featured = models.BooleanField(default=False, help_text='Featured')
    avg_rating = models.FloatField(default=0.0, help_text='Cached average rating')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['country'], name='idx_dest_country'),
            models.Index(fields=['city'], name='idx_dest_city'),
            models.Index(fields=['is_featured'], name='idx_dest_featured'),
            models.Index(fields=['avg_rating'], name='idx_dest_rating'),
        ]

    def __str__(self):
        return f'{self.name}, {self.country}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.name}-{self.country}')
        super().save(*args, **kwargs)

    def update_average_rating(self):
        from reviews.models import Review
        result = Review.objects.filter(destination=self).aggregate(avg=models.Avg('rating'))
        self.avg_rating = round(result['avg'] or 0, 1)
        self.save(update_fields=['avg_rating', 'updated_at'])

    def get_top_activities(self, limit=5):
        return self.activities.order_by('-rating')[:limit]

class DestinationPhoto(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='photos', help_text='Destination')
    image = models.ImageField(upload_to='destinations/photos/', validators=[validate_image_file, validate_file_size])
    caption = models.CharField(max_length=255, blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-uploaded_at']
    def __str__(self):
        return f'Photo of {self.destination.name}'
