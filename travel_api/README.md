# Travel Itinerary Planning & Booking API

A RESTful backend built with Django and Django REST Framework for a travel startup. Users can browse destinations, build day-by-day itineraries, book accommodations and activities, track budgets, collaborate with companions, and review places.

## Technologies

Django, Django REST Framework, Simple JWT, django-filter, drf-spectacular, python-decouple, Pillow, pytest, pytest-django, pytest-cov, PostgreSQL (SQLite for development).

## Installation

```bash
git clone <your-repo-url> && cd travel_api
python -m venv venv
source venv/bin/activate        # Windows: source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env            # then edit values
```

## Environment Variables

| Variable | Example | Notes |
|---|---|---|
| `SECRET_KEY` | `change-me` | Required |
| `DEBUG` | `False` | `True` for local dev only |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma separated |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Or PostgreSQL URL |

## Database Setup

SQLite works out of the box. For PostgreSQL, create a database and set its connection values in `.env`.

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver      # http://localhost:8000
```

## Running Tests

```bash
pytest                          # or: python manage.py test
pytest --cov=. --cov-report=term-missing
```

Tests run against a separate test database.

## Documentation

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`
- Postman collection: `postman/Travel_API.postman_collection.json` (import it, set `base_url`, run **Register**; tokens save automatically)
- ERD: `docs/erd.svg` (PNG copy at `docs/erd.png`)

![ERD](docs/erd.png)

## Authentication Flow

1. `POST /api/v1/accounts/register/` or `/login/` returns `access` (1 hour) and `refresh` (7 days) tokens.
2. Send `Authorization: Bearer <access>` on every request.
3. When the access token expires, `POST /api/v1/accounts/token/refresh/` with the refresh token.

Roles per itinerary: **owner** (full control), **editor/admin collaborator** (edit), **viewer** (read-only).

## API Endpoints (base `/api/v1/`)

| Area | Endpoints |
|---|---|
| Accounts | `POST accounts/register/`, `login/`, `token/refresh/`, `password/change/`, `password/reset/`, `password/reset/confirm/`; `GET/PATCH accounts/profile/` |
| Destinations | `GET destinations/`, `destinations/{id}/`, `.../popular_activities/`, `.../weather_info/`; `GET/POST destinations/search/` |
| Itineraries | CRUD `itineraries/`; `POST {id}/duplicate/`, `{id}/share/`; `GET {id}/export_pdf/`, `upcoming/` |
| Trips | `GET/POST trips/search/`; `GET trips/{id}/report/`; `POST/PATCH/DELETE trips/{id}/collaborators/[{user_id}/]` |
| Bookings | CRUD `bookings/`; `POST {id}/confirm/`, `{id}/cancel/`; `POST bookings/bulk-update/` |
| Reviews | CRUD `reviews/`; `GET destinations/{id}/reviews/` |
| Budgets | `GET/PATCH budgets/{itinerary_id}/`; `GET/POST itineraries/{id}/expenses/` |
| Analytics | `GET analytics/`, `analytics/budget_summary/`, `analytics/destination_preferences/` |

Lists support `?search=`, `?ordering=`, `?page=`, plus model-specific filters (e.g. `?status=planning&min_budget=1000`).

## Example Requests

```bash
# Register
curl -X POST http://localhost:8000/api/v1/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"traveler1","email":"t@example.com","password":"StrongPass123!","password2":"StrongPass123!"}'

# Create an itinerary
curl -X POST http://localhost:8000/api/v1/itineraries/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Paris Trip","destination":1,"start_date":"2026-11-01","end_date":"2026-11-07","budget":"2500.00"}'

# Search destinations
curl "http://localhost:8000/api/v1/destinations/?country=France&ordering=-avg_daily_cost" \
  -H "Authorization: Bearer $TOKEN"
```

## Project Structure

```
travel_api/          settings, root urls, wsgi/asgi
accounts/            custom User, JWT auth, profile, permissions
destinations/        Destination model, filters, browse + search views
itineraries/         Itinerary, DailyPlan, Collaboration, permissions
bookings/            Accommodation, Activity, Booking
reviews/             Review model and endpoints
budgets/             Budget, Expense
docs/                ERD diagram
postman/             Postman collection
media/ static/       Uploaded and collected files
```

Each app holds `models.py`, `serializers.py`, `views.py`, `urls.py`, and `tests.py`. Apps also include `permissions.py` or `filters.py` where needed.

## Notes

- Uploads (PDFs, images) are validated for size and type and stored under `media/`.
- Never commit `.env`, `db.sqlite3`, `media/`, or `__pycache__/`.
- Register app-specific URL includes before the router in the root `urls.py` so `destinations/search/` is not captured as a `{pk}`.
