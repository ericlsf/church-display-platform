#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source hub/venv/bin/activate
python -m py_compile display/agent/version.py

PYTHONPATH=display python - <<'PY'
from agent.version import VERSION, get_version_info, installed_version, version_info
assert installed_version()
assert VERSION == installed_version()
legacy = get_version_info()
current = version_info()
for key in ("version", "tag", "branch", "commit", "describe", "dirty", "git"):
    assert key in legacy, key
assert legacy["version"] == current["version"]
print("Version compatibility API: PASS")
print("Installed version:", installed_version())
PY

echo
echo "v5.6.3 version API compatibility applied."
echo "Run the production gate before deploying."
