# Church Display Platform v12.1.0

## UI foundation consolidation

- Makes `base.html` the only supported parent template for application pages.
- Removes the duplicate legacy header and navigation from the shared layout.
- Renders the application shell once and gives `<main>` its final layout class server-side.
- Adds a global UI foundation stylesheet with shared design tokens and reusable card, button, badge, form, grid, and action patterns.
- Moves Content Deployments onto the shared base layout.
- Adds Content Deployments to shell route detection and the command palette.
- Adds regression tests that reject pages extending `application_shell.html` directly or bypassing `base.html`.

This release intentionally preserves page-specific CSS while establishing one stable layout and component foundation for gradual migration.
