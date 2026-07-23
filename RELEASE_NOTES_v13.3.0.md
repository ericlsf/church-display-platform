# Church Display Platform v13.3.0

## Remote Screenshots

This release delivers the first Fleet Operations feature in the planned order: a polished remote screenshot workflow.

### Added

- A dedicated live screenshot workspace on every display details page.
- One-click **Take Screenshot** requests without SSH.
- Automatic screenshot status polling every 10 seconds.
- Screenshot freshness indicators and stale-state highlighting.
- Full-size screenshot viewing in a lightbox or separate browser tab.
- Screenshot job progress and failure messaging.
- A versioned screenshot API:
  - `GET /api/v1/displays/<display_id>/screenshot`
  - `POST /api/v1/displays/<display_id>/screenshot`
- Preview metadata including capture time, age, file size, and availability.

### Compatibility

The release uses the player agent's existing `upload_preview` job and automatic preview uploads. No player reconfiguration is required.

### Installation safety

The installer backs up replaced files, validates Python imports and routes, runs focused tests, commits the installed release, and creates the `v13.3.0` Git tag.
