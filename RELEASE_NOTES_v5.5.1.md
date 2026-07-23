# v5.5.1 — Live Telemetry as Source of Truth

## Fixed

- A display actively showing media no longer reports `No local media`.
- Current playback proves at least one playable local file exists.
- Media counts are read from multiple current and legacy heartbeat fields.
- Display version is taken from live heartbeat/agent telemetry before saved configuration.
- Completed/succeeded sync states are recognized in addition to `success`.
- Current playback can establish that the player is running.

Health Diagnostics, display cards, Command Center software status, and the
one-click upgrade panel all consume the corrected normalized fleet state.
