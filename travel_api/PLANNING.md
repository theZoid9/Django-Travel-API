# Implementation plan and design decisions

## User journeys

Visitors browse destinations and reviews. Registered users plan trips, manage their bookings and budgets, invite collaborators and leave reviews. Editors update shared trips; viewers inspect them. Staff maintain the shared travel catalogue.

## Data and access boundaries

accounts owns identity/profile; destinations owns catalogue taxonomy and photos; itineraries owns trips, daily plans and collaboration; bookings owns accommodation/activity offerings and reservations; budgets owns budgets/expenses; reviews owns destination/activity reviews. See erd.svg for relationships.

Ownership is checked both when retrieving records and when accepting writable parent IDs. Booking, budget, expense and daily-plan writes are restricted to trip owners. Trip edit/publish operations also permit collaborator roles, but never viewers. Reviews use object-level authorship checks. Catalogue writes require staff because catalogue records have no individual owner field.

## Feedback implementation

1. Configuration: environment example, root ignore rules, explicit production secret, documented SMTP settings.
2. Serialization: ownership validation for parent IDs; custom updates recalculate both booking types; partial booking/trip date validation uses existing values.
3. Views: protected booking RetrieveUpdateDestroyAPIView classes; bulk endpoint GET discovers supported options and POST validates statuses before saving.
4. Permissions: author-only review writes, staff catalogue/photo writes, role-protected trip publication.
5. Routes: nested destination reviews and budget expenses; app URL namespaces retained; README matches registered paths.
6. Authentication: generic-response reset request, emailed UID/token, validated password confirmation, expiring single-use token and throttling.
7. Filtering: custom destination q filter and bounded finite advanced-search rating.
8. Performance: separate correlated booking-sum subqueries prevent join multiplication; budget sums are annotated once. Query-count tests compare small and larger lists.
9. Testing: regression tests exercise cross-user relationship assignments, author/staff/owner/viewer/editor boundaries, booking/expense/budget/review/daily-plan CRUD, reset replay, nested parent enforcement, filtering and totals. Existing broad model exception assertions now expect ValidationError.
10. Delivery: initial budgets/reviews migrations support clean database setup; README and validation record accompany the implementation.

## Validation and deployment sequence

Run system checks, migration drift detection and the complete test suite with coverage. Back up existing databases before migration. For fresh installations run migrate; existing unmigrated budget/review tables need schema verification before fake-initial. Configure a random production key, allowed hosts, SMTP and a shared throttle cache. No deployment is performed by this change.

## Tradeoffs

Bulk updates report individual invalid/unauthorised entries without saving them; valid entries can succeed. Budget and booking management intentionally stays owner-only. Password-reset email contains API submission instructions because this repository has no frontend. Existing JWTs retain their configured expiry after password reset; token/session revocation is a separate feature. Search preferences retain the existing profile-bio storage behaviour.
