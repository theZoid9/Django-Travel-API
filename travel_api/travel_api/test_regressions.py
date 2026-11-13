from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core import mail
from django.core.cache import cache
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase
from itineraries.models import Itinerary, TripCollaborator
from itineraries.querysets import with_booking_totals
from bookings.models import Accommodation, Activity, AccommodationBooking, ActivityBooking
from budgets.models import Budget, Expense
from destinations.models import Destination
from reviews.models import Review, ActivityReview

class FeedbackRegressionTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='Original!Secret123')
        self.other = User.objects.create_user(username='other', email='other@example.com')
        self.viewer = User.objects.create_user(username='viewer', email='viewer@example.com')
        self.editor = User.objects.create_user(username='editor', email='editor@example.com')
        self.trip = Itinerary.objects.create(owner=self.owner, title='Trip', start_date=date(2027,1,1), end_date=date(2027,1,10))
        self.foreign = Itinerary.objects.create(owner=self.other, title='Other', start_date=date(2027,1,1), end_date=date(2027,1,10))
        TripCollaborator.objects.create(itinerary=self.trip, user=self.viewer, role='viewer')
        TripCollaborator.objects.create(itinerary=self.trip, user=self.editor, role='collaborator')
        self.dest = Destination.objects.create(name='Cape Town', country='South Africa', city='Cape Town')
        self.hotel = Accommodation.objects.create(destination=self.dest, name='Hotel', accommodation_type='hotel', price_per_night=100)
        self.activity = Activity.objects.create(destination=self.dest, name='Walk', activity_type='nature', price=25, duration_minutes=60)
        self.budget = Budget.objects.create(itinerary=self.trip, total_amount=1000)
        self.foreign_budget = Budget.objects.create(itinerary=self.foreign, total_amount=1000)
        self.client.force_authenticate(self.owner)

    def booking_payload(self, kind, trip=None):
        payload = {'itinerary': (trip or self.trip).pk}
        if kind == 'accommodation': payload.update(accommodation=self.hotel.pk, check_in='2027-01-01', check_out='2027-01-03')
        else: payload.update(activity=self.activity.pk, date='2027-01-02', participants_count=2)
        return payload

    def test_booking_crud_and_ownership(self):
        for kind in ('accommodation', 'activity'):
            url = '/api/v1/booking/' + kind + '-bookings/'
            self.assertEqual(self.client.post(url, self.booking_payload(kind,self.foreign)).status_code,400)
            response = self.client.post(url,self.booking_payload(kind))
            self.assertEqual(response.status_code,201,response.data)
            detail = url + str(response.data['id']) + '/'
            self.assertEqual(self.client.get(detail).status_code,200)
            self.assertEqual(self.client.patch(detail,{'itinerary':self.foreign.pk}).status_code,400)
            patch = {'check_out':'2027-01-04'} if kind == 'accommodation' else {'participants_count':3}
            result = self.client.patch(detail,patch)
            self.assertEqual(result.status_code,200,result.data)
            self.assertEqual(Decimal(result.data['total_price']),300 if kind == 'accommodation' else 75)
            self.client.force_authenticate(self.other)
            for method in ('get','patch','delete'):
                self.assertEqual(getattr(self.client,method)(detail).status_code,404)
            self.client.force_authenticate(self.owner)
            self.assertEqual(self.client.delete(detail).status_code,204)

    def test_expenses_and_budgets_crud(self):
        data = {'budget': self.foreign_budget.pk,'category':'food','amount':'20','description':'Lunch','date':'2027-01-02'}
        self.assertEqual(self.client.post('/api/v1/expenses/',data).status_code,400)
        self.assertEqual(self.client.post('/api/v1/budgets/',{'itinerary':self.foreign.pk,'total_amount':100}).status_code,400)
        data['budget']=self.budget.pk
        response=self.client.post('/api/v1/expenses/',data)
        self.assertEqual(response.status_code,201,response.data)
        url='/api/v1/expenses/%s/' % response.data['id']
        self.assertEqual(self.client.patch(url,{'budget':self.foreign_budget.pk}).status_code,400)
        self.assertEqual(self.client.patch(url,{'amount':30}).status_code,200)
        self.assertEqual(self.client.get(url).status_code,200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(url).status_code,404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(url).status_code,204)
        url='/api/v1/budgets/%s/' % self.budget.pk
        self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.patch(url,{'total_amount':2000}).status_code,200)
        self.assertEqual(self.client.delete(url).status_code,204)

    def test_review_author_permissions(self):
        for model, field, value, route in [(Review,'destination',self.dest,'reviews'),(ActivityReview,'activity',self.activity,'activity-reviews')]:
            response=self.client.post('/api/v1/'+route+'/',{field:value.pk,'rating':4,'title':'Good'})
            self.assertEqual(response.status_code,201,response.data)
            url='/api/v1/%s/%s/' % (route,response.data['id'])
            self.client.force_authenticate(self.other)
            self.assertEqual(self.client.patch(url,{'rating':1}).status_code,403)
            self.assertEqual(self.client.delete(url).status_code,403)
            self.client.force_authenticate(self.owner)
            self.assertEqual(self.client.patch(url,{'rating':5}).status_code,200)
            self.assertEqual(self.client.delete(url).status_code,204)

    def test_catalog_writes_staff_only(self):
        for route, obj in [('accommodations',self.hotel),('activities',self.activity)]:
            url='/api/v1/%s/%s/' % (route,obj.pk)
            self.assertEqual(self.client.patch(url,{'name':'Changed'}).status_code,403)
            self.assertEqual(self.client.delete(url).status_code,403)
            self.owner.is_staff=True; self.owner.save()
            self.assertEqual(self.client.patch(url,{'name':'Changed'}).status_code,200)
            self.owner.is_staff=False; self.owner.save()

    def test_trip_roles(self):
        url='/api/v1/itineraries/%s/' % self.trip.pk
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get(url).status_code,200)
        for method, suffix, data in [('patch','',{'title':'Denied'}),('delete','',{}),('post','publish/',{})]:
            self.assertEqual(getattr(self.client,method)(url+suffix,data).status_code,403)
        self.client.force_authenticate(self.editor)
        self.assertEqual(self.client.patch(url,{'title':'Edited'}).status_code,200)
        self.assertEqual(self.client.post(url+'publish/').status_code,200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(url).status_code,404)

    def test_bulk_validation_and_metadata(self):
        booking=AccommodationBooking.objects.create(itinerary=self.trip, accommodation=self.hotel,check_in=date(2027,1,1),check_out=date(2027,1,3))
        url='/api/v1/booking/bulk-update/'
        self.assertIn('confirmed',self.client.get(url).data['statuses'])
        response=self.client.post(url,{'bookings':[{'type':'accommodation','id':booking.pk,'status':'invalid'}]},format='json')
        self.assertEqual(response.data['failure_count'],1)
        booking.refresh_from_db();self.assertEqual(booking.status,'pending')
        response=self.client.post(url,{'bookings':[{'type':'accommodation','id':booking.pk,'status':'confirmed'}]},format='json')
        self.assertEqual(response.data['success_count'],1)
        self.assertEqual(self.client.post(url,{'bookings':'bad'},format='json').status_code,400)

    def test_nested_resources(self):
        self.assertEqual(self.client.get('/api/v1/destinations/%s/reviews/' % self.dest.pk).status_code,200)
        url='/api/v1/budgets/%s/expenses/' % self.budget.pk
        response=self.client.post(url,{'budget':self.foreign_budget.pk,'category':'food','amount':10,'description':'Lunch','date':'2027-01-02'})
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(response.data['budget'],self.budget.pk)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(url).status_code,404)

    def test_rating_validation_and_custom_filter(self):
        for value in ['bad','nan','inf','-1','6']:
            self.assertEqual(self.client.get('/api/v1/destinations/search-advanced/',{'min_rating':value}).status_code,400)
        self.assertEqual(self.client.get('/api/v1/destinations/',{'q':'Cape'}).data['count'],1)
        self.assertEqual(self.client.get('/api/v1/destinations/',{'q':'NoMatch'}).data['count'],0)

    def test_booking_total_annotation_no_join_multiplication(self):
        for price in [100,100]:
            AccommodationBooking.objects.create(itinerary=self.trip, accommodation=self.hotel,check_in=date(2027,1,1),check_out=date(2027,1,3),total_price=price,status='confirmed')
        for price in [25,25]:
            ActivityBooking.objects.create(itinerary=self.trip, activity=self.activity,date=date(2027,1,2),total_price=price,status='confirmed')
        with self.assertNumQueries(1):
            totals=[item.calculate_total_cost() for item in with_booking_totals(Itinerary.objects.order_by('id'))]
        self.assertEqual(totals,[Decimal('250'),Decimal('0')])

    def test_list_query_counts_do_not_grow(self):
        for route in ['budgets','itineraries']:
            with CaptureQueriesContext(connection) as before:
                self.assertEqual(self.client.get('/api/v1/'+route+'/').status_code,200)
            for index in range(5):
                trip=Itinerary.objects.create(owner=self.owner,title='Extra',start_date=date(2027,1,1),end_date=date(2027,1,3))
                budget=Budget.objects.create(itinerary=trip,total_amount=100)
                Expense.objects.create(budget=budget,category='food',amount=10,description='Food',date=date(2027,1,1))
            with CaptureQueriesContext(connection) as after:
                self.assertEqual(self.client.get('/api/v1/'+route+'/').status_code,200)
            self.assertLessEqual(len(after),len(before)+1)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_flow_and_replay(self):
        cache.clear();self.client.force_authenticate(None)
        url='/api/v1/accounts/password/reset/'
        known=self.client.post(url,{'email':self.owner.email})
        unknown=self.client.post(url,{'email':'missing@example.com'})
        self.assertEqual(known.data,unknown.data)
        self.assertEqual(len(mail.outbox),1)
        uid=urlsafe_base64_encode(force_bytes(self.owner.pk))
        token=default_token_generator.make_token(self.owner)
        data={'uid':uid,'token':token,'new_password':'Fresh!Secret56789','new_password_confirm':'Fresh!Secret56789'}
        self.assertIn(token,mail.outbox[0].body)
        self.assertEqual(self.client.post(url+'confirm/',data).status_code,200)
        self.assertEqual(self.client.post(url+'confirm/',data).status_code,400)
        self.owner.refresh_from_db();self.assertTrue(self.owner.check_password(data['new_password']))

    def test_daily_plan_ownership_and_crud(self):
        data={'itinerary':self.foreign.pk,'day_number':1,'date':'2027-01-01','title':'Day one'}
        self.assertEqual(self.client.post('/api/v1/daily-plans/',data).status_code,400)
        data['itinerary']=self.trip.pk
        response=self.client.post('/api/v1/daily-plans/',data)
        self.assertEqual(response.status_code,201,response.data)
        url='/api/v1/daily-plans/%s/' % response.data['id']
        self.assertEqual(self.client.patch(url,{'title':'Updated'}).status_code,200)
        self.assertEqual(self.client.delete(url).status_code,204)

    def test_trip_actions_and_report(self):
        url='/api/v1/itineraries/%s/' % self.trip.pk
        extra=get_user_model().objects.create_user(username='invite',email='invite@example.com')
        response=self.client.post(url+'add-collaborator/',{'user_id':extra.pk,'role':'viewer'})
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(self.client.post(url+'add-collaborator/',{'user_id':extra.pk,'role':'viewer'}).status_code,400)
        self.assertEqual(self.client.post(url+'duplicate/').status_code,201)
        self.assertEqual(self.client.get(url+'summary/').status_code,200)
        # Multiple budgets are allowed by the data model and must not crash reports.
        Budget.objects.create(itinerary=self.trip,total_amount=200)
        self.assertEqual(self.client.get('/api/v1/itinerary/%s/report/' % self.trip.pk).status_code,200)
        self.assertEqual(self.client.post('/api/v1/itinerary/search/',{'query':'beach'}).status_code,200)
        self.assertEqual(self.client.delete(url).status_code,204)

    def test_password_reset_rejects_invalid_and_weak_passwords(self):
        cache.clear(); self.client.force_authenticate(None)
        url='/api/v1/accounts/password/reset/confirm/'
        data={'uid':'invalid','token':'bad','new_password':'a','new_password_confirm':'a'}
        self.assertEqual(self.client.post(url,data).status_code,400)
        data.update(uid=urlsafe_base64_encode(force_bytes(self.owner.pk)),token=default_token_generator.make_token(self.owner))
        self.assertEqual(self.client.post(url,data).status_code,400)
        data['new_password_confirm']='different'
        self.assertEqual(self.client.post(url,data).status_code,400)

    def test_anonymous_sensitive_writes(self):
        self.client.force_authenticate(None)
        for url in ['/api/v1/itineraries/','/api/v1/expenses/','/api/v1/budgets/','/api/v1/booking/activity-bookings/','/api/v1/reviews/']:
            self.assertEqual(self.client.post(url,{}).status_code,401)
        self.assertEqual(self.client.post('/api/v1/destinations/%s/upload-photo/' % self.dest.pk).status_code,401)

    def test_partial_booking_validation(self):
        response=self.client.post('/api/v1/booking/accommodation-bookings/',self.booking_payload('accommodation'))
        self.assertEqual(self.client.patch('/api/v1/booking/accommodation-bookings/%s/' % response.data['id'],{'check_out':'2026-01-01'}).status_code,400)
        response=self.client.post('/api/v1/booking/activity-bookings/',self.booking_payload('activity'))
        self.assertEqual(self.client.patch('/api/v1/booking/activity-bookings/%s/' % response.data['id'],{'participants_count':999}).status_code,400)

    def test_budget_summary_and_advanced_search(self):
        Expense.objects.create(budget=self.budget,category='food',amount=25,description='Lunch',date=date(2027,1,1))
        response=self.client.get('/api/v1/budgets/%s/summary/' % self.budget.pk)
        self.assertEqual(response.data['total_spent'],25)
        self.assertEqual(self.client.get('/api/v1/destinations/search-advanced/',{'q':'Cape','country':'South Africa','min_rating':0}).data['count'],1)
        self.assertEqual(self.client.get('/api/v1/destinations/%s/photos/' % self.dest.pk).status_code,200)
