from pathlib import Path


def test_activity_combines_jobs_history_and_upcoming_work():
    jobs = Path("hub/templates/jobs.html").read_text(encoding="utf-8")
    history = Path("hub/templates/history.html").read_text(encoding="utf-8")
    schedules = Path("hub/templates/schedules.html").read_text(encoding="utf-8")
    for template in (jobs, history, schedules):
        assert '<p class="eyebrow">ACTIVITY</p>' in template
        assert "Jobs &amp; Work" in template
        assert "Events &amp; Health" in template
        assert "Upcoming Work" in template


def test_display_context_owns_groups_presets_and_bulk_actions():
    displays = Path("hub/templates/displays.html").read_text(encoding="utf-8")
    groups = Path("hub/templates/groups.html").read_text(encoding="utf-8")
    profiles = Path("hub/templates/display_profiles.html").read_text(encoding="utf-8")
    assert "Manage groups" in displays
    assert "Display presets" in displays
    assert "Apply preset" in displays
    assert "Back to Displays" in groups
    assert "Display Presets" in profiles


def test_home_replaces_the_duplicate_operator_cockpit():
    home = Path("hub/templates/fleet_dashboard.html").read_text(encoding="utf-8")
    command_route = Path("hub/routes/command_center.py").read_text(encoding="utf-8")
    cockpit_route = Path("hub/routes/fleet_command_center.py").read_text(encoding="utf-8")
    assert "<h1>Home</h1>" in home
    assert 'redirect(url_for("fleet_dashboard.page"), code=302)' in command_route
    assert 'redirect(url_for("fleet_dashboard.page"), code=302)' in cockpit_route


def test_legacy_operations_pages_redirect_without_removing_action_routes():
    fleet = Path("hub/routes/fleet_operations.py").read_text(encoding="utf-8")
    bulk = Path("hub/routes/bulk_operations.py").read_text(encoding="utf-8")
    fleet_map = Path("hub/routes/fleet_map.py").read_text(encoding="utf-8")
    assert 'redirect(url_for("displays.page"), code=302)' in fleet
    assert 'redirect(url_for("displays.page"), code=302)' in bulk
    assert 'redirect(url_for("displays.page"), code=302)' in fleet_map
    assert '@fleet_operations_bp.route("/bulk", methods=["POST"])' in fleet
    assert '@bulk_operations_bp.route("/run", methods=["POST"])' in bulk
