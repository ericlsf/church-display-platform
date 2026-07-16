# v6.5.0 — Alert Acknowledgement and Resolution Tracking

## Added

- Acknowledge active alerts.
- Separate Active and Acknowledged views.
- Restore an acknowledged alert to the active list.
- Persistent acknowledgement state.
- Acknowledgement user and timestamp.
- Automatic cleanup when the underlying alert resolves.
- Active severity counts exclude acknowledged alerts.

## Behavior

Acknowledging an alert does not suppress the underlying health check. If the
condition resolves, its stored acknowledgement is removed automatically. If
the same condition occurs again later, it returns as a new active alert.
