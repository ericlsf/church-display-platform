# v3.4.0 — Product quality and operational polish

## Added

- Request IDs on every Hub response.
- Friendly 403, 404, and 500 error pages with support reference IDs.
- Security-oriented response headers.
- Integration tests for job lifecycle and heartbeat persistence.
- Source validation command that skips virtual environments.
- Template parsing as part of validation.
- Operations, troubleshooting, and upgrade guides.
- Keyboard skip link and clearer focus styling.

## Changed

- Responsive behavior is improved for narrow displays and tablets.
- Flash messages use a consistent global presentation.
- Tables, toolbars, dashboard actions, and navigation adapt more cleanly on mobile.

## Validation

Run:

```bash
./scripts/validate-source.sh
```
