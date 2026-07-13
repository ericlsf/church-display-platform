#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/apply-v2.5.0.py
chmod +x scripts/install-platform.sh
if [[ -d hub/venv ]]; then
  hub/venv/bin/python -m py_compile hub/app.py hub/routes/*.py hub/services/*.py
fi
echo "v2.5.0 applied. Restart Hub and open /setup or /system."
