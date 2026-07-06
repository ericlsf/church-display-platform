from datetime import datetime
from services.config import EVENT_LOG_FILE


def log_event(message):
    EVENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S")
    with open(EVENT_LOG_FILE, "a") as f:
        f.write(f"{stamp}  {message}\n")


def read_events(limit=100):
    if not EVENT_LOG_FILE.exists():
        return []
    try:
        lines = EVENT_LOG_FILE.read_text().splitlines()
    except Exception:
        return []
    return list(reversed(lines[-limit:]))
