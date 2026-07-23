# v4.13.0 — Stabilization and Production Gate

This release intentionally adds no new Hub feature pages.

## Added

- Repository-wide Python compilation.
- Runtime import validation for every Hub route and service module.
- Flask route smoke tests using the application test client.
- Backup creation, safe extraction, and checksum verification.
- Full unittest execution.
- systemd unit validation.
- Live Hub service and login-page checks.
- Production release builder that refuses dirty or failing source trees.
- SHA-256 release manifest.

## Production gate

Run:

```bash
./scripts/production-gate.sh
```

The command exits nonzero on any failed compile, import, route, backup, test,
systemd, service, or HTTP check.

## Release packaging

After committing and tagging:

```bash
PYTHONPATH=hub:display \
  hub/venv/bin/python \
  scripts/build-production-release.py v4.13.0
```

Artifacts are written to `dist/`.
