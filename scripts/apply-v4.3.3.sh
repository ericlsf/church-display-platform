#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p hub/data/display-releases

source hub/venv/bin/activate

python -m py_compile \
  hub/services/display_artifacts.py \
  hub/routes/display_releases.py \
  hub/routes/deployments.py

PYTHONPATH=hub python -m unittest \
  tests.test_display_artifacts \
  tests.test_display_release_determinism \
  tests.test_display_release_paths \
  -v

echo
echo "v4.3.3 immutable display artifacts applied."
echo "Cancel old checksum-mismatch jobs and queue a brand-new deployment."
