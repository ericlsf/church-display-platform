# v8.0.1 — Breadcrumb Layout Fix

## Fixed

The compact v8 breadcrumb bar inherited a larger line-height than its assigned
30px height, causing breadcrumb labels to be vertically clipped.

## Changes

- Increases the breadcrumb row to 36px.
- Vertically centers all breadcrumb items.
- Removes inherited overflow clipping.
- Keeps long current-page labels safely truncated.
- Updates the main-content top offset to match the corrected height.
- Adds runtime enforcement against legacy style overrides.
