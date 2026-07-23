"""Resolve display-player releases independently from Hub-only tags."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def list_display_release_tags(limit=30):
    """Return tags where the deployable display tree actually changed."""
    raw_tags = _git("tag", "--sort=v:refname")
    releases = []
    previous_tree = ""

    for tag in [line.strip() for line in raw_tags.splitlines() if line.strip()]:
        tree = _git("rev-parse", f"{tag}:display")
        if not tree or tree == previous_tree:
            continue
        previous_tree = tree
        releases.append(tag)

    releases.reverse()
    return releases[:limit]


def latest_display_tag():
    tags = list_display_release_tags(limit=1)
    return tags[0] if tags else ""
