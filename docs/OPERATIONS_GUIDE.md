# Operations guide

## Daily checks

1. Open the Dashboard and review **Needs Attention**.
2. Confirm expected displays are online and the display app is running.
3. Review failed or timed-out jobs.
4. Confirm the active playlist and current media are expected.
5. Review pending enrollment and draft-publication counts.

## Content change workflow

1. Synchronize Google Drive into the Hub cache.
2. Open Content and review the playlist.
3. Save ordering changes as a draft.
4. Preview the draft.
5. Publish the draft.
6. Deploy or schedule only the published revision.
7. Confirm the display reports `source: hub` after synchronization.

## Release workflow

1. Work from a feature branch based on `develop`.
2. Run `./scripts/validate-source.sh`.
3. Merge through a pull request.
4. Update `main` only with validated code.
5. Run `./scripts/validate-release.sh vX.Y.Z`.
6. Tag and push the release.
7. Dry-run deployment to one display.
8. Real-deploy to one test display.
9. Run the post-deploy check before wider rollout.

## Incident workflow

1. Copy the error reference ID shown in the UI.
2. Check `journalctl -u church-display-hub.service` for that request.
3. Use Operations or Remote Management to collect display logs.
4. Restart only the failed component first.
5. Use reboot escalation only after service recovery fails.
6. Record the incident and corrective action in the issue tracker.
