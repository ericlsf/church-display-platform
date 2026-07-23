# v5.0.1 — Display Folder Picker

## Fixed

The unified display page no longer uses a free-text field for content-folder
assignment.

## Added

- Selectable folder dropdown populated from the configured Drive remote.
- Current assignment shown prominently.
- Current folder remains selectable even if the Drive listing temporarily fails.
- Duplicate folder names are removed.
- Clear warning when the folder backend cannot be reached.
- Apply button is disabled when no folders are available.

The existing quick-settings workflow continues to queue the folder assignment,
initial sync, and overlay update together.
