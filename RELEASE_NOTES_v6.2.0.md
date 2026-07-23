# v6.2.0 — Bulk Operations

## Added

Operators can select multiple displays and queue:

- Sync Now
- Restart Player
- Reboot Device
- Collect Logs
- Assign Content Folder
- Assign Display Profile
- Enable or disable Maintenance Mode
- Deploy Software Update

## Safety

- Invalid display IDs are ignored.
- At least one valid display is required.
- Required folder, profile, maintenance, and release values are validated.
- Matching active jobs are skipped to prevent duplicates.
- The result reports queued and skipped counts.
