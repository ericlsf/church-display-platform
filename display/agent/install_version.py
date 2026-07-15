"""Write authoritative release metadata after a successful deployment."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=str(path.parent),
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def record_installed_release(
    display_root: Path,
    version: str,
    *,
    sha256: str = "",
    commit: str = "",
    package_url: str = "",
) -> dict:
    version = str(version or "").strip()

    if not version:
        raise ValueError("Installed version cannot be empty")

    metadata = {
        "version": version,
        "sha256": str(sha256 or ""),
        "commit": str(commit or ""),
        "package_url": str(package_url or ""),
        "installed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    _atomic_write(
        display_root / "VERSION",
        version + "\n",
    )

    _atomic_write(
        display_root / "release.json",
        json.dumps(metadata, indent=2) + "\n",
    )

    return metadata
