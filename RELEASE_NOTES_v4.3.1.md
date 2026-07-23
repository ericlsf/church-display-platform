# v4.3.1 — Per-display presentation settings

## Added

The Displays page now provides per-display controls for:

- overlay enabled/disabled;
- overlay text;
- clock enabled/disabled;
- countdown enabled/disabled;
- countdown display window;
- image duration.

Saving creates an `apply_display_settings` job for that display. The agent
updates only presentation-related values in its local `config.json`, preserving
the assigned playlist, media cache, schedules, and other display configuration.

The player already reloads configuration automatically, so changes normally
appear within approximately two seconds without restarting the display app.
