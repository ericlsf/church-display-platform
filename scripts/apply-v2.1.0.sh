#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/*.sh release/*.py display/scripts/*.sh display/install.sh display/installer/install.sh

if [ -x hub/venv/bin/python ]; then
  hub/venv/bin/python -m py_compile hub/app.py hub/routes/*.py hub/services/*.py
else
  echo "Hub venv not found; skipping Hub compile check."
fi

if [ -x display/venv/bin/python ]; then
  display/venv/bin/python -m py_compile display/app/*.py display/agent/*.py display/agent/jobs/*.py
else
  echo "Display venv not found; skipping Display compile check."
fi

sudo systemctl restart church-display-agent.service 2>/dev/null || true

echo "v2.1.0 files applied. Restart the Hub process to load the new routes and templates."
