# v13.12.0 — Remote Maintenance

- Adds an administrator-only terminal for the Hub and display devices.
- Streams command output, exit status, elapsed time, and recent command history.
- Requires password re-verification and uses a short maintenance unlock window.
- Adds a one-click Hub update workflow with a scheduled service restart.
- Runs display commands through the existing job queue so results remain visible in Activity.
- Audits commands and limits privileged operations to an installed sudo allowlist.

## One-time Hub setup

After pulling this release on the Hub:

```bash
sudo bash scripts/install-remote-maintenance.sh lsfservice
sudo systemctl restart church-display-hub.service
```
