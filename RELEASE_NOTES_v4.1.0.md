# v4.1.0 — Fast display installation

## Added

- One-command display installer.
- Hub URL and display-name arguments.
- Raspberry Pi package and Python dependency installation.
- Display and agent service generation.
- Restricted sudo policy for approved remote recovery operations.
- Automatic enrollment registration.
- Hub and job-endpoint connectivity checks.
- Post-install service self-test.
- New-display deployment guide.

## Installation

```bash
./scripts/install-display.sh \
  --hub-url http://church-display-hub.local:8090 \
  --display-name "Lobby Display"
```
