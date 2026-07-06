#!/usr/bin/env bash
set -u

HUB_URL="${HUB_URL:-http://127.0.0.1:8090}"
DISPLAY_PORT="${DISPLAY_PORT:-8080}"
VERSION="${DISPLAY_VERSION:-1.1.0}"

HOSTNAME_VALUE="$(hostname)"
IP_VALUE="$(hostname -I | awk '{print $1}')"
DISPLAY_HOST="http://${IP_VALUE}:${DISPLAY_PORT}"

curl -sS -X POST "${HUB_URL}/discovery/register" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"${HOSTNAME_VALUE}\",\"hostname\":\"${HOSTNAME_VALUE}\",\"ip\":\"${IP_VALUE}\",\"host\":\"${DISPLAY_HOST}\",\"version\":\"${VERSION}\"}" >/dev/null
