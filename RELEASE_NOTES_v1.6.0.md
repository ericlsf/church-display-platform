# Church Display Platform v1.6.0

This release intentionally defers fleet/group management and focuses on the remaining operational areas:

- Media Management page with Google Drive folder analysis and direct sync queuing.
- Health Monitoring refresh with heartbeat metrics, system stats, app version, sync state, and alerts.
- Scheduling page for scheduled syncs, folder changes, restarts, reboots, and deployments.
- Optional Hub scheduler systemd timer files.
- UI polish for tables, badges, stat cards, and dashboard consistency.

## Optional scheduler timer

To have due schedules processed every minute without opening the Schedules page:

```bash
cd ~/church-display-platform/hub
sudo cp systemd/church-display-hub-scheduler.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now church-display-hub-scheduler.timer
```

## Install

```bash
cd ~
unzip -o church-display-platform-v1.6.0-ops-release.zip
cp -a church-display-platform-main/. ~/church-display-platform/

cd ~/church-display-platform/hub
source venv/bin/activate
python -m py_compile app.py routes/*.py services/*.py
sudo fuser -k 8090/tcp
python app.py
```
