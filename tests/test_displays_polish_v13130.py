from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_displays_workspace_has_compact_actions_and_selection():
    template = (ROOT / "hub/templates/displays.html").read_text(encoding="utf-8")

    assert "{{ hub_version }}" in template
    assert "fleet-card-selection-control" in template
    assert "card-update-button" in template
    assert "Take screenshot" in template
    assert "fleet-menu-divider" in template
    assert "fleet-activity-strip" in template
    assert 'id="activity-list"' not in template
    assert "data-fleet-toast" in template


def test_displays_polish_aligns_controls_and_preserves_controller_role():
    template = (ROOT / "hub/templates/displays.html").read_text(encoding="utf-8")
    style = (ROOT / "hub/static/style.css").read_text(encoding="utf-8")
    live_script = (ROOT / "hub/static/display-fleet-v1300.js").read_text(
        encoding="utf-8"
    )

    assert 'data-device-role="{{ row.device_role }}"' in template
    assert 'card.dataset.deviceRole !== "controller"' in template
    assert "card.dataset.deviceRole !== 'controller'" in live_script
    assert ".fleet-summary-copy" in style
    assert ".fleet-card-topline" in style
    assert ".fleet-more-actions>div .fleet-menu-danger" in style
    assert ":focus-visible" in style
