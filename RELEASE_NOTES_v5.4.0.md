# v5.4.0 — Safe One-Click Upgrades

## Added

- Current/latest version comparison on each display page.
- Version selector.
- Dry-run deployment mode.
- Direct deployment mode.
- Maintenance-mode protection with explicit override.
- Active deployment progress.
- Duplicate deployment reuse.
- Health-check, restart, and rollback intent in deployment payloads.
- One-click rollback job after a failed deployment.

## Important

The display agent must support `rollback_update` for automatic rollback
execution. Until then, the Hub will queue and audit the rollback request, but
the agent may report the job as unsupported.
