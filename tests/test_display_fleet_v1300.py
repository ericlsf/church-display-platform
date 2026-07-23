from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v13_fleet_health_assets_are_wired():
    template = (ROOT / "hub/templates/displays.html").read_text()
    route = (ROOT / "hub/routes/displays.py").read_text()
    script = (ROOT / "hub/static/display-fleet-v1300.js").read_text()
    style = (ROOT / "hub/static/display-fleet-v1300.css").read_text()

    assert "display-fleet-v1300.css?v=13.0.0" in template
    assert "display-fleet-v1300.js?v=13.0.0" in template
    for marker in (
        "data-attention-count",
        "data-active-jobs",
        "data-app-health",
        "data-media-count",
        "data-inspector-job",
    ):
        assert marker in template

    for field in (
        '"display_app_running"',
        '"update_available"',
        '"cpu_temp"',
        '"disk_usage"',
        '"job"',
        '"attention"',
        '"active_jobs"',
    ):
        assert field in route

    assert "data-inspector-job-progress" in script
    assert "data-attention-count" in script
    assert ".fleet-health-strip" in style
    assert ".system-metrics" in style



def test_job_summary_tracks_active_and_unacknowledged_failures():
    route = (ROOT / "hub/routes/displays.py").read_text()
    start = route.index("def _display_job_summary")
    end = route.index("def _system_value", start)
    block = route[start:end]
    assert 'status") in {"queued", "running"}' in block
    assert 'status") in {"failed", "timed_out"}' in block
    assert 'not job.get("acknowledged")' in block
    assert '"active_count": len(active)' in block
    assert '"failed_count": len(failed)' in block
