"""
Custom exception handler so every error response from the API follows the
same shape: {"error": True, "detail": ..., "status_code": ...}
"""
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    """
    Wrap DRF's default exception handler to return consistent, informative
    error payloads across the whole API (validation, auth, permission and
    not-found errors all pass through here).
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        response.data = {
            'error': True,
            'status_code': response.status_code,
            'detail': response.data,
        }
    return response
