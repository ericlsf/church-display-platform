#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
systemctl disable --now cloudflared.service 2>/dev/null || true
cloudflared service uninstall 2>/dev/null || true
rm -f /etc/church-display/remote-access.json
echo "Cloudflare Tunnel service disabled. The Cloudflare hostname and Access application must be removed separately in the Cloudflare dashboard."
