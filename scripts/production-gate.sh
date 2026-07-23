#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="$ROOT/hub/venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "FAIL  Hub virtual environment is missing: $PYTHON"
  exit 1
fi

echo "1. Compile active source"
"$PYTHON" -m compileall -q   hub   display/app   display/agent   display/scripts

echo "2. Validate runtime imports"
PYTHONPATH=hub "$PYTHON" scripts/validate-runtime-imports.py

echo "3. Run Hub route smoke tests"
PYTHONPATH=hub "$PYTHON" scripts/smoke-test-hub.py

echo "4. Verify backup and restore"
PYTHONPATH=hub "$PYTHON" scripts/verify-backup-restore.py

echo "5. Run test suite"
PYTHONPATH=hub:display "$PYTHON" -m unittest discover -s tests -v

echo "6. Validate systemd units"
systemd-analyze verify \
  /etc/systemd/system/church-display-hub.service

if [[ -f /etc/systemd/system/church-display-rollouts.service ]]; then
  systemd-analyze verify \
    /etc/systemd/system/church-display-rollouts.service \
    /etc/systemd/system/church-display-rollouts.timer
fi

echo "7. Check Hub service"
systemctl is-active --quiet church-display-hub.service
echo "PASS  Hub service active"

echo "8. Check local HTTP response"
STATUS="$(
  curl -sS -o /dev/null -w '%{http_code}' \
    http://127.0.0.1:8090/login
)"

case "$STATUS" in
  200|301|302|303|307|308)
    echo "PASS  Login page HTTP $STATUS"
    ;;
  *)
    echo "FAIL  Login page HTTP $STATUS"
    exit 1
    ;;
esac

echo
echo "Production gate: PASS"
