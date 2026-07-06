#!/bin/bash
set -e

PROJECT="/home/lsfservice/church-display"

echo "Installing Church Display..."

cp systemd/*.service /etc/systemd/system/
cp systemd/*.timer /etc/systemd/system/

systemctl daemon-reload

systemctl enable church-display.service
systemctl enable church-sync.timer

echo "Done. Reboot to start."
