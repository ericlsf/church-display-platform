import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_FILE = ROOT / "hub" / "logs" / "audit.jsonl"

SENSITIVE_KEYS = {
    "password",
    "current_password",
    "new_password",
    "confirm_password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "cookie",
}

MAX_VALUE_LENGTH = 500


def _now():
    return datetime.now(timezone.utc).isoformat()


def _clean_value(value):
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return [_clean_value(item) for item in value[:50]]
    if isinstance(value, dict):
        return sanitize_details(value)

    text = str(value)
    if len(text) > MAX_VALUE_LENGTH:
        text = text[:MAX_VALUE_LENGTH] + "…"
    return text


def sanitize_details(details):
    result = {}
    for key, value in (details or {}).items():
        key_text = str(key)
        if key_text.lower() in SENSITIVE_KEYS:
            result[key_text] = "[REDACTED]"
        else:
            result[key_text] = _clean_value(value)
    return result


def append_audit(
    action,
    actor="unknown",
    category="system",
    target="",
    details=None,
    status="success",
    request_id="",
    remote_addr="",
):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "id": str(uuid.uuid4()),
        "timestamp": _now(),
        "actor": actor or "unknown",
        "category": category or "system",
        "action": action or "unknown",
        "target": target or "",
        "status": status or "success",
        "details": sanitize_details(details or {}),
        "request_id": request_id or "",
        "remote_addr": remote_addr or "",
    }

    with AUDIT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")

    return record


def read_audit(
    limit=100,
    actor="",
    category="",
    action="",
    status="",
    query="",
):
    if not AUDIT_FILE.exists():
        return []

    rows = []
    actor = actor.strip().lower()
    category = category.strip().lower()
    action = action.strip().lower()
    status = status.strip().lower()
    query = query.strip().lower()

    with AUDIT_FILE.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except Exception:
                continue

            if actor and actor not in str(row.get("actor", "")).lower():
                continue
            if category and category != str(row.get("category", "")).lower():
                continue
            if action and action not in str(row.get("action", "")).lower():
                continue
            if status and status != str(row.get("status", "")).lower():
                continue

            if query:
                haystack = json.dumps(row, sort_keys=True).lower()
                if query not in haystack:
                    continue

            rows.append(row)

    rows.reverse()
    return rows[: max(1, min(int(limit), 5000))]


def distinct_values(field):
    values = {
        str(row.get(field, "")).strip()
        for row in read_audit(limit=5000)
        if str(row.get(field, "")).strip()
    }
    return sorted(values, key=str.lower)


def export_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp",
        "actor",
        "category",
        "action",
        "target",
        "status",
        "request_id",
        "remote_addr",
        "details",
    ])

    for row in rows:
        writer.writerow([
            row.get("timestamp", ""),
            row.get("actor", ""),
            row.get("category", ""),
            row.get("action", ""),
            row.get("target", ""),
            row.get("status", ""),
            row.get("request_id", ""),
            row.get("remote_addr", ""),
            json.dumps(row.get("details", {}), sort_keys=True),
        ])

    return output.getvalue()
