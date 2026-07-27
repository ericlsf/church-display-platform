#!/usr/bin/env bash
set -euo pipefail

SERVICE_USER="${1:-${SUDO_USER:-lsfservice}}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER_TARGET="/usr/local/sbin/church-display-hub-update"
SUDOERS_TARGET="/etc/sudoers.d/church-display-maintenance"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

install -m 0755 "$REPO_ROOT/scripts/church-display-hub-update" "$HELPER_TARGET"

cat >"$SUDOERS_TARGET" <<EOF
${SERVICE_USER} ALL=(root) NOPASSWD: ${HELPER_TARGET}
${SERVICE_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart church-display-hub.service
${SERVICE_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status church-display-hub.service
${SERVICE_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart church-display-agent.service
${SERVICE_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart church-display.service
${SERVICE_USER} ALL=(root) NOPASSWD: /usr/sbin/reboot
EOF
chmod 0440 "$SUDOERS_TARGET"
visudo -cf "$SUDOERS_TARGET"

echo "Remote maintenance helper installed for ${SERVICE_USER}."
