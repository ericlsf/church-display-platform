# v7.0.1 — Vertical Sidebar Layout Fix

## Fixed

Legacy navigation CSS caused the new sidebar groups to render horizontally
inside the sidebar. This created clipped labels and a horizontal scrollbar.

## Changes

- Forces all navigation groups into a vertical stack.
- Forces every group link onto its own row.
- Prevents horizontal overflow.
- Contains labels inside the sidebar width.
- Keeps collapsed mode icon-only.
- Adds runtime enforcement in case legacy styles mutate the navigation layout.
- Preserves mobile navigation behavior.
