# v4.4.0 — Installer polish

## Improvements

- Five-step guided setup with clearer progress.
- Automatic Hub connectivity check and manual fallback.
- Stable display ID shown and editable before installation.
- Existing installation is backed up instead of silently deleted.
- Download retries and empty-package validation.
- Registration rejects unexpected Hub/display ID mismatches.
- Installer polls enrollment status after setup.
- Final summary distinguishes pending approval from approved status.
- Actionable commands are printed for diagnostics.
- New installer health endpoint:
  `/install/display/health`.

## Recommended install command

```bash
bash <(curl -fsSL http://church-display-hub.local:8090/install/display)
```
