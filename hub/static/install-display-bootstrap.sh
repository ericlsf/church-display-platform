#!/usr/bin/env bash
set -euo pipefail

DEFAULT_HUB_URL="__HUB_URL__"
HUB_URL="${CHURCH_DISPLAY_HUB_URL:-$DEFAULT_HUB_URL}"
DISPLAY_NAME="${CHURCH_DISPLAY_NAME:-}"
DISPLAY_ID="${CHURCH_DISPLAY_ID:-}"
AUTO_START="${CHURCH_DISPLAY_AUTO_START:-yes}"
INSTALL_ROOT="/opt/church-display"
PACKAGE="/tmp/church-display-package.tar.gz"

step() {
  printf '\n\033[1;36m%s\033[0m\n' "$1"
}

ok() {
  printf '\033[1;32m✓\033[0m %s\n' "$1"
}

warn() {
  printf '\033[1;33m!\033[0m %s\n' "$1"
}

die() {
  printf '\033[1;31mERROR:\033[0m %s\n' "$1" >&2
  exit 1
}

normalize_id() {
  printf '%s' "$1" |
    tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

prompt_yes_no() {
  local prompt="$1"
  local default="${2:-yes}"
  local answer=""

  if [[ "$default" == "yes" ]]; then
    read -rp "$prompt [Y/n]: " answer
    answer="${answer:-Y}"
  else
    read -rp "$prompt [y/N]: " answer
    answer="${answer:-N}"
  fi

  [[ "$answer" =~ ^[Yy]$ ]]
}

if [[ "$(id -u)" -eq 0 ]]; then
  die "Run this as the desktop user, not with sudo."
fi

if [[ ! -t 0 ]]; then
  die "Interactive setup requires: bash <(curl -fsSL $DEFAULT_HUB_URL/install/display)"
fi

clear 2>/dev/null || true
cat <<'BANNER'
╔══════════════════════════════════════════╗
║          Church Display Setup            ║
╚══════════════════════════════════════════╝
BANNER

echo
echo "This setup installs only the display player and agent."
echo "Normal management happens from the Hub after enrollment."

step "1 of 5 — Find the Hub"

if curl -fsS --max-time 8 "$HUB_URL/setup" >/dev/null 2>&1; then
  ok "Found Hub at $HUB_URL"
else
  warn "The default Hub did not respond: $HUB_URL"
  read -rp "Enter the Hub URL: " HUB_URL
  HUB_URL="${HUB_URL%/}"

  curl -fsS --max-time 10 "$HUB_URL/setup" >/dev/null 2>&1 \
    || die "The Hub is not reachable at $HUB_URL"
  ok "Connected to $HUB_URL"
fi

step "2 of 5 — Name this display"

HOSTNAME_VALUE="$(hostname)"
PROPOSED_ID="$(normalize_id "$HOSTNAME_VALUE")"

if [[ -z "$DISPLAY_NAME" ]]; then
  read -rp "Friendly name [$HOSTNAME_VALUE]: " DISPLAY_NAME
  DISPLAY_NAME="${DISPLAY_NAME:-$HOSTNAME_VALUE}"
fi

if [[ -z "$DISPLAY_ID" ]]; then
  read -rp "Stable ID [$PROPOSED_ID]: " DISPLAY_ID
  DISPLAY_ID="${DISPLAY_ID:-$PROPOSED_ID}"
fi

DISPLAY_ID="$(normalize_id "$DISPLAY_ID")"
[[ -n "$DISPLAY_ID" ]] || die "The stable display ID cannot be empty."

if prompt_yes_no "Start the player automatically after boot?" "yes"; then
  AUTO_START="yes"
else
  AUTO_START="no"
fi

echo
echo "Hub:          $HUB_URL"
echo "Hostname:     $HOSTNAME_VALUE"
echo "Stable ID:    $DISPLAY_ID"
echo "Friendly name:$DISPLAY_NAME"
echo "Auto-start:   $AUTO_START"

prompt_yes_no "Continue with installation?" "yes" || exit 0

step "3 of 5 — Download the display software"

curl -fL --retry 3 --retry-delay 2 --connect-timeout 10 \
  "$HUB_URL/install/display/package.tar.gz" \
  -o "$PACKAGE" \
  || die "Could not download the display package."

[[ -s "$PACKAGE" ]] || die "The downloaded package is empty."
ok "Display package downloaded"

step "4 of 5 — Install"

sudo mkdir -p "$INSTALL_ROOT"

if [[ -d "$INSTALL_ROOT/display" ]]; then
  BACKUP="$INSTALL_ROOT/display-backup-$(date +%Y%m%d-%H%M%S)"
  warn "An existing installation was found."
  sudo mv "$INSTALL_ROOT/display" "$BACKUP"
  ok "Existing installation backed up to $BACKUP"
fi

sudo tar -xzf "$PACKAGE" -C "$INSTALL_ROOT"
sudo chown -R "$USER:$USER" "$INSTALL_ROOT"

[[ -x "$INSTALL_ROOT/display/install.sh" ]] || \
  chmod +x "$INSTALL_ROOT/display/install.sh"

ARGS=(
  --hub-url "$HUB_URL"
  --display-name "$DISPLAY_NAME"
  --display-id "$DISPLAY_ID"
  --non-interactive
)

if [[ "$AUTO_START" != "yes" ]]; then
  ARGS+=(--no-player)
fi

"$INSTALL_ROOT/display/install.sh" "${ARGS[@]}"

step "5 of 5 — Verify enrollment"

STATUS_URL="$HUB_URL/discovery/status?display_id=$DISPLAY_ID"
STATUS="unknown"

for attempt in $(seq 1 12); do
  RESPONSE="$(curl -fsS --max-time 8 "$STATUS_URL" 2>/dev/null || true)"
  STATUS="$(
    python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("status", "unknown"))
except Exception:
    print("unknown")' <<<"$RESPONSE"
  )"

  case "$STATUS" in
    approved|pending)
      break
      ;;
  esac

  sleep 2
done

echo
case "$STATUS" in
  approved)
    ok "The Hub recognizes this display as approved."
    ;;
  pending)
    ok "The display is waiting for approval."
    ;;
  *)
    warn "The agent is installed, but enrollment status could not be confirmed."
    ;;
esac

systemctl is-active --quiet church-display-agent.service \
  && ok "Display agent is running" \
  || warn "Display agent is not running"

if [[ "$AUTO_START" == "yes" ]]; then
  systemctl is-active --quiet church-display.service \
    && ok "Display player is running" \
    || warn "The player may be waiting for the graphical desktop session"
fi

rm -f "$PACKAGE"

cat <<EOF

╔══════════════════════════════════════════╗
║             Setup Complete               ║
╚══════════════════════════════════════════╝

Display ID:
  $DISPLAY_ID

Next step:
  Open $HUB_URL/setup

Then:
  1. Approve the display.
  2. Confirm the stable ID.
  3. Select the initial playlist.
  4. Wait for the display to show Ready.

Diagnostics:
  sudo systemctl status church-display-agent.service --no-pager
  sudo journalctl -u church-display-agent.service -n 100 --no-pager
EOF
