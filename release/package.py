#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


EXCLUDE_DIRS = {
    ".git", ".pytest_cache", "__pycache__", "venv", ".venv",
    "media", "logs", "status", "backups", "dist",
}

EXCLUDE_SUFFIXES = {
    ".pyc", ".pyo", ".log", ".tmp",
}

EXCLUDE_PATH_PARTS = {
    "hub/config/jobs.json",
    "hub/config/events.log",
    "hub/static/previews",
    "display/status",
    "display/logs",
    "display/media",
    "release/dist",
}


def should_exclude(path):
    rel = path.relative_to(ROOT).as_posix()
    parts = set(path.relative_to(ROOT).parts)

    if parts & EXCLUDE_DIRS:
        return True

    if path.suffix in EXCLUDE_SUFFIXES:
        return True

    for part in EXCLUDE_PATH_PARTS:
        if rel == part or rel.startswith(part + "/"):
            return True

    return False


def add_file(zf, path, arcname):
    info = zipfile.ZipInfo.from_file(path, arcname)
    if path.suffix in {".sh", ".py"} and os.access(path, os.X_OK):
        info.external_attr = 0o755 << 16
    with open(path, "rb") as f:
        zf.writestr(info, f.read(), compress_type=zipfile.ZIP_DEFLATED)


def build_source_zip(output_path, extra_files=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            if path.resolve() == output_path.resolve():
                continue
            if should_exclude(path):
                continue
            arcname = Path("church-display-platform") / path.relative_to(ROOT)
            add_file(zf, path, arcname.as_posix())

        for arcname, content in (extra_files or {}).items():
            zf.writestr(str(Path("church-display-platform") / arcname), content)

    return output_path
