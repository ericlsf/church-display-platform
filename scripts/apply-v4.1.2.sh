#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v4.1.2.py

chmod +x display/install.sh
chmod +x hub/static/install-display-bootstrap.sh

cd hub
source venv/bin/activate

python -m py_compile \
  app.py \
  routes/display_installer.py \
  services/display_package.py

echo
echo "v4.1.2 installer architecture applied."
echo "Restart the Hub, then use:"
echo "  bash <(curl -fsSL http://church-display-hub.local:8090/install/display)"
