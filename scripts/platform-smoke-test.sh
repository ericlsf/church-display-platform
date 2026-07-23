#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"
DISPLAY_ID="${DISPLAY_ID:-$(hostname)}"
FAILURES=0
WARNINGS=0

pass() { printf 'PASS  %s\n' "$1"; }
warn() { printf 'WARN  %s\n' "$1"; WARNINGS=$((WARNINGS + 1)); }
fail() { printf 'FAIL  %s\n' "$1"; FAILURES=$((FAILURES + 1)); }

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    pass "command available: $1"
  else
    fail "missing command: $1"
  fi
}

check_http() {
  local path="$1"
  local label="$2"
  local code
  code="$(curl -sS -o /tmp/church-display-smoke-body -w '%{http_code}' --max-time 10 "${HUB_URL}${path}" 2>/dev/null || true)"
  if [[ "$code" =~ ^2|3 ]]; then
    pass "$label (${path}) HTTP $code"
  else
    fail "$label (${path}) HTTP ${code:-unreachable}"
  fi
}

cd "$ROOT"

echo "Church Display platform smoke test"
echo "Root: $ROOT"
echo "Hub:  $HUB_URL"
echo

check_command python3
check_command git
check_command curl
check_command rclone
check_command systemctl

if [[ -d hub/venv ]]; then
  pass "Hub virtual environment exists"
else
  fail "Hub virtual environment missing"
fi

if [[ -d display/venv ]]; then
  pass "Display virtual environment exists"
else
  fail "Display virtual environment missing"
fi

if [[ -x display/scripts/sync_media.sh ]]; then
  pass "sync_media.sh is executable"
else
  fail "display/scripts/sync_media.sh is not executable"
fi

if systemctl is-active --quiet church-display-agent.service; then
  pass "church-display-agent.service is active"
else
  fail "church-display-agent.service is not active"
fi

if systemctl list-unit-files church-display.service >/dev/null 2>&1; then
  if systemctl is-active --quiet church-display.service; then
    pass "church-display.service is active"
  elif systemctl is-enabled --quiet church-display.service 2>/dev/null; then
    warn "church-display.service is enabled but inactive"
  else
    warn "church-display.service is installed but intentionally inactive/disabled"
  fi
else
  warn "church-display.service not installed"
fi

check_http "/" "Hub home"
check_http "/health" "Health page"
check_http "/content" "Content page"
check_http "/deployments" "Deployments page"
check_http "/api/v1/jobs?limit=1" "Jobs API"

if curl -fsS --max-time 10 "${HUB_URL}/api/v1/jobs/next?display_id=${DISPLAY_ID}" \
  >/tmp/church-display-next-job.json 2>/dev/null; then
  pass "Display agent job-poll endpoint responds"
else
  fail "Display agent job-poll endpoint failed"
fi

if [[ -f display/status/sync.json ]]; then
  if python3 - <<'PY'
import json
from pathlib import Path
p = Path("display/status/sync.json")
data = json.loads(p.read_text())
assert isinstance(data, dict)
PY
  then
    pass "display/status/sync.json is valid JSON"
  else
    fail "display/status/sync.json is invalid"
  fi
else
  warn "display/status/sync.json not created yet"
fi

if [[ -d hub/content/cache ]]; then
  pass "Hub content cache directory exists"
else
  warn "Hub content cache has not been populated yet"
fi

if [[ -d hub/content/manifests ]]; then
  bad=0
  while IFS= read -r -d '' file; do
    if ! python3 - "$file" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
assert isinstance(data, dict)
assert "files" in data
PY
    then
      fail "invalid manifest: $file"
      bad=1
    fi
  done < <(find hub/content/manifests -type f -name '*.json' -print0 2>/dev/null)
  if [[ "$bad" -eq 0 ]]; then
    pass "Hub content manifests are valid JSON"
  fi
else
  warn "Hub manifest directory has not been populated yet"
fi

if [[ -f scripts/run-tests.sh ]]; then
  if ./scripts/run-tests.sh; then
    pass "Automated test suite passed"
  else
    fail "Automated test suite failed"
  fi
else
  warn "scripts/run-tests.sh not found"
fi

echo
echo "Smoke test complete: ${FAILURES} failure(s), ${WARNINGS} warning(s)."

if [[ "$FAILURES" -gt 0 ]]; then
  exit 1
fi
