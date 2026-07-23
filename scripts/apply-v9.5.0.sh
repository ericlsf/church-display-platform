#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$ROOT/backups/v9.5.0-$STAMP"
[[ -f "$ROOT/hub/app.py" ]] || { echo "Run from the church-display-platform repository root." >&2; exit 1; }
mkdir -p "$BACKUP/hub/templates" "$BACKUP/hub/static"
for file in hub/templates/media.html hub/static/media-library-v950.css hub/static/media-library-v950.js; do
  [[ -f "$ROOT/$file" ]] && { mkdir -p "$BACKUP/$(dirname "$file")"; cp -a "$ROOT/$file" "$BACKUP/$file"; }
done
cp -a "$PACKAGE_ROOT/payload/." "$ROOT/"
chmod 0644 "$ROOT/hub/templates/media.html" "$ROOT/hub/static/media-library-v950.css" "$ROOT/hub/static/media-library-v950.js"
echo "v9.5.0 installed. Backup: $BACKUP"
