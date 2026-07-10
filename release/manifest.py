#!/usr/bin/env python3
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run_git(args, default=""):
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            return default
        return result.stdout.strip() or default
    except Exception:
        return default


def current_commit():
    return run_git(["rev-parse", "HEAD"], "unknown")


def current_short_commit():
    commit = current_commit()
    if commit == "unknown":
        return "unknown"
    return commit[:8]


def current_branch():
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"], "unknown")


def current_tag(default="untagged"):
    exact = run_git(["describe", "--tags", "--exact-match"], "")
    if exact:
        return exact
    return run_git(["describe", "--tags", "--abbrev=0"], default)


def describe():
    return run_git(["describe", "--tags", "--always", "--dirty"], current_short_commit())


def is_dirty():
    return bool(run_git(["status", "--porcelain"], ""))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(version, package_name=None, package_sha256=None, package_size=None):
    return {
        "name": "church-display-platform",
        "version": version,
        "commit": current_commit(),
        "commit_short": current_short_commit(),
        "branch": current_branch(),
        "describe": describe(),
        "dirty": is_dirty(),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "minimum_hub": "1.7.0",
        "minimum_display": "1.7.0",
        "package": {
            "file": package_name or "",
            "sha256": package_sha256 or "",
            "size_bytes": package_size or 0,
        },
    }


def write_manifest(path, manifest):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n")
