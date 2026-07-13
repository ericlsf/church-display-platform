#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/*.sh 2>/dev/null || true
chmod +x release/*.py 2>/dev/null || true
chmod +x display/scripts/*.sh
chmod +x display/install.sh display/installer/install.sh 2>/dev/null || true

if [ -x hub/venv/bin/python ]; then
  hub/venv/bin/python -m py_compile hub/app.py hub/routes/*.py hub/services/*.py
else
  python3 -m py_compile hub/app.py hub/routes/*.py hub/services/*.py
fi

if [ -x display/venv/bin/python ]; then
  display/venv/bin/python -m py_compile display/app/*.py display/agent/*.py display/agent/jobs/*.py
else
  python3 -m py_compile display/app/*.py display/agent/*.py display/agent/jobs/*.py
fi

sudo systemctl restart church-display-agent.service

echo
echo "v2.2.0 applied."
echo "Restart the Hub process, then deploy a playlist from /content."
