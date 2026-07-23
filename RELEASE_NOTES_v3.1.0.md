# v3.1.0 — Operator workflow

## Added

- Consolidated operator dashboard focused on attention items, active work, content status, schedules, and display state.
- Global search across displays, groups, sites, playlists, and jobs.
- Notification center with dismissible recurring operational notifications.
- Draft and published playlist states.
- Explicit publish, discard, deploy-published, and schedule-published actions.

## Changed

- Editing playlist order now saves a draft instead of immediately changing live playback order.
- Google Drive reconciliation preserves both published and draft order while inserting new or modified files according to playlist policy.
- The header includes global search and notification count.

## Runtime files

Notification dismissals remain local in `hub/config/notification_dismissals.json` and are ignored by Git.
