# v5.8.0 — Automatic Verification Rollback

## Added

When a deployment installer reports success but the display heartbeat does not
confirm the target version within three minutes, the Hub automatically queues a
`rollback_update` job.

## Safeguards

- Rollback only applies to `verification_failed` deployments.
- The same deployment cannot queue duplicate rollback jobs.
- The timeout is constrained between 60 seconds and 30 minutes.
- Existing successful or active deployments are not affected.
- The display page shows the rollback countdown and queued state.

## Default

The default verification timeout is 180 seconds.
