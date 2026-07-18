from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "hub/templates/displays.html").read_text()
ROUTE = (ROOT / "hub/routes/displays.py").read_text()
CSS = (ROOT / "hub/static/display-fleet-v1110.css").read_text()
JS = (ROOT / "hub/static/display-fleet-v1110.js").read_text()

assert 'class="source-badge">Google Drive<' in TEMPLATE
assert 'name="sync_remote"' not in TEMPLATE
assert 'remote = "gdrive"' in ROUTE
assert 'display["sync_remote"] = "gdrive"' in ROUTE
assert '<select name="sync_folder" required>' in TEMPLATE
assert '<select name="profile_id">' in TEMPLATE
assert 'datalist' not in TEMPLATE
assert 'class="display-card-main"' in TEMPLATE
assert 'class="advanced-menu"' in TEMPLATE
assert '.display-card-main{display:grid' in CSS
assert '.advanced-panel{position:absolute' in CSS
assert 'action="/displays/bulk-workspace"' in TEMPLATE
assert 'data-display-select' in TEMPLATE
assert '@displays_bp.route("/bulk-workspace", methods=["POST"])' in ROUTE
assert 'name = \'display_ids\'' in JS
print("v11.1.0 display fleet tests passed")
