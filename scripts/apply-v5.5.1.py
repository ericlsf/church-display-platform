#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLEET = ROOT / "hub/services/fleet_operations.py"


def main():
    text = FLEET.read_text(encoding="utf-8")

    import_line = (
        "from services.telemetry_normalization import "
        "normalize_fleet_telemetry"
    )
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, value in enumerate(lines)
            if value.startswith("from services.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    marker = "        health = state_rows.get(display_id, {})"
    if "telemetry = normalize_fleet_telemetry(" not in text:
        if marker not in text:
            raise SystemExit("Could not locate fleet health block")
        text = text.replace(
            marker,
            marker
            + "\n        telemetry = normalize_fleet_telemetry(health, display)",
            1,
        )

    replacements = {
        '''        version = (
            health.get("version")
            or display.get("version")
            or "unknown"
        )''': '        version = telemetry["version"]',
        '''        media = health.get("media", {})
        media_count = int(
            health.get("media_count")
            or (media.get("total", 0) if isinstance(media, dict) else 0)
            or 0
        )''': '        media_count = telemetry["media_count"]',
        '''        player_running = bool(
            health.get("display_app_running")
            or health.get("player_running")
        )''': '        player_running = telemetry["player_running"]',
        '''        sync_ok = bool(
            health.get("sync_state") == "success"
            or health.get("last_sync_status") == "success"
        )''': '        sync_ok = telemetry["sync_ok"]',
    }

    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new, 1)

    required = [
        'version = telemetry["version"]',
        'media_count = telemetry["media_count"]',
        'player_running = telemetry["player_running"]',
        'sync_ok = telemetry["sync_ok"]',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(
            "Could not safely patch fleet telemetry: "
            + ", ".join(missing)
        )

    FLEET.write_text(text, encoding="utf-8")
    print("v5.5.1 live telemetry normalization applied.")


if __name__ == "__main__":
    main()
