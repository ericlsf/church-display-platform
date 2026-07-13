import io
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DISPLAY_ROOT = ROOT / "display"

EXCLUDED_PARTS = {
    "venv",
    "__pycache__",
    "media",
    "status",
    "logs",
    "backups",
}

EXCLUDED_NAMES = {
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


def should_include(path):
    relative = path.relative_to(DISPLAY_ROOT)

    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if path.suffix in {".pyc", ".pyo"}:
        return False

    return True


def build_display_package():
    if not DISPLAY_ROOT.exists():
        raise FileNotFoundError(f"Display source not found: {DISPLAY_ROOT}")

    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path in sorted(DISPLAY_ROOT.rglob("*")):
            if not path.is_file() or not should_include(path):
                continue

            relative = path.relative_to(DISPLAY_ROOT)
            archive_name = Path("church-display") / relative
            info = archive.gettarinfo(str(path), arcname=str(archive_name))

            if relative.parts and relative.parts[0] in {"scripts", "installer"}:
                info.mode |= 0o111
            if path.name == "install.sh":
                info.mode |= 0o111

            with path.open("rb") as handle:
                archive.addfile(info, handle)

        version_data = (current_version() + "\n").encode("utf-8")
        version_info = tarfile.TarInfo("church-display/VERSION")
        version_info.size = len(version_data)
        version_info.mode = 0o644
        archive.addfile(version_info, io.BytesIO(version_data))

    buffer.seek(0)
    return buffer
