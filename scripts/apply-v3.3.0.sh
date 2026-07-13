#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_NAME="${SUDO_USER:-$USER}"

cd "$ROOT"
chmod +x scripts/*.sh scripts/*.py display/scripts/*.sh release/*.py 2>/dev/null || true

sudo cp hub/systemd/church-display-backup.service /etc/systemd/system/church-display-backup.service
sudo cp hub/systemd/church-display-backup.timer /etc/systemd/system/church-display-backup.timer
sudo sed -i "s/^User=.*/User=$USER_NAME/" /etc/systemd/system/church-display-backup.service
sudo sed -i "s|^WorkingDirectory=.*|WorkingDirectory=$ROOT|" /etc/systemd/system/church-display-backup.service
sudo sed -i "s|^ExecStart=.*|ExecStart=$ROOT/hub/venv/bin/python $ROOT/scripts/backup-platform.py|" /etc/systemd/system/church-display-backup.service

sudo systemctl daemon-reload
sudo systemctl enable --now church-display-backup.timer

cd hub
source venv/bin/activate
python -m py_compile app.py routes/*.py services/*.py

cd ../display
source venv/bin/activate
python -m py_compile agent/*.py agent/jobs/*.py

echo "v3.3.0 applied. Restart Hub and agent services."
