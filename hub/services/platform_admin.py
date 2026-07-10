import io
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

from services.config import APP_DIR, CONFIG_DIR, LOG_DIR, load_hub_settings, save_json

ROOT_DIR = APP_DIR.parent
DATA_DIR = APP_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
SUPPORT_DIR = DATA_DIR / "support"
SETUP_MARKER = CONFIG_DIR / ".setup-complete"

for path in (DATA_DIR, BACKUP_DIR, SUPPORT_DIR):
    path.mkdir(parents=True, exist_ok=True)


def command_output(command, timeout=15):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return {
            "command": " ".join(command),
            "returncode": result.returncode,
            "stdout": result.stdout[-10000:],
            "stderr": result.stderr[-10000:],
        }
    except Exception as exc:
        return {"command": " ".join(command), "returncode": -1, "stdout": "", "stderr": str(exc)}


def setup_complete():
    return SETUP_MARKER.exists()


def mark_setup_complete():
    SETUP_MARKER.write_text(datetime.now().isoformat(timespec="seconds") + "\n")


def save_hub_settings(settings):
    current = load_hub_settings()
    current.update(settings)
    save_json(CONFIG_DIR / "hub.json", current)
    return current


def create_backup(include_media=False):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"church-display-backup-{stamp}.tar.gz"

    include_paths = [
        APP_DIR / "config",
        APP_DIR / "data",
        APP_DIR / "content" / "playlists",
        APP_DIR / "content" / "revisions",
        APP_DIR / "content" / "manifests",
    ]
    if include_media:
        include_paths.append(APP_DIR / "content" / "cache")

    with tarfile.open(target, "w:gz") as archive:
        for path in include_paths:
            if path.exists():
                archive.add(path, arcname=str(path.relative_to(ROOT_DIR)))

    return target


def restore_backup(archive_path):
    archive_path = Path(archive_path).resolve()
    if not archive_path.exists() or archive_path.parent != BACKUP_DIR.resolve():
        raise ValueError("Invalid backup path")

    with tarfile.open(archive_path, "r:gz") as archive:
        root = ROOT_DIR.resolve()
        for member in archive.getmembers():
            destination = (root / member.name).resolve()
            if root not in destination.parents and destination != root:
                raise ValueError("Unsafe backup archive")
        archive.extractall(ROOT_DIR)


def list_backups():
    rows = []
    for path in sorted(BACKUP_DIR.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True):
        rows.append({
            "name": path.name,
            "size": path.stat().st_size,
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
        })
    return rows


def build_support_bundle():
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = SUPPORT_DIR / f"church-display-support-{stamp}.tar.gz"
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "git": command_output(["git", "describe", "--tags", "--always", "--dirty"]),
        "git_status": command_output(["git", "status", "--short"]),
        "rclone": command_output(["rclone", "version"]),
        "hub_service": command_output(["systemctl", "status", "church-display-hub.service", "--no-pager"]),
        "agent_service": command_output(["systemctl", "status", "church-display-agent.service", "--no-pager"]),
        "disk": command_output(["df", "-h", str(ROOT_DIR)]),
        "memory": command_output(["free", "-h"]),
    }

    report_path = SUPPORT_DIR / "support-report.json"
    report_path.write_text(json.dumps(report, indent=2))

    with tarfile.open(target, "w:gz") as archive:
        archive.add(report_path, arcname="support-report.json")
        for path in [LOG_DIR, CONFIG_DIR, APP_DIR / "content" / "manifests"]:
            if path.exists():
                archive.add(path, arcname=str(path.relative_to(APP_DIR)))

    report_path.unlink(missing_ok=True)
    return target


def platform_status():
    settings = load_hub_settings()
    return {
        "setup_complete": setup_complete(),
        "settings": settings,
        "git": command_output(["git", "describe", "--tags", "--always", "--dirty"]),
        "hub_service": command_output(["systemctl", "is-active", "church-display-hub.service"]),
        "agent_service": command_output(["systemctl", "is-active", "church-display-agent.service"]),
        "rclone": command_output(["rclone", "listremotes"]),
        "disk": command_output(["df", "-h", str(ROOT_DIR)]),
    }
