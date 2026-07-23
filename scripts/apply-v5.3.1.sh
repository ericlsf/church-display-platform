#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/apply-v5.3.1.py

source hub/venv/bin/activate

python -m py_compile \
  hub/app.py \
  hub/routes/dashboard.py \
  hub/routes/command_center_home.py

PYTHONPATH=hub python - <<'PY'
import app as hub_app

app = getattr(hub_app, "app", None)
if app is None:
    app = hub_app.create_app()

routes = {
    str(rule): rule.endpoint
    for rule in app.url_map.iter_rules()
}

assert routes.get("/") == "command_center_home.home", routes.get("/")
assert routes.get("/legacy-dashboard") == "dashboard.dashboard"
assert routes.get("/command-center") == "command_center.page"

print("Root route: PASS")
print("Legacy dashboard route: PASS")
print("Command Center route: PASS")
PY

echo
echo "v5.3.1 default Command Center applied."
echo "Run the production gate before committing."
