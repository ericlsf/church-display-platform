# Church Display Platform

A Raspberry Pi digital-signage platform with a central Flask Hub and display-side player/agent.

## Main areas

- **Dashboard and health:** live heartbeat, preview, sync, version, and system status.
- **Media and content:** Google Drive folder browsing, playlist ordering, deployment, and scheduling.
- **Jobs and deployments:** remote sync, restart, reboot, previews, version checks, tagged deployments, and rollback safeguards.
- **Release pipeline:** reproducible ZIP packages with manifests, checksums, and generated release notes.

## Development

Start both applications with:

```bash
./scripts/dev-start.sh
```

Check status:

```bash
./scripts/dev-status.sh
```

Stop both:

```bash
./scripts/dev-stop.sh
```

## Repository audit

Before committing or tagging:

```bash
./scripts/repo-audit.sh
```

This checks for tracked runtime files and compiles Hub, display, agent, and release Python modules.

## Release pipeline

Build only from a clean committed repository:

```bash
./release/build_release.py v1.8.0
```

Artifacts are written to `release/dist/`:

- `church-display-platform-vX.Y.Z.zip`
- `manifest.json`
- `SHA256SUMS`
- `release_notes.md`

Verify the package:

```bash
./release/verify.py \
  release/dist/church-display-platform-v1.8.0.zip \
  --manifest release/dist/manifest.json
```

For a non-production test build from a dirty tree, explicitly use `--allow-dirty`.

See `docs/ARCHITECTURE.md` for component and runtime ownership details.
