import os
from django.core.exceptions import ValidationError

def validate_file_size(value, max_mb=5):
    limit = max_mb * 1024 * 1024
    if value.size > limit:
        raise ValidationError(f'File size must be under {max_mb} MB.')

def validate_image_file(value):
    allowed = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed:
        raise ValidationError(f'Unsupported file type {ext}. Allowed: {", ".join(allowed)}')

def validate_pdf_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError('Only PDF files are allowed.')

def validate_rating(value):
    if not (1 <= value <= 5):
        raise ValidationError('Rating must be between 1 and 5.')

def validate_future_date(value):
    from django.utils import timezone
    if value < timezone.now().date():
        raise ValidationError('Date must be in the future.')
