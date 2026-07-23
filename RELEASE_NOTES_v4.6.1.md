# v4.6.1 — Deployment deduplication

## Fixed

- Duplicate Fleet rows are collapsed before bulk deployment.
- An active deployment for the same display, target, and mode is reused.
- Repeated form submission no longer creates another active deployment.
- Bulk confirmation counts unique displays.

## Cleanup

`scripts/resolve-duplicate-deployments.py` marks repeated successful deployment
records resolved while preserving one canonical successful job and the audit
history.
