# v4.8.0 — Audit History

## Added

- Automatic audit logging for successful and failed mutating requests.
- Actor, category, action, target, request ID, and source address.
- Redaction of passwords, secrets, tokens, API keys, and authorization data.
- Search and filters by actor, category, status, and free text.
- Expandable detail rows.
- CSV export using the active filters.

## Captured operations

This includes folder and overlay changes, deployments, scheduled rollouts,
display restarts, provisioning, user changes, job resolution, and other
POST/PUT/PATCH/DELETE actions routed through the Hub.
