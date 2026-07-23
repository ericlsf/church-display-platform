# v5.6.1 — Verification Dependency Repair

## Fixed

v5.6.0 referenced `services.live_display_telemetry` but did not bundle that
module. This caused the deployment-verification tests to fail during import.

This release restores the exact live-heartbeat service required by:

- deployment verification;
- version reconciliation;
- exact display media counts.

## Added

`find-deployment-handler.py` identifies the repository files that implement
`deploy_update`. It does not modify them automatically. The output provides the
file and line references needed for a safe integration of
`record_installed_release()`.
