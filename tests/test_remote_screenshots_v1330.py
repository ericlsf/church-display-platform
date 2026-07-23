from pathlib import Path


def test_screenshot_blueprint_registered():
    source = Path("hub/app.py").read_text(encoding="utf-8")
    assert "from routes.screenshots import screenshots_bp" in source
    assert "register_blueprint(screenshots_bp)" in source


def test_display_details_has_screenshot_workspace():
    template = Path("hub/templates/display_details.html").read_text(encoding="utf-8")
    assert "data-screenshot-workspace" in template
    assert "data-screenshot-request" in template
    assert "display-screenshots-v1330.js" in template
    assert "display-screenshots-v1330.css" in template


def test_screenshot_api_supports_status_and_capture_request():
    source = Path("hub/routes/screenshots.py").read_text(encoding="utf-8")
    assert 'methods=["GET"]' in source
    assert 'methods=["POST"]' in source
    assert 'create_job(display_id, "upload_preview", {})' in source


def test_preview_metadata_includes_freshness():
    source = Path("hub/services/fleet_state.py").read_text(encoding="utf-8")
    assert "preview_updated_at" in source
    assert "preview_age_seconds" in source
    assert "preview_available" in source
