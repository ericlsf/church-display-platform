# Church Display Platform v11.2.1

## Fleet workspace stylesheet hotfix

The v11.2.0 Displays template defined a Jinja `head` block, but the shared base template did not render that block. As a result, the fleet-specific stylesheet was never loaded and the management drawers rendered inline as unstyled page content.

This hotfix:

- Adds the missing `head` extension point to the shared base template.
- Loads the v11.2 fleet stylesheet correctly.
- Adds cache-busting query strings to the fleet CSS and JavaScript assets.
- Restores compact cards, visible action buttons, the responsive grid, and slide-out inspectors.
