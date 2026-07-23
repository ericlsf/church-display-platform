# Church Display Platform v13.1.1

## Telemetry compatibility fix

This maintenance release restores fleet telemetry from current display players.

### Fixed

- Displays now read media totals from `total_media`, `player_media_count`, heartbeat `media.total`, and existing historical field names.
- Displays now read memory usage from the agent's `system.memory` field.
- Displays now read disk usage from the agent's `system.disk` field.
- Hub status checks fall back from `/api/v1/status` to the current player's `/api/status` endpoint.
- Added regression coverage using the Welcome Center status payload.

### Installation safety

The installer backs up every replaced file, does not overwrite runtime configuration, validates Python source, runs focused telemetry tests, commits the release, and creates the `v13.1.1` tag.
