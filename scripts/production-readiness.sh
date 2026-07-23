#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"
cd "$ROOT"

failures=0
warnings=0
pass(){ printf 'PASS  %s\n' "$1"; }
warn(){ printf 'WARN  %s\n' "$1"; warnings=$((warnings+1)); }
fail(){ printf 'FAIL  %s\n' "$1"; failures=$((failures+1)); }

[[ -z "$(git status --porcelain)" ]] && pass "Git working tree clean" || warn "Git working tree has uncommitted changes"
[[ -x scripts/validate-source.sh ]] && ./scripts/validate-source.sh || fail "validate-source.sh unavailable"
systemctl is-active --quiet church-display-hub.service && pass "Hub service active" || fail "Hub service inactive"
systemctl is-active --quiet church-display-agent.service && pass "Agent service active" || fail "Agent service inactive"
curl -fsS --max-time 10 "$HUB_URL/" >/dev/null && pass "Home page responds" || fail "Home page unavailable"
curl -fsS --max-time 10 "$HUB_URL/operations" >/dev/null && pass "Operations page responds" || fail "Operations page unavailable"
curl -fsS --max-time 10 "$HUB_URL/api/v1/jobs?limit=1" >/dev/null && pass "Jobs API responds" || fail "Jobs API unavailable"
[[ -x display/scripts/sync_media.sh ]] && pass "Media sync script executable" || fail "Media sync script not executable"
command -v rclone >/dev/null && pass "rclone installed" || fail "rclone missing"

if grep -q '^CHURCH_DISPLAY_SECRET_KEY=REPLACE_ME' /etc/church-display/hub.env 2>/dev/null; then
  fail "Hub session secret is still REPLACE_ME"
elif grep -q '^CHURCH_DISPLAY_SECRET_KEY=' /etc/church-display/hub.env 2>/dev/null; then
  pass "Hub session secret configured"
else
  warn "Could not confirm Hub session secret"
fi

if [[ -d hub/content/cache ]]; then pass "Hub content cache exists"; else warn "Hub content cache not populated"; fi
if [[ -d hub/content/manifests ]]; then pass "Hub manifests directory exists"; else warn "Hub manifests not populated"; fi

echo
echo "Production readiness: $failures failure(s), $warnings warning(s)."
(( failures == 0 )) || exit 1
