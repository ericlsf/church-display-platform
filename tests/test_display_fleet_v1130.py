from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_live_fleet_assets_and_api_are_wired():
    template = (ROOT / 'hub/templates/displays.html').read_text()
    route = (ROOT / 'hub/routes/displays.py').read_text()
    script = (ROOT / 'hub/static/display-fleet-v1130.js').read_text()
    style = (ROOT / 'hub/static/display-fleet-v1130.css').read_text()
    assert 'display-fleet-v1130.css?v=11.3.0' in template
    assert 'display-fleet-v1130.js?v=11.3.0' in template
    assert 'data-display-id="{{ row.id }}"' in template
    assert 'data-live-state' in template
    assert '@displays_bp.route("/api/status")' in route
    assert 'jsonify({' in route
    assert "fetch('/displays/api/status'" in script
    assert 'window.setInterval(refreshFleet, 15000)' in script
    assert '.live-refresh-state' in style

def test_live_api_does_not_query_drive():
    route = (ROOT / 'hub/routes/displays.py').read_text()
    start = route.index('def display_status_api')
    end = route.index('@displays_bp.route("/add"', start)
    block = route[start:end]
    assert 'cached_drive_folders' not in block
    assert 'rclone' not in block
