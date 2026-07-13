# Production go-live: 1–2 day plan

This checklist is intentionally short. Do not add features during the release window.

## Day 1 — Validate and stage

1. Commit all source changes and confirm `git status --short` is empty.
2. Run `./scripts/validate-source.sh`.
3. Run `./scripts/production-readiness.sh`.
4. Create a manual backup from **Administration → System**.
5. Confirm Google Drive → Hub cache sync succeeds.
6. Confirm one test display downloads content from the Hub (`source: hub`).
7. Exercise these actions on the test display:
   - start/restart display app;
   - sync now;
   - screenshot;
   - log collection;
   - dry-run deployment.
8. Verify login for Admin, Editor, and Viewer roles.
9. Freeze playlist and schedule changes until go-live is complete.

## Day 2 — Deploy and observe

1. Enable Maintenance Mode.
2. Tag and deploy the release to one display.
3. Verify heartbeat, preview, current media, and display-app state.
4. Deploy to remaining displays/site groups.
5. Disable Maintenance Mode.
6. Watch Home, Operations, Notifications, and Jobs for at least 30 minutes.
7. Mark known historical failures resolved; do not delete audit records.
8. Record the deployed tag and backup filename.

## Rollback triggers

Rollback immediately if any of these occur:

- Hub cannot start after one service restart;
- displays stop receiving heartbeats;
- published playlist manifests cannot be retrieved;
- more than one display fails the same deployment stage;
- authentication blocks display-agent API traffic.

## Production freeze

For the first 48 hours after go-live, accept only critical bug fixes. Defer UI refinements and new features to the next release.
