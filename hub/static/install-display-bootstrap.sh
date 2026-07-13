#!/usr/bin/env bash
set -euo pipefail

HUB_URL="__HUB_URL__"
INSTALL_ROOT="/opt/church-display"
PACKAGE="/tmp/church-display-package.tar.gz"
DISPLAY_NAME="${CHURCH_DISPLAY_NAME:-}"
AUTO_START="${CHURCH_DISPLAY_AUTO_START:-yes}"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this installer as the desktop user, not with sudo." >&2
  exit 1
fi

clear 2>/dev/null || true
echo "Church Display Setup"
echo "===================="
echo
echo "Hub found: $HUB_URL"
read -rp "Use this Hub? [Y/n]: " answer
answer="${answer:-Y}"

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
  read -rp "Hub URL: " HUB_URL
  HUB_URL="${HUB_URL%/}"
fi

if [[ -z "$DISPLAY_NAME" ]]; then
  read -rp "Display name [$(hostname)]: " DISPLAY_NAME
  DISPLAY_NAME="${DISPLAY_NAME:-$(hostname)}"
fi

read -rp "Start automatically when the Pi boots? [Y/n]: " start_answer
start_answer="${start_answer:-Y}"
if [[ "$start_answer" =~ ^[Nn]$ ]]; then
  AUTO_START="no"
fi

echo
echo "Hub:     $HUB_URL"
echo "ID:      $(hostname)"
echo "Name:    $DISPLAY_NAME"
echo
read -rp "Install? [Y/n]: " install_answer
install_answer="${install_answer:-Y}"
[[ "$install_answer" =~ ^[Yy]$ ]] || exit 0

echo "Downloading display package..."
curl -fsSL "$HUB_URL/install/display/package.tar.gz" -o "$PACKAGE"

echo "Extracting display package..."
sudo rm -rf "$INSTALL_ROOT"
sudo mkdir -p "$INSTALL_ROOT"
sudo tar -xzf "$PACKAGE" -C "$INSTALL_ROOT"
sudo chown -R "$USER:$USER" "$INSTALL_ROOT"

chmod +x "$INSTALL_ROOT/display/install.sh"

args=(
  --hub-url "$HUB_URL"
  --display-name "$DISPLAY_NAME"
  --display-id "$(hostname)"
  --non-interactive
)

if [[ "$AUTO_START" != "yes" ]]; then
  args+=(--no-player)
fi

exec "$INSTALL_ROOT/display/install.sh" "${args[@]}"
