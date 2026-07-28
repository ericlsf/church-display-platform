"""Resolve display-player releases independently from Hub-only tags."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HUB_VERSION_FILE = ROOT / "hub" / "VERSION"
DISPLAY_VERSION_FILE = ROOT / "display" / "VERSION"


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


def _git_ok(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.returncode == 0


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


def _version(path):
    try:
        return path.read_text(encoding="utf-8").strip().lstrip("v")
    except OSError:
        return ""


def release_readiness():
    """Describe whether this checkout can produce a coherent fleet release."""
    hub_version = _version(HUB_VERSION_FILE)
    display_version = _version(DISPLAY_VERSION_FILE)
    expected_tag = f"v{hub_version}" if hub_version else ""
    head_tag = _git("describe", "--tags", "--exact-match", "HEAD")
    expected_tag_reachable = bool(
        expected_tag and _git_ok("merge-base", "--is-ancestor", expected_tag, "HEAD")
    )
    latest_tag = latest_display_tag()
    issues = []

    if not hub_version or not display_version:
        issues.append("Hub and display version markers must both be present.")
    elif hub_version != display_version:
        issues.append(
            f"Hub v{hub_version} and display v{display_version} are not aligned."
        )
    if expected_tag and not expected_tag_reachable:
        issues.append(f"Current branch does not contain tag {expected_tag}.")
    if expected_tag and latest_tag and latest_tag != expected_tag:
        issues.append(
            f"Latest deployable display release is {latest_tag}, not {expected_tag}."
        )

    return {
        "ready": not issues,
        "hub_version": f"v{hub_version}" if hub_version else "Unknown",
        "display_version": f"v{display_version}" if display_version else "Unknown",
        "expected_tag": expected_tag or "Unknown",
        "head_tag": head_tag or "Untagged",
        "expected_tag_reachable": expected_tag_reachable,
        "latest_display_tag": latest_tag or "Unknown",
        "issues": issues,
    }
