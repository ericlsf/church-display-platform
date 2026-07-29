from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_release_versions_match_v13210():
    assert text("hub/VERSION").strip() == "v13.21.0"
    assert text("display/VERSION").strip().lstrip("v") == "13.21.0"


def test_display_version_comes_from_installed_version_file():
    config = text("display/agent/config.py")
    assert 'APP_DIR / "VERSION"' in config
    assert '"1.2.3"' not in config


def test_update_waits_for_restarted_agent_checkin():
    update = text("display/agent/jobs/update.py")
    agent = text("display/agent/agent.py")
    assert "update_state.awaiting_checkin()" in update
    assert 'recover.py' in update
    assert '--watch' in update
    assert 'report(\n                "running",\n                95,' in update
    assert "finalize_after_heartbeat(installed_version())" in agent


def test_release_contains_recovery_runtime_and_units():
    release = text("hub/services/display_releases.py")
    installer = text("display/install.sh")
    assert '"recovery"' in release
    assert '"systemd"' in release
    assert "church-display-recovery.timer" in installer
    assert "enable --now church-display-recovery.timer" in installer
    assert (ROOT / "display/recovery/recover.py").is_file()
    assert (ROOT / "display/systemd/church-display-recovery.service").is_file()


def test_remote_terminal_normalizes_windows_line_endings():
    terminal = text("hub/services/remote_terminal.py")
    assert '.replace("\\r\\n", "\\n").replace("\\r", "\\n")' in terminal