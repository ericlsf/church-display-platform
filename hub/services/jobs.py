import json
import uuid
from datetime import datetime, timedelta

from services.config import CONFIG_DIR
from services.resilience import maintenance_enabled

JOBS_FILE = CONFIG_DIR / "jobs.json"
TERMINAL_STATUSES = {"success", "failed", "cancelled", "timed_out"}
MAINTENANCE_ALLOWED = {
    "heartbeat", "collect_logs", "list_files", "read_file", "upload_preview",
    "service_action", "update_check",
}


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def load_jobs():
    if not JOBS_FILE.exists():
        save_jobs({"jobs": []})
        return {"jobs": []}
    try:
        data = json.loads(JOBS_FILE.read_text())
    except Exception:
        data = {"jobs": []}
    data.setdefault("jobs", [])
    return data


def save_jobs(data):
    data.setdefault("jobs", [])
    tmp = JOBS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(JOBS_FILE)


def normalize_job(job):
    job.setdefault("attempt", 0)
    job.setdefault("max_attempts", 2)
    job.setdefault("timeout_seconds", 900)
    job.setdefault("cancel_requested", False)
    job.setdefault("cancellable", True)
    job.setdefault("history", [])
    return job


def create_job(display_id, job_type, payload=None, max_attempts=2, timeout_seconds=900):
    data = load_jobs()
    job = {
        "id": str(uuid.uuid4()),
        "display_id": display_id,
        "type": job_type,
        "payload": payload or {},
        "status": "queued",
        "progress": 0,
        "message": "",
        "created_at": now_iso(),
        "started_at": "",
        "updated_at": now_iso(),
        "completed_at": "",
        "attempt": 0,
        "max_attempts": max(1, int(max_attempts)),
        "timeout_seconds": max(30, int(timeout_seconds)),
        "cancel_requested": False,
        "cancellable": job_type not in {"reboot", "service_action"},
        "history": [],
    }
    data["jobs"].append(job)
    save_jobs(data)
    return job


def _expire_and_retry(data):
    changed = False
    now = datetime.now()
    for job in data["jobs"]:
        normalize_job(job)
        if job.get("status") != "running":
            continue
        started = parse_iso(job.get("started_at", ""))
        if not started:
            continue
        if now - started <= timedelta(seconds=int(job.get("timeout_seconds", 900))):
            continue
        job["history"].append({
            "at": now_iso(), "status": "timed_out", "message": "Job exceeded timeout"
        })
        if job["attempt"] < job["max_attempts"]:
            job.update({
                "status": "queued", "progress": 0,
                "message": f"Retrying after timeout ({job['attempt']}/{job['max_attempts']})",
                "started_at": "", "updated_at": now_iso(), "completed_at": "",
            })
        else:
            job.update({
                "status": "timed_out", "progress": 100,
                "message": "Job exceeded timeout and retries were exhausted",
                "updated_at": now_iso(), "completed_at": now_iso(),
            })
        changed = True
    if changed:
        save_jobs(data)


def list_jobs(limit=100):
    data = load_jobs()
    _expire_and_retry(data)
    return list(reversed(data["jobs"][-limit:]))


def get_next_job(display_id):
    data = load_jobs()
    _expire_and_retry(data)
    in_maintenance = maintenance_enabled()
    for job in data["jobs"]:
        normalize_job(job)
        if job.get("status") != "queued":
            continue
        if job.get("display_id") not in [display_id, "all"]:
            continue
        if in_maintenance and job.get("type") not in MAINTENANCE_ALLOWED:
            continue
        if job.get("cancel_requested"):
            job.update({"status": "cancelled", "progress": 100, "completed_at": now_iso(), "updated_at": now_iso(), "message": "Cancelled before execution"})
            save_jobs(data)
            continue
        job["status"] = "running"
        job["progress"] = 1
        job["attempt"] += 1
        job["started_at"] = now_iso()
        job["updated_at"] = now_iso()
        job["history"].append({"at": now_iso(), "status": "running", "message": f"Attempt {job['attempt']}"})
        save_jobs(data)
        return job
    return None


def update_job(job_id, status=None, progress=None, message=None):
    data = load_jobs()
    for job in data["jobs"]:
        normalize_job(job)
        if job.get("id") != job_id:
            continue
        if status:
            job["status"] = status
        if progress is not None:
            try: job["progress"] = int(progress)
            except Exception: pass
        if message is not None:
            job["message"] = str(message)
        job["updated_at"] = now_iso()
        if status in TERMINAL_STATUSES:
            job["completed_at"] = now_iso()
            job["history"].append({"at": now_iso(), "status": status, "message": job.get("message", "")})
        save_jobs(data)
        return job
    return None


def request_cancel(job_id):
    data = load_jobs()
    for job in data["jobs"]:
        normalize_job(job)
        if job.get("id") != job_id:
            continue
        if job.get("status") in TERMINAL_STATUSES:
            return job
        job["cancel_requested"] = True
        if job.get("status") == "queued":
            job.update({"status": "cancelled", "progress": 100, "completed_at": now_iso(), "message": "Cancelled by operator"})
        else:
            job["message"] = "Cancellation requested; waiting for current operation to stop"
        job["updated_at"] = now_iso()
        save_jobs(data)
        return job
    return None


def retry_job(job_id):
    data = load_jobs()
    for job in data["jobs"]:
        normalize_job(job)
        if job.get("id") != job_id:
            continue
        job.update({
            "status": "queued", "progress": 0, "message": "Manual retry queued",
            "started_at": "", "completed_at": "", "updated_at": now_iso(),
            "cancel_requested": False,
        })
        job["max_attempts"] = max(job["max_attempts"], job["attempt"] + 1)
        job["history"].append({"at": now_iso(), "status": "queued", "message": "Manual retry"})
        save_jobs(data)
        return job
    return None
