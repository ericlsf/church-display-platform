#!/usr/bin/env python3
import subprocess
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
        return result.stdout.strip()
    except Exception:
        return default


def previous_tag(current_version):
    tags = run_git(["tag", "--sort=-creatordate"], "")
    seen_current = False
    for tag in tags.splitlines():
        tag = tag.strip()
        if not tag:
            continue
        if tag == current_version:
            seen_current = True
            continue
        if seen_current:
            return tag
    # Fallback: most recent tag that is not current.
    for tag in tags.splitlines():
        tag = tag.strip()
        if tag and tag != current_version:
            return tag
    return ""


def commit_subjects(since_tag=""):
    args = ["log", "--pretty=format:%s"]
    if since_tag:
        args.insert(1, f"{since_tag}..HEAD")
    output = run_git(args, "")
    return [line.strip() for line in output.splitlines() if line.strip()]


def categorize(subjects):
    groups = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Other": [],
    }

    for subject in subjects:
        lower = subject.lower()
        if lower.startswith(("add ", "added ", "create ", "introduce ")):
            groups["Added"].append(subject)
        elif lower.startswith(("fix ", "fixed ", "resolve ", "repair ")):
            groups["Fixed"].append(subject)
        elif lower.startswith(("change ", "changed ", "update ", "improve ", "refactor ")):
            groups["Changed"].append(subject)
        else:
            groups["Other"].append(subject)

    return groups


def render_release_notes(version, manifest):
    prev = previous_tag(version)
    subjects = commit_subjects(prev)
    groups = categorize(subjects)

    lines = [
        f"# Church Display Platform {version}",
        "",
        f"Built: {manifest.get('built_at', '')}",
        f"Commit: {manifest.get('commit_short', '')}",
        f"Describe: {manifest.get('describe', '')}",
        "",
    ]

    if prev:
        lines += [f"Changes since `{prev}`:", ""]
    else:
        lines += ["Changes in this release:", ""]

    any_items = False
    for heading in ["Added", "Changed", "Fixed", "Other"]:
        items = groups.get(heading, [])
        if not items:
            continue
        any_items = True
        lines += [f"## {heading}", ""]
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    if not any_items:
        lines += ["- Release package generated from the current repository state.", ""]

    lines += [
        "## Verification", "",
        "This release includes:", "",
        "- `manifest.json`", 
        "- `SHA256SUMS`", 
        "- source package ZIP", 
        "- generated release notes", 
        "",
    ]

    return "\n".join(lines)
