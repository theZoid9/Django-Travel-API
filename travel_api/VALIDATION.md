# Validation record

Validated 13 November 2026 using the existing project virtual environment (Django 4.2.30) and SQLite test database.

- `python -m coverage run manage.py test --noinput`: 73 tests passed.
- `python -m coverage report`: 92.64% statement coverage (1,645 statements, 121 missed).
- Coverage includes all six apps and project code; test modules and migrations are excluded by .coveragerc. This is statement coverage, not branch coverage.
- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- `git diff --check`: no whitespace errors.

Regression tests cover ownership of submitted parent IDs, review authorship, staff-only catalogue writes, owner/editor/viewer trip actions, anonymous write denial, booking CRUD and price recalculation, partial date/capacity validation, expense/budget/review/daily-plan CRUD, nested routes, bulk status validation, password reset and replay rejection, custom filtering, and query counts as lists grow.

The test database was created from migrations and destroyed after the run. The user's existing database was not migrated or modified. Initial migrations for budgets and reviews are included; README describes the existing-table adoption path. Email delivery was tested with Django's in-memory backend; external SMTP was not exercised. Production deployment was not performed.

Test execution supplied a temporary SECRET_KEY through the process environment and did not modify the local .env file.
