#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(pwd)}"; RELEASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="$ROOT/backups/v9.7.0-$STAMP"
mkdir -p "$BACKUP"
for path in hub/templates/media.html hub/routes/media.py tests/test_command_center_v920.py; do if [[ -f "$ROOT/$path" ]]; then mkdir -p "$BACKUP/$(dirname "$path")"; cp -a "$ROOT/$path" "$BACKUP/$path"; fi; done
cp -a "$RELEASE_DIR/payload/." "$ROOT/"
python3 -m py_compile "$ROOT/hub/routes/media.py"
python3 "$ROOT/tests/test_media_library_v970.py"
python3 "$ROOT/tests/test_command_center_v920.py"
echo "v9.7.0 installed. Backup: $BACKUP"
