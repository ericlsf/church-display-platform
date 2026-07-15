#!/usr/bin/env python3
"""Verify Hub backup and restore using stable snapshots of live state."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tarfile
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

CANDIDATES = [
    ROOT / "hub" / "config",
    ROOT / "hub" / "data",
    ROOT / "hub" / "logs" / "audit.jsonl",
]

SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def source_files():
    files = []
    for candidate in CANDIDATES:
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                path
                for path in candidate.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and not path.name.endswith(".tmp")
                and not path.name.endswith("-wal")
                and not path.name.endswith("-shm")
            )
    return sorted(set(files))


def snapshot_sqlite(source: Path, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)

    source_connection = sqlite3.connect(
        f"file:{source}?mode=ro",
        uri=True,
        timeout=30,
    )
    destination_connection = sqlite3.connect(destination)

    try:
        source_connection.backup(destination_connection)
    finally:
        destination_connection.close()
        source_connection.close()


def snapshot_file(source: Path, destination: Path):
    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.suffix.lower() in SQLITE_SUFFIXES:
        snapshot_sqlite(source, destination)
        return

    # Copy a stable point-in-time version. The original file may continue to
    # change after this copy, which is expected for logs and active state.
    with source.open("rb") as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)


def safe_extract(archive: Path, destination: Path):
    destination = destination.resolve()

    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            if destination not in target.parents and target != destination:
                raise RuntimeError(
                    "Unsafe path detected in backup archive"
                )

        # Explicit filter removes the Python 3.14 deprecation warning and
        # applies safer extraction semantics on supported Python versions.
        try:
            tar.extractall(destination, filter="data")
        except TypeError:
            tar.extractall(destination)


def main() -> int:
    files = source_files()

    if not files:
        raise RuntimeError("No Hub state files found to back up")

    with tempfile.TemporaryDirectory(
        prefix="church-display-backup-test-"
    ) as temp_name:
        temp = Path(temp_name)
        snapshot_root = temp / "snapshot"
        restore_root = temp / "restore"
        archive = temp / "hub-state.tar.gz"

        snapshot_root.mkdir()
        restore_root.mkdir()

        snapshot_hashes = {}

        for source in files:
            relative = source.relative_to(ROOT)
            snapshot = snapshot_root / relative
            snapshot_file(source, snapshot)
            snapshot_hashes[str(relative)] = sha256(snapshot)

        with tarfile.open(archive, "w:gz") as tar:
            for relative in sorted(snapshot_hashes):
                source = snapshot_root / relative
                tar.add(
                    source,
                    arcname=relative,
                    recursive=False,
                )

        safe_extract(archive, restore_root)

        restored_hashes = {}
        for relative in snapshot_hashes:
            restored = restore_root / relative
            if not restored.is_file():
                raise RuntimeError(
                    f"Missing restored file: {relative}"
                )
            restored_hashes[relative] = sha256(restored)

        mismatches = {
            relative: {
                "snapshot": snapshot_hashes[relative],
                "restored": restored_hashes.get(relative),
            }
            for relative in snapshot_hashes
            if snapshot_hashes[relative]
            != restored_hashes.get(relative)
        }

        if mismatches:
            print(json.dumps(mismatches, indent=2))
            raise RuntimeError(
                f"Backup verification failed for "
                f"{len(mismatches)} file(s)"
            )

        print(
            f"Backup verification passed: "
            f"{len(snapshot_hashes)} file(s), "
            f"{archive.stat().st_size} bytes"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
