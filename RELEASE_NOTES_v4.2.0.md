# v4.2.0 — Robust setup and enrollment

## Fixed

- The Hub no longer generates a new display ID from the friendly name.
- Hostname word boundaries are preserved as dashes.
- Registration stores and returns the display's proposed stable ID.
- Existing approved displays return their Hub-assigned identity when registering.
- Plain Sync Now fails immediately with a useful message when no playlist is assigned.

## Added

- Editable stable ID during enrollment.
- Required initial playlist selection.
- Hub cache preparation during approval.
- Automatic initial `set_sync_folder` job.
- Enrollment status endpoint.
- Provisioning state and initial-sync progress on the Setup page.
- Installer normalization of hostnames such as `Welcome-Center` to `welcome-center`.

## Result

A newly installed display follows this sequence:

1. Propose stable ID from hostname.
2. Appear in pending enrollment with that exact ID.
3. Administrator confirms ID, name, and initial playlist.
4. Hub prepares the playlist cache.
5. Hub queues the initial folder assignment and sync.
6. Setup reports provisioning status and Ready state.
