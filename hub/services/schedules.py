import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from services.config import CONFIG_DIR
from services.events import log_event
from services.jobs import create_job

SCHEDULES_FILE = CONFIG_DIR / "schedules.json"


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def load_schedules():
    if not SCHEDULES_FILE.exists():
        save_schedules({"schedules": []})
        return {"schedules": []}

    try:
        data = json.loads(SCHEDULES_FILE.read_text())
    except Exception:
        data = {"schedules": []}

    data.setdefault("schedules", [])
    return data


def save_schedules(data):
    data.setdefault("schedules", [])
    SCHEDULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SCHEDULES_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(SCHEDULES_FILE)


def create_schedule(name, display_id, job_type, run_at, payload=None, recurrence="once"):
    data = load_schedules()
    schedule = {
        "id": str(uuid.uuid4()),
        "name": name or job_type,
        "display_id": display_id,
        "job_type": job_type,
        "payload": payload or {},
        "run_at": run_at,
        "recurrence": recurrence or "once",
        "enabled": True,
        "last_run": "",
        "created_at": now_iso(),
    }
    data["schedules"].append(schedule)
    save_schedules(data)
    return schedule


def delete_schedule(schedule_id):
    data = load_schedules()
    before = len(data.get("schedules", []))
    data["schedules"] = [s for s in data.get("schedules", []) if s.get("id") != schedule_id]
    save_schedules(data)
    return len(data["schedules"]) != before


def toggle_schedule(schedule_id):
    data = load_schedules()
    changed = False
    for schedule in data.get("schedules", []):
        if schedule.get("id") == schedule_id:
            schedule["enabled"] = not bool(schedule.get("enabled", True))
            changed = True
            break
    save_schedules(data)
    return changed


def parse_run_at(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def advance_daily(value):
    run_at = parse_run_at(value)
    if not run_at:
        return value
    next_run = run_at + timedelta(days=1)
    while next_run <= datetime.now():
        next_run += timedelta(days=1)
    return next_run.isoformat(timespec="minutes")


def process_due_schedules():
    data = load_schedules()
    now = datetime.now()
    queued = []

    for schedule in data.get("schedules", []):
        if not schedule.get("enabled", True):
            continue

        run_at = parse_run_at(schedule.get("run_at", ""))
        if not run_at or run_at > now:
            continue

        job = create_job(
            schedule.get("display_id", ""),
            schedule.get("job_type", ""),
            schedule.get("payload", {}),
        )
        queued.append(job)
        schedule["last_run"] = now_iso()
        log_event(f"Scheduled job {schedule.get('job_type')} queued for {schedule.get('display_id')}")

        if schedule.get("recurrence") == "daily":
            schedule["run_at"] = advance_daily(schedule.get("run_at", ""))
        else:
            schedule["enabled"] = False

    if queued:
        save_schedules(data)

    return queued
