# v4.10.0 — Notification Center

## Added

- Central notification inbox.
- Unread badge in Hub navigation.
- Pending-enrollment notifications.
- Failed job notifications.
- Completed deployment, sync, restart, and settings notifications.
- Offline-display notifications outside maintenance mode.
- Mark read, mark all read, dismiss, and clear completed actions.
- Direct links to the relevant Hub page.
- Automatic refresh every 30 seconds.

## Deduplication

Each event source is recorded once, preventing repeated notifications for the
same job or enrollment request.
