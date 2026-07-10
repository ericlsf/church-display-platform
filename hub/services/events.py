from datetime import datetime
from services.config import EVENT_LOG_FILE
from services.database import record_event, recent_events


def log_event(message, category="general", level="info", metadata=None):
    EVENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S")
    with open(EVENT_LOG_FILE, "a") as f:
        f.write(f"{stamp}  {message}\n")
    try:
        record_event(message, category=category, level=level, metadata=metadata)
    except Exception:
        pass


def read_events(limit=100):
    try:
        rows = recent_events(limit)
        if rows:
            return [f"{row['created_at']}  {row['message']}" for row in rows]
    except Exception:
        pass
    if not EVENT_LOG_FILE.exists():
        return []
    try:
        lines = EVENT_LOG_FILE.read_text().splitlines()
    except Exception:
        return []
    return list(reversed(lines[-limit:]))
