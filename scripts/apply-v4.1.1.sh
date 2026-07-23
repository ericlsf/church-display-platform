#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.1.1.py

cd hub
source venv/bin/activate

python -m py_compile   app.py   routes/display_installer.py   services/display_package.py

echo
echo "Hub bootstrap installer applied."
echo
echo "Restart the Hub, then install a fresh Pi with:"
echo "  curl -fsSL http://church-display-hub.local:8090/install/display | bash"
