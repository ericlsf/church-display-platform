#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/dev-stop.sh"
sleep 2
"$ROOT_DIR/scripts/dev-start.sh"
"$ROOT_DIR/scripts/dev-status.sh"


