# v5.7.0 — Rollback and Deployment Timeline

- Adds real `rollback_update` handling to the display agent.
- Restores the last-known-good source backup while preserving runtime data.
- Restarts and verifies the player after rollback.
- Restarts the agent after reporting success.
- Adds a seven-stage deployment timeline refreshed every 15 seconds.
