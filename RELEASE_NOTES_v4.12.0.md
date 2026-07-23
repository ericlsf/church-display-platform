# v4.12.0 — Display Profiles

## Added

- Create reusable presentation profiles.
- Edit profile names, descriptions, and presentation settings.
- Apply profiles to individual displays or saved groups.
- Clone an existing profile.
- Mark one profile as the default.
- Export profiles as portable JSON.
- Import portable profile JSON.
- Keep the 20 most recent revisions for each profile.
- Restore a previous revision.
- Preview profile contents before applying.

## Profile settings

Profiles currently contain:

- overlay enabled state;
- overlay text;
- clock enabled state;
- countdown enabled state;
- countdown display window;
- image duration.

## Display behavior

Applying a profile creates an `apply_display_settings` job for every resolved
target. Existing playlists, media files, schedules, and unrelated display
configuration are preserved.
