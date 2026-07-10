
## Release Pipeline

Build a release package from a committed/tagged repository state:

```bash
./release/build_release.py v1.8.0
```

The command writes artifacts to `release/dist/`:

- `church-display-platform-vX.Y.Z.zip`
- `manifest.json`
- `SHA256SUMS`
- `release_notes.md`

Verify a generated package:

```bash
./release/verify.py release/dist/church-display-platform-v1.8.0.zip --manifest release/dist/manifest.json
```

The Hub Releases page is available at `/releases`.
