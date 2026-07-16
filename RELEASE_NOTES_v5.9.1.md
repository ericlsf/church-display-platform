# v5.9.1 — Overlay Preview Layout Fix

## Fixed

The content editor was embedded inside a narrow display-details column but
still attempted to render a two-column editor. This caused the preview to
overlap the adjacent Display Profile panel.

The preview overlay also used physical-display-sized typography inside a small
browser preview, causing the overlay text, clock, and countdown to collide.

## Changes

- Forces the editor into a contained single-column layout.
- Removes sticky preview positioning.
- Prevents all editor controls from widening their parent card.
- Scales preview text using responsive font sizes.
- Limits and truncates long overlay and countdown text.
- Reserves separate collision-safe areas for overlay, clock, and countdown.
- Allows the overlay to use the full width when countdown is disabled.
