# Travel Itinerary Planning & Booking API

A Django REST Framework backend for searching destinations, building
day-by-day trip itineraries, booking accommodations and activities,
tracking budgets, collaborating with travel companions, and leaving
reviews.

## Tech Stack

- **Django 6.1** + **Django REST Framework 3.18**
- **djangorestframework-simplejwt** — JWT authentication
- **django-filter** — advanced query filtering
- **drf-spectacular** — OpenAPI 3 schema, Swagger UI, and ReDoc
- **python-decouple** — environment-based configuration
- **Pillow** — image upload support
- SQLite by default (Postgres-ready via `.env`)

## Project Structure

```
travel_api/
├── travel_api/          # Project settings, root urls, exception handler
├── accounts/             # Custom User model, auth (register/login/reset), profile
├── destinations/         # Destination catalog, search, filters
├── itineraries/          # Itinerary, Collaboration, DailyPlan, trip analytics
├── bookings/              # Accommodation, Activity, Booking
├── reviews/               # Review (destinations/accommodations/activities)
├── budgets/                # Budget, Expense tracking per trip
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── pytest.ini
└── manage.py
```

## Setup

```bash
cd travel_api
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
# or, to also install testing tools:
pip install -r requirements-dev.txt

cp .env.example .env              # generate/replace SECRET_KEY for real use

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API is then available at `http://127.0.0.1:8000/api/v1/`.

- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc/`
- **Raw OpenAPI schema**: `http://127.0.0.1:8000/api/schema/`
- **Django admin**: `http://127.0.0.1:8000/admin/`

## Running Tests

```bash
python manage.py test               # Django's own test runner
# or
pytest                              # pytest-django, same test suite
coverage run manage.py test && coverage report -m   # with coverage
```

57 tests currently pass with ~85% coverage across models, serializers,
views, viewsets, and permissions.

## Authentication

JWT-based. Register or log in to receive an `access`/`refresh` token
pair, then send `Authorization: Bearer <access_token>` on subsequent
requests.

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/accounts/register/` | POST | Create an account, returns tokens |
| `/api/v1/accounts/login/` | POST | Log in, returns tokens |
| `/api/v1/auth/token/refresh/` | POST | Exchange a refresh token for a new access token |
| `/api/v1/accounts/profile/` | GET/PUT/PATCH | View/update your own profile |
| `/api/v1/accounts/password/change/` | POST | Change password (authenticated) |
| `/api/v1/accounts/password/reset/` | POST | Request a reset token |
| `/api/v1/accounts/password/reset/confirm/` | POST | Confirm reset with uid/token |

## Core Resources (ViewSets, under `/api/v1/`)

| Resource | Base path | Notes |
|---|---|---|
| Itineraries | `/itineraries/` | Full CRUD + `duplicate`, `export_pdf`, `share`, `upcoming` |
| Destinations | `/destinations/` | Read-only browse + `popular_activities`, `weather_info` |
| Accommodations | `/accommodations/` | Full CRUD, public read |
| Activities | `/activities/` | Full CRUD, public read |
| Bookings | `/bookings/` | Full CRUD + `confirm`, `cancel` |
| Reviews | `/reviews/` | Full CRUD + `helpful` |
| Trip Analytics | `/analytics/` | `list`, `budget_summary`, `destination_preferences` |

## Additional Function/Class-Based Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/destinations/search/` | GET/POST | Free-text destination search; POST saves the search |
| `/api/v1/itineraries/search/` | GET/POST | Search the current user's trips; POST saves the search |
| `/api/v1/itineraries/<id>/report/` | GET | Combined budget/booking/itinerary report |
| `/api/v1/itineraries/create/` | GET/POST | Simple list/create (alternative to the ViewSet) |
| `/api/v1/itineraries/<id>/collaborators/` | POST | Add a collaborator |
| `/api/v1/itineraries/<id>/collaborators/<user_id>/` | PATCH/DELETE | Update/remove a collaborator |
| `/api/v1/bookings/bulk-update/` | POST | Atomically update multiple bookings' status |
| `/api/v1/bookings/manage/<id>/` | GET/PUT/PATCH/DELETE | Alternative single-booking CBV |
| `/api/v1/budgets/<trip_id>/` | GET/PUT/PATCH | Per-category trip budget (auto-created) |
| `/api/v1/budgets/<trip_id>/expenses/` | GET/POST | List/create expenses for a trip |
| `/api/v1/budgets/expenses/<id>/` | GET/PUT/PATCH/DELETE | Manage a single expense |

## Data Model Highlights

- **User** (custom, `accounts.User`) — extends `AbstractUser` with travel profile fields.
- **Itinerary** — owned by a `User`, tied to one `Destination`; `collaborators`
  is a `ManyToManyField` through the `Collaboration` model (role: viewer/editor/admin).
- **DailyPlan** — day-by-day breakdown of an itinerary; `ManyToManyField` to `Activity`.
- **Accommodation** / **Activity** — bookable catalog items scoped to a `Destination`.
- **Booking** — links a `User` + `Itinerary` to exactly one `Accommodation` or `Activity`.
- **Review** — targets exactly one of `Destination` / `Accommodation` / `Activity`.
- **Budget** (1:1 with `Itinerary`) / **Expense** — per-category budgeting and spend tracking.

See `docs/ERD.md` for the full entity-relationship diagram and design notes.

## Environment Variables (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | *(generated)* | Django secret key — replace for any real deployment |
| `DEBUG` | `True` | Toggle debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `DB_ENGINE` | `sqlite` | `sqlite` or `postgresql` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | — | Used when `DB_ENGINE=postgresql` |
| `MAX_UPLOAD_SIZE_MB` | `5` | Max size for image/document uploads |

## Notes

- Query optimization (`select_related`, `prefetch_related`, `annotate`,
  `only`/`defer`) is applied throughout the ViewSets and CBVs that serve
  list/detail data, to avoid N+1 queries.
- Every write endpoint validates at both the serializer (field/object)
  and model (`clean()`) level.
- The custom DRF exception handler (`travel_api/exceptions.py`) wraps
  all error responses in a consistent `{error, status_code, detail}` shape.
