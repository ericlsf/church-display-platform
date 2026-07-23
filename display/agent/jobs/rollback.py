from __future__ import annotations
import json, shutil, subprocess, time
from pathlib import Path
from agent.config import APP_DIR
from agent.install_version import record_installed_release
from agent.utils import run_command

BACKUP_DIR = APP_DIR.parent / "backups" / "last-good-display"
PRESERVE = {"venv","media","status","logs","config","backups"}

def _backup_version():
    version = BACKUP_DIR / "VERSION"
    if version.exists():
        value = version.read_text(encoding="utf-8").strip()
        if value:
            return value
    metadata = BACKUP_DIR / "release.json"
    if metadata.exists():
        try:
            data = json.loads(metadata.read_text(encoding="utf-8"))
            return str(data.get("version") or data.get("tag") or "unknown")
        except Exception:
            pass
    return "unknown"

def handle_rollback_update(job, report):
    try:
        if not BACKUP_DIR.exists():
            raise RuntimeError("No last-known-good backup is available")
        report("running", 20, "Restoring last-known-good display files")
        for child in APP_DIR.iterdir():
            if child.name in PRESERVE:
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
        for source in BACKUP_DIR.iterdir():
            if source.name in PRESERVE:
                continue
            target = APP_DIR / source.name
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            else:
                shutil.copy2(source, target)

        version = _backup_version()
        record_installed_release(
            APP_DIR,
            version,
            commit="rollback",
            package_url="local:last-good-display",
        )

        report("running", 70, "Restarting display application")
        code, stdout, stderr = run_command(
            ["sudo","systemctl","restart","church-display.service"],
            timeout=45,
        )
        if code != 0:
            raise RuntimeError((stderr or stdout or "Restart failed")[-500:])
        time.sleep(6)
        code, stdout, stderr = run_command(
            ["systemctl","is-active","church-display.service"],
            timeout=15,
        )
        if code != 0 or stdout.strip() != "active":
            raise RuntimeError("Display service did not become active")

        report("success", 100, f"Rollback completed; restored {version}")
        subprocess.Popen(
            ["sudo","systemctl","restart","church-display-agent.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        report("failed", 100, f"Rollback failed: {exc}")
