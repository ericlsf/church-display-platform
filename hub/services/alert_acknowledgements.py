"""Persistent alert acknowledgement state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "config" / "alert_acknowledgements.json"
_LOCK = Lock()


def _load():
    if not STATE_FILE.exists():
        return {"acknowledgements": {}}

    try:
        data = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
    except Exception:
        return {"acknowledgements": {}}

    if not isinstance(data, dict):
        return {"acknowledgements": {}}

    data.setdefault("acknowledgements", {})
    return data


def _save(data):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp = STATE_FILE.with_suffix(".json.tmp")
    temp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp.replace(STATE_FILE)


def list_acknowledgements():
    return dict(
        _load().get("acknowledgements", {})
    )


def acknowledge_alert(key, *, user="", note=""):
    key = str(key or "").strip()

    if not key:
        raise ValueError("Alert key is required")

    with _LOCK:
        data = _load()

        data["acknowledgements"][key] = {
            "acknowledged_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "acknowledged_by": str(user or ""),
            "note": str(note or "").strip(),
        }

        _save(data)

    return data["acknowledgements"][key]


def clear_acknowledgement(key):
    key = str(key or "").strip()

    if not key:
        raise ValueError("Alert key is required")

    with _LOCK:
        data = _load()
        removed = data["acknowledgements"].pop(
            key,
            None,
        )
        _save(data)

    return removed


def clear_stale_acknowledgements(active_keys):
    active_keys = {
        str(key)
        for key in active_keys
        if key
    }

    with _LOCK:
        data = _load()
        existing = data["acknowledgements"]

        stale = [
            key
            for key in existing
            if key not in active_keys
        ]

        for key in stale:
            existing.pop(key, None)

        if stale:
            _save(data)

    return stale
