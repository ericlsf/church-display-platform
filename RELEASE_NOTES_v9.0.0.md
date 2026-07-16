# v9.0.0 — Single Application Shell

- Replaces layered v7/v8 navigation with one application shell.
- Installs one sidebar, one top bar, and one breadcrumb row.
- Removes old shell JavaScript references from base.html.
- Loads a dedicated shell stylesheet instead of appending more overrides.
- Creates a timestamped backup of base.html.
- Removes late-rendered legacy navigation and clears legacy page offsets.
- Uses one authoritative offset: 58px top bar + 34px breadcrumb.
