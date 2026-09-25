"""
accounts/validators.py

Reusable validators for uploaded files (images, PDFs) used by several
apps' models (accounts, destinations, bookings, budgets).
"""
from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf']


def _max_upload_bytes():
    return getattr(settings, 'MAX_UPLOAD_SIZE_MB', 5) * 1024 * 1024


def validate_image_file_size(file):
    """Reject uploaded images larger than MAX_UPLOAD_SIZE_MB."""
    if file.size > _max_upload_bytes():
        raise ValidationError(
            f'Image file too large. Max size is {settings.MAX_UPLOAD_SIZE_MB}MB.'
        )


def validate_image_extension(file):
    """Reject uploaded images that aren't a recognised image type."""
    ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f'Unsupported image type ".{ext}". Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
        )


def validate_document_file_size(file):
    """Reject uploaded documents (e.g. itinerary PDFs) larger than the limit."""
    if file.size > _max_upload_bytes():
        raise ValidationError(
            f'File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB}MB.'
        )


def validate_pdf_extension(file):
    """Reject uploaded documents that aren't PDFs."""
    ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError('Only PDF files are allowed for this field.')
