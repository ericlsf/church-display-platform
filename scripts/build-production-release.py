#!/usr/bin/env python3
"""Build a source release only after all production checks pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

EXCLUDES = {
    ".git",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "venv",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tmp",
}


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
    )


def include(path: Path) -> bool:
    relative = path.relative_to(ROOT)

    if any(part in EXCLUDES for part in relative.parts):
        return False

    if path.suffix in EXCLUDE_SUFFIXES:
        return False

    return True


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def dirty_files() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        line
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
    )
    args = parser.parse_args()

    if not args.version.startswith("v"):
        raise SystemExit("Version must start with `v`")

    dirty = dirty_files()
    if dirty and not args.allow_dirty:
        print("Refusing to package a dirty working tree:")
        for line in dirty:
            print(line)
        return 1

    python = str(
        ROOT / "hub" / "venv" / "bin" / "python"
    )

    run([
        python,
        "-m",
        "compileall",
        "-q",
        "hub",
        "display/app",
        "display/agent",
        "display/scripts",
    ])
    run([python, "scripts/validate-runtime-imports.py"])
    run([python, "scripts/smoke-test-hub.py"])
    run([python, "scripts/verify-backup-restore.py"])
    run([
        python,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v",
    ])

    DIST.mkdir(exist_ok=True)
    archive = DIST / (
        f"church-display-platform-{args.version}.tar.gz"
    )
    manifest = DIST / (
        f"church-display-platform-{args.version}.json"
    )

    with tempfile.TemporaryDirectory(
        prefix="church-display-release-"
    ) as temp_name:
        staging = Path(temp_name) / (
            f"church-display-platform-{args.version}"
        )
        staging.mkdir(parents=True)

        for path in ROOT.rglob("*"):
            if not path.is_file() or not include(path):
                continue

            target = staging / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())

        with tarfile.open(archive, "w:gz") as tar:
            tar.add(
                staging,
                arcname=staging.name,
            )

    metadata = {
        "version": args.version,
        "commit": git_commit(),
        "archive": archive.name,
        "sha256": sha256(archive),
        "size_bytes": archive.stat().st_size,
        "working_tree_dirty": bool(dirty),
    }

    manifest.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print()
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
