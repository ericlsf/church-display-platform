# v3.3.0 — Resilience, maintenance, and unified jobs

## Added

- Configurable automatic player recovery with thresholds and cooldowns.
- Optional reboot escalation after repeated failed restart attempts.
- Automatic failed-sync repair.
- Maintenance mode that pauses disruptive jobs while monitoring remains active.
- Bi-weekly platform backups using a persistent 14-day systemd timer.
- Configurable backup retention and optional cached-media inclusion.
- Job attempts, timeouts, automatic retry, manual retry, and cancellation controls.
- Resilience state reported in display heartbeats.

## Safety defaults

- Automatic recovery is enabled.
- Automatic reboot escalation is disabled until explicitly enabled.
- Maintenance mode suppresses sync, deployment, restart, and reboot work.
- Backups run every 14 days and retain six archives by default.
