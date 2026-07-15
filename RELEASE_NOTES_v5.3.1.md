# v5.3.1 — Command Center as Default Dashboard

## Changed

- `/` now redirects to `/command-center`.
- The previous dashboard remains available at `/legacy-dashboard`.
- The Command Center navigation label is now `Dashboard`.
- Existing command-center functionality remains unchanged.

## Rollback

To return the original dashboard to `/`, restore:

- `hub/routes/dashboard.py`
- `hub/app.py`
- `hub/templates/base.html`

from the previous commit.
