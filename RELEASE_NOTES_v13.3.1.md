# Church Display Platform v13.3.1

## Live Device Health Reliability & Workspace Polish

This maintenance release fixes the display-details telemetry regression introduced when the remote screenshot workspace began polling the raw fleet-state endpoint.

### Fixed

- CPU temperature, memory, storage, status, and heartbeat no longer revert to **Unknown** after the 15-second live refresh.
- The details page now consumes the same normalized telemetry endpoint as the working All Displays page.
- Initial server rendering correctly flattens nested heartbeat `system` values.
- Percentage and temperature values are formatted safely whether the player sends numbers or already-formatted strings.

### Improved

- Prominent health status badge and four-metric summary strip.
- Memory is now visible alongside CPU temperature, storage, and media count.
- Quick actions for screenshot, media sync, player restart, log collection, and device reboot.
- Runtime summary with version, player state, heartbeat, uptime, and sync state.
- Network summary with IP address, hostname, and display ID.
- Screenshot metadata now includes capture age and current media.
- Responsive layout for tablets and phones.

### Installation safety

The installer preserves runtime configuration, backs up replaced files, validates the Python source, runs focused regression tests, commits the installed release, and creates the `v13.3.1` Git tag.
