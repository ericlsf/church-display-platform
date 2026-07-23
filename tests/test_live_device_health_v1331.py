from pathlib import Path


def test_details_service_flattens_nested_system_metrics():
    source = Path("hub/services/display_details.py").read_text(encoding="utf-8")
    assert "def _live_health_view" in source
    assert '"cpu_temperature": _system_value(system, "cpu_temp", "temperature")' in source
    assert '"memory_percent": _system_value(system, "memory_usage", "memory_percent"' in source
    assert '"storage_percent": _system_value(system, "disk_usage", "disk_percent"' in source


def test_live_health_uses_normalized_displays_endpoint():
    source = Path("hub/static/live-display-health-v1331.js").read_text(encoding="utf-8")
    assert 'fetch("/displays/api/status"' in source
    assert "/api/v1/fleet-state" in source  # regression explanation remains documented
    assert "data-live-memory" in source
    assert "data-live-ip" in source


def test_displays_status_api_exposes_details_metrics():
    source = Path("hub/routes/displays.py").read_text(encoding="utf-8")
    for field in ("ip_address", "uptime", "hostname", "readiness", "player_state"):
        assert f'"{field}"' in source


def test_display_details_has_polished_health_workspace():
    template = Path("hub/templates/display_details.html").read_text(encoding="utf-8")
    assert "display-health-v1331.css" in template
    assert "live-display-health-v1331.js" in template
    assert "health-metric-strip" in template
    assert "data-live-memory" in template
    assert "Connection Details" in template
    assert "Collect Logs" in template
