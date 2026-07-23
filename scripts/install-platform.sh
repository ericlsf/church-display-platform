#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USER_NAME="${SUDO_USER:-${USER}}"

cd "$ROOT"

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip rclone curl ffmpeg unzip

python3 -m venv hub/venv
hub/venv/bin/python -m pip install --upgrade pip
hub/venv/bin/python -m pip install -r hub/requirements.txt

python3 -m venv display/venv
display/venv/bin/python -m pip install --upgrade pip
display/venv/bin/python -m pip install -r display/requirements.txt

chmod +x scripts/*.sh display/scripts/*.sh release/*.py display/install.sh display/installer/install.sh 2>/dev/null || true

sudo cp hub/systemd/church-display-hub.service /etc/systemd/system/church-display-hub.service
sudo sed -i "s/^User=.*/User=${USER_NAME}/" /etc/systemd/system/church-display-hub.service
sudo sed -i "s#^WorkingDirectory=.*#WorkingDirectory=${ROOT}/hub#" /etc/systemd/system/church-display-hub.service
sudo sed -i "s#^ExecStart=.*#ExecStart=${ROOT}/hub/venv/bin/python ${ROOT}/hub/app.py#" /etc/systemd/system/church-display-hub.service

sudo systemctl daemon-reload
sudo systemctl enable --now church-display-hub.service

if [[ -f /etc/systemd/system/church-display-agent.service ]]; then
  sudo systemctl enable --now church-display-agent.service
fi

echo
echo "Installation complete."
echo "Open: http://$(hostname -I | awk '{print $1}'):8090/setup"
echo "Hub status: systemctl status church-display-hub.service"
