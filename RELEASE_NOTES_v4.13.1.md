# v4.13.1 — Smoke Test Route Expectations

- Accepts HTTP 400 from `/api/v1/jobs/next` when called without required display parameters.
- Accepts HTTP 502 from `/api/v1/content/manifest` when the content backend is unavailable in generic test context.
- Keeps strict failure handling for all other unexpected statuses and exceptions.
- Adds regression tests for both route expectations.
