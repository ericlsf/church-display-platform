import io
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DISPLAY_ROOT = ROOT / "display"

EXCLUDED_DIRS = {
    "venv",
    "__pycache__",
    "media",
    "status",
    "logs",
    "backups",
}

EXCLUDED_FILES = {
    "church-display.log",
    "config.json",
    "config.json.bak",
}


def current_version():
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def include_file(path):
    relative = path.relative_to(DISPLAY_ROOT)

    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False

    if path.name in EXCLUDED_FILES:
        return False

    if path.suffix in {".pyc", ".pyo"}:
        return False

    return True


def build_display_package():
    if not (DISPLAY_ROOT / "install.sh").exists():
        raise FileNotFoundError("display/install.sh is missing")

    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path in sorted(DISPLAY_ROOT.rglob("*")):
            if not path.is_file() or not include_file(path):
                continue

            relative = path.relative_to(DISPLAY_ROOT)
            info = archive.gettarinfo(
                str(path),
                arcname=str(Path("display") / relative),
            )

            if path.suffix == ".sh" or path.name == "install.sh":
                info.mode |= 0o111

            with path.open("rb") as source:
                archive.addfile(info, source)

        version = (current_version() + "\n").encode("utf-8")
        info = tarfile.TarInfo("display/VERSION")
        info.size = len(version)
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(version))

    buffer.seek(0)
    return buffer
