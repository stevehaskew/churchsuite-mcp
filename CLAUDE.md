# ChurchSuite API reference

The full ChurchSuite Core API v2 OpenAPI spec is published at:

https://assets.churchsuite.com/openapi/latest/openapi.json

Fetch it directly (e.g. `curl -s https://assets.churchsuite.com/openapi/latest/openapi.json`)
to look up exact paths, parameters, schemas, and required scopes instead of
guessing or scraping developer.churchsuite.com (which 403s programmatically).

## Known gaps

- The Rotas module's API coverage is metadata-only: `/rotas/ministries`,
  `/rotas/ministry_teams`, `/rotas/ministry_members`, `/rotas/roles`. There is
  **no endpoint for individual rota slots/instances with assigned dates** —
  only a ministry's recurrence definition (`days`, `starts_at`/`ends_at`,
  `rotation_type`). "When am I next serving?" can only be answered
  approximately (membership + recurrence pattern), not with a confirmed date.
- `/rotas/ministry_members` has no filter-by-person query param; filtering by
  a specific person requires fetching members and matching `person.id` /
  `person.type` client-side.

## Required checks for every change

Whenever adding or modifying a tool that calls new ChurchSuite endpoints:

- Check the endpoint's `security` requirements in the OpenAPI spec against the
  scope configured in `TokenManager` (`src/churchsuite_mcp/auth.py`, default
  `bookings.read`). If an endpoint needs a scope not already granted, flag it
  to the user before merging — the OAuth app's scope grant must be updated
  out-of-band with ChurchSuite, code changes alone won't grant it.
- Add or update tests in `tests/test_tools.py` covering the new/changed
  behaviour.
- Update this file's "Known gaps" section if the change reveals new API
  limitations, or removes a previously documented one.
