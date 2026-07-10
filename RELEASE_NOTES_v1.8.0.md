# v1.8.0 Release Pipeline

## Added

- Repository release toolchain under `release/`.
- `release/build_release.py` to generate release ZIPs, manifests, checksums, and release notes.
- `release/verify.py` to verify release packages before deployment.
- `manifest.json` support embedded inside generated release ZIPs.
- `SHA256SUMS` generation for release artifacts.
- Hub Releases page at `/releases`.

## Changed

- Release packaging is now repository-generated instead of manually assembled.
- Navigation now includes Releases.

## Notes

Build a release from the repository root:

```bash
./release/build_release.py v1.8.0
```

Verify the generated package:

```bash
./release/verify.py release/dist/church-display-platform-v1.8.0.zip --manifest release/dist/manifest.json
```
