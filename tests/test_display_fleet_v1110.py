from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "hub/templates/displays.html").read_text()
ROUTE = (ROOT / "hub/routes/displays.py").read_text()

assert 'class="source-badge">Google Drive<' in TEMPLATE
assert 'name="sync_remote"' not in TEMPLATE
assert 'remote = "gdrive"' in ROUTE
assert 'display["sync_remote"] = "gdrive"' in ROUTE
assert '<select name="sync_folder" required>' in TEMPLATE
assert '<select name="profile_id">' in TEMPLATE
assert 'datalist' not in TEMPLATE
assert 'display-preview' in TEMPLATE
assert ('class="advanced-menu"' in TEMPLATE or 'class="inspector-section advanced-section"' in TEMPLATE)
assert 'action="/displays/bulk-workspace"' in TEMPLATE
assert 'data-display-select' in TEMPLATE
assert '@displays_bp.route("/bulk-workspace", methods=["POST"])' in ROUTE
print("v11.1.0 display fleet compatibility tests passed")
