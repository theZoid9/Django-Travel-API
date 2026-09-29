# Travel Itinerary Planning & Booking API

A comprehensive RESTful API for travel itinerary planning, booking, budget tracking, and collaboration.

## Quick Start

```bash
cd travel_api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API Docs

- Swagger: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## Key Endpoints

| Endpoint | Methods | Description |
|----------|---------|-------------|
| /api/v1/accounts/register/ | POST | Register |
| /api/v1/accounts/login/ | POST | JWT Login |
| /api/v1/destinations/ | GET | List destinations |
| /api/v1/itineraries/ | GET/POST | Trips CRUD |
| /api/v1/itinerary/search/ | GET/POST | Search trips (FBV) |
| /api/v1/itinerary/{id}/report/ | GET | Trip report (FBV) |
| /api/v1/booking/bulk-update/ | POST | Bulk update (FBV) |
| /api/v1/reviews/ | GET/POST | Reviews CRUD |
| /api/v1/budgets/ | GET/POST | Budgets CRUD |

## Testing

```bash
pytest --cov=. --cov-report=term-missing
```

## Environment Variables

Copy `.env.example` to `.env` and fill in values.
