#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-}"
ALLOW_DIRTY="${ALLOW_DIRTY:-0}"

cd "$ROOT"

if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 vX.Y.Z"
  exit 2
fi

if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v2.4.1"
  exit 2
fi

echo "Validating release $VERSION"
echo

if [[ "$ALLOW_DIRTY" != "1" ]] && [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is dirty. Commit or stash changes first."
  git status --short
  exit 1
fi

git fetch --tags origin

if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "Tag $VERSION already exists."
  exit 1
fi

if [[ -x scripts/repo-audit.sh ]]; then
  ./scripts/repo-audit.sh
fi

if [[ -x scripts/run-tests.sh ]]; then
  ./scripts/run-tests.sh
fi

python3 -m compileall -q hub display release

HUB_URL="${HUB_URL:-http://127.0.0.1:8090}" \
  ./scripts/platform-smoke-test.sh

if [[ -x release/build_release.py ]] && [[ -x release/verify.py ]]; then
  ./release/build_release.py "$VERSION"

  ZIP="release/dist/church-display-platform-${VERSION}.zip"
  MANIFEST="release/dist/manifest.json"

  if [[ ! -f "$ZIP" ]]; then
    echo "Expected release archive not found: $ZIP"
    exit 1
  fi

  ./release/verify.py "$ZIP" --manifest "$MANIFEST"
else
  echo "Release toolchain is missing or not executable."
  exit 1
fi

echo
echo "Release $VERSION validated successfully."
echo "Next:"
echo "  git tag -a $VERSION -m \"$VERSION\""
echo "  git push origin $VERSION"
