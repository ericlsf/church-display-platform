#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
BACKUP = APP_DIR.parent / "backups" / "last-good-display"
STATE = APP_DIR / "status" / "display_update.json"
SOURCE_NAMES = {"app", "agent", "scripts", "recovery", "systemd", "requirements.txt", "install.sh", "VERSION", "RELEASE"}
TIMEOUT_SECONDS = 240


def _load_state():
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        updated = datetime.fromisoformat(state.get("updated_at"))
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        return None, None
    return state, updated


def main(watch=False):
    while True:
        state, updated = _load_state()
        if state is None or state.get("phase") != "awaiting_checkin":
            return 0
        age = (datetime.now(timezone.utc) - updated).total_seconds()
        if age >= TIMEOUT_SECONDS:
            break
        if not watch:
            return 0
        time.sleep(min(10, max(1, TIMEOUT_SECONDS - age)))

    if not BACKUP.exists():
        return 1
    for name in SOURCE_NAMES:
        source, target = BACKUP / name, APP_DIR / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        if source.is_dir():
            shutil.copytree(source, target)
        elif source.exists():
            shutil.copy2(source, target)
    state.update({
        "phase": "recovered",
        "message": "Agent check-in timed out; last-known-good software restored",
        "recovered_at": datetime.now(timezone.utc).isoformat(),
    })
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    prefix = [] if hasattr(os, "geteuid") and os.geteuid() == 0 else ["sudo", "-n"]
    subprocess.run(prefix + ["systemctl", "restart", "church-display.service"], check=False)
    subprocess.run(prefix + ["systemctl", "restart", "church-display-agent.service"], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(watch="--watch" in sys.argv[1:]))