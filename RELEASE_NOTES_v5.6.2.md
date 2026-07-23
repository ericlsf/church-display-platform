# v5.6.2 — Authoritative Version Integration

## Display deployment handler

The active handler in `display/agent/jobs/update.py` now:

1. downloads and verifies the artifact;
2. extracts and validates the staged release;
3. backs up the current installation;
4. installs source and dependencies;
5. writes authoritative `VERSION` and `release.json`;
6. reads `VERSION` back and verifies it;
7. restarts and verifies the display service;
8. reports installer success;
9. restarts the display agent.

The version is recorded before either the success report or agent restart.

## Version comparison

The Hub now treats `v5.6.2` and `5.6.2` as the same release while still
rejecting genuinely different versions such as `4.3.0`.

## Deployment completion

Installer success remains separate from heartbeat verification. The display is
fully verified only after the restarted agent reports the installed target.
