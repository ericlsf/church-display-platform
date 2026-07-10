#!/usr/bin/env bash
set -u

EXPECTED_VERSION="${1:-}"
HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-90}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-5}"

if [[ -z "$EXPECTED_VERSION" ]]; then
  echo "Usage: $0 vX.Y.Z"
  exit 2
fi

deadline=$(( $(date +%s) + TIMEOUT_SECONDS ))

echo "Waiting for platform health after deployment of $EXPECTED_VERSION..."

while (( $(date +%s) < deadline )); do
  agent_ok=0
  hub_ok=0
  version_ok=0

  systemctl is-active --quiet church-display-agent.service && agent_ok=1
  curl -fsS --max-time 5 "$HUB_URL/health" >/dev/null 2>&1 && hub_ok=1

  current="$(git describe --tags --always 2>/dev/null || true)"
  if [[ "$current" == "$EXPECTED_VERSION"* ]]; then
    version_ok=1
  fi

  if (( agent_ok && hub_ok && version_ok )); then
    echo "Post-deploy verification passed."
    echo "Version: $current"
    exit 0
  fi

  sleep "$INTERVAL_SECONDS"
done

echo "Post-deploy verification failed."
echo "Agent status:"
systemctl --no-pager status church-display-agent.service || true
echo
echo "Current Git version:"
git describe --tags --always --dirty || true
exit 1
