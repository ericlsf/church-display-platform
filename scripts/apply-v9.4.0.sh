#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="backups/v9.4.0-$STAMP"
mkdir -p "$BACKUP/hub/templates" "$BACKUP/hub/static" "$BACKUP/hub/routes" "$BACKUP/hub/services"
for f in hub/templates/command_center.html hub/routes/command_center.py hub/services/command_center.py; do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/$f"
done
for f in hub/static/command-center-v940.css hub/static/command-center-v940.js; do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/$f"
done
cp -a payload/hub/. hub/
python3 -m unittest tests.test_command_center_v940 -v
printf '
v9.4.0 applied. Backup: %s
Restart the hub and run scripts/production-gate.sh.
' "$BACKUP"
