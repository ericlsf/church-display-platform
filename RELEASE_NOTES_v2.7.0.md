# v2.7.0 — Live operations and fleet groups

## Added
- Live Operations console using Server-Sent Events.
- Automatic display, health, current-media, version, preview, and job-progress updates.
- Display groups with persistent membership.
- Group folder assignment and immediate sync.
- Group sync, heartbeat, restart, reboot, and app deployment actions.
- Group online/outdated summaries.

## Notes
- Existing dashboard SSE remains supported.
- Group runtime configuration is stored outside Git.
- Existing global role enforcement continues to protect mutating routes when authentication is enabled.
