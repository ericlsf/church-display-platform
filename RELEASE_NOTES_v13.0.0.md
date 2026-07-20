# Church Display Platform v13.0.0

## Fleet Health Workspace

The Displays workspace now provides a live operational view of each display instead of only showing assignments.

### Added

- Fleet-wide counts for displays needing attention and active jobs.
- Per-display player health, software-update state, and job progress.
- Live media count, CPU temperature, disk usage, and memory usage.
- A live-health section in the display inspector.
- Expanded `/displays/api/status` telemetry for health and job information.
- Automatic 15-second refresh of the new health fields.
- Visual attention treatment for displays with stopped players, failed jobs, sync errors, available updates, or offline status.

### Compatibility

This release uses the existing heartbeat and job data. Displays that do not yet report a metric show `Unknown` rather than failing the page.
