from django.db.models import OuterRef, Subquery, Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from bookings.models import AccommodationBooking, ActivityBooking

def with_booking_totals(queryset):
    field = DecimalField(max_digits=14, decimal_places=2)
    def total(model):
        values = model.objects.filter(itinerary_id=OuterRef('pk'), status='confirmed').order_by().values('itinerary_id').annotate(amount=Sum('total_price')).values('amount')
        return Coalesce(Subquery(values, output_field=field), Value(0), output_field=field)
    return queryset.annotate(booking_cost=total(AccommodationBooking) + total(ActivityBooking))
