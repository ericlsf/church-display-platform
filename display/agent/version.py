"""Authoritative installed-version helpers for the display agent."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

DISPLAY_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = DISPLAY_ROOT / "VERSION"
RELEASE_FILE = DISPLAY_ROOT / "release.json"

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""

def installed_version() -> str:
    value = _read_text(VERSION_FILE)
    if value:
        return value
    try:
        data = json.loads(_read_text(RELEASE_FILE) or "{}")
    except Exception:
        data = {}
    value = str(data.get("version") or data.get("tag") or "").strip()
    return value or "unknown"

def git_metadata() -> dict:
    result = {
        "branch": "Unknown",
        "commit": "Unknown",
        "tag": "untagged",
        "describe": "Unknown",
        "dirty": "Unknown",
    }
    if not (DISPLAY_ROOT / ".git").exists():
        return result
    commands = {
        "branch": ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        "commit": ["git", "rev-parse", "--short", "HEAD"],
        "tag": ["git", "describe", "--tags", "--exact-match"],
        "describe": ["git", "describe", "--tags", "--always", "--dirty"],
    }
    for key, command in commands.items():
        try:
            completed = subprocess.run(
                command,
                cwd=DISPLAY_ROOT,
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if completed.returncode == 0:
                result[key] = completed.stdout.strip() or result[key]
        except Exception:
            pass
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=DISPLAY_ROOT,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if completed.returncode == 0:
            result["dirty"] = "yes" if completed.stdout.strip() else "no"
    except Exception:
        pass
    return result

def version_info() -> dict:
    version = installed_version()
    git = git_metadata()
    return {
        "version": version,
        "tag": version,
        "branch": git.get("branch", "Unknown"),
        "commit": git.get("commit", "Unknown"),
        "describe": git.get("describe", "Unknown"),
        "dirty": git.get("dirty", "Unknown"),
        "git": git,
    }

def get_version_info() -> dict:
    return version_info()

def get_version() -> str:
    return installed_version()

def current_version() -> str:
    return installed_version()

VERSION = installed_version()
__version__ = VERSION
