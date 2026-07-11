# v3.1.2 — Display app recovery

## Added

- Heartbeat-reported `church-display.service` state.
- Automatic alert when the agent is online but the display app is stopped.
- Start/restart display app controls on Dashboard, Live Operations, and Displays.
- Verification that a restart job actually leaves the display service active.

## Behavior

The existing `restart_display` job now acts as both **Start Display App** and **Restart Display App**. An inactive service is started by `systemctl restart`; an active service is restarted normally.
