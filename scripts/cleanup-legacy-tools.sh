#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MIGRATIONS_DIR="tools/migrations"
mkdir -p "$MIGRATIONS_DIR"

echo "Removing known broken obsolete deployment helper..."
rm -f scripts/apply-deployments-page.py
rm -f scripts/apply-deployments-page.sh

echo "Archiving completed one-time apply scripts..."

shopt -s nullglob

for file in scripts/apply-v*.py scripts/apply-v*.sh; do
  base="$(basename "$file")"
  target="$MIGRATIONS_DIR/$base"

  if [[ -e "$target" ]]; then
    rm -f "$file"
    continue
  fi

  mv "$file" "$target"
  echo "  moved $file -> $target"
done

shopt -u nullglob

cat > "$MIGRATIONS_DIR/README.md" <<'EOF'
# Historical migration helpers

These scripts were used to apply earlier one-time release migrations.

They are retained for historical reference and disaster recovery, but they are
not active application code and are excluded from normal source validation.

New releases should update the current source tree directly and use the release
pipeline rather than adding another permanent `apply-vX.Y.Z` helper.
EOF

echo
echo "Legacy tool cleanup complete."
echo "Run ./scripts/validate-source.sh next."
