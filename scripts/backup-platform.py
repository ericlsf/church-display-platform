#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hub"))

from services.platform_admin import create_backup, prune_backups
from services.resilience import load_resilience


def main():
    settings = load_resilience().get("backups", {})
    if not settings.get("enabled", True):
        print("Bi-weekly backups are disabled.")
        return 0
    path = create_backup(include_media=settings.get("include_media", False))
    removed = prune_backups(settings.get("retain", 6))
    print(f"Created {path}")
    if removed:
        print("Removed old backups: " + ", ".join(removed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
