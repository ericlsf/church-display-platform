# v4.2.1 — Provisioning polish and cursor hiding

## Added

- Qt-level cursor hiding for kiosk playback.
- Display readiness scoring.
- Ready, Provisioning, Needs Playlist, and Needs Attention states.
- One-click retry for incomplete initial provisioning.
- Readiness checks for heartbeat, player, playlist, local media, and sync result.

## Changed

The cursor is hidden by the display application itself after automatic launch,
which is reliable under the Wayland kiosk session and does not depend on mouse
movement or desktop utilities.
