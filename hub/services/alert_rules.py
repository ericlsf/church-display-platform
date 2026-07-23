"""Persistent Alert Center policy configuration."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock


ROOT = Path(__file__).resolve().parents[1]
RULES_FILE = ROOT / "config" / "alert_rules.json"
_LOCK = Lock()

DEFAULT_RULES = {
    "offline_delay_minutes": 5,
    "disk_warning_percent": 80,
    "disk_critical_percent": 90,
    "health_warning_percent": 100,
    "health_critical_percent": 60,
    "quiet_hours_enabled": False,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00",
    "categories": {
        "connectivity": True,
        "health": True,
        "content": True,
        "software": True,
        "system": True,
        "jobs": True,
    },
}


def _merged_rules(data):
    result = {
        **DEFAULT_RULES,
        **(data if isinstance(data, dict) else {}),
    }

    result["categories"] = {
        **DEFAULT_RULES["categories"],
        **result.get("categories", {}),
    }

    return result


def load_alert_rules():
    if not RULES_FILE.exists():
        return _merged_rules({})

    try:
        data = json.loads(
            RULES_FILE.read_text(encoding="utf-8")
        )
    except Exception:
        data = {}

    return _merged_rules(data)


def save_alert_rules(rules):
    normalized = _merged_rules(rules)

    normalized["offline_delay_minutes"] = min(
        max(
            int(normalized["offline_delay_minutes"]),
            0,
        ),
        1440,
    )

    normalized["disk_warning_percent"] = min(
        max(
            int(normalized["disk_warning_percent"]),
            1,
        ),
        99,
    )

    normalized["disk_critical_percent"] = min(
        max(
            int(normalized["disk_critical_percent"]),
            normalized["disk_warning_percent"],
        ),
        100,
    )

    normalized["health_warning_percent"] = min(
        max(
            int(normalized["health_warning_percent"]),
            1,
        ),
        100,
    )

    normalized["health_critical_percent"] = min(
        max(
            int(normalized["health_critical_percent"]),
            0,
        ),
        normalized["health_warning_percent"],
    )

    with _LOCK:
        RULES_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp = RULES_FILE.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(
                normalized,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temp.replace(RULES_FILE)

    return normalized
