import shutil
from pathlib import Path

from services.config import CONFIG_DIR, LOG_DIR
from services.database import initialize_database


def run_startup_checks():
    problems = []
    for path in (CONFIG_DIR, LOG_DIR):
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            probe = Path(path) / ".write-test"
            probe.write_text("ok")
            probe.unlink()
        except Exception as exc:
            problems.append(f"Not writable: {path}: {exc}")

    if not shutil.which("rclone"):
        problems.append("rclone is not installed or not in PATH")

    try:
        initialize_database()
    except Exception as exc:
        problems.append(f"SQLite initialization failed: {exc}")

    return problems
