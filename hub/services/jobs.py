import json
import uuid
from datetime import datetime

from services.config import CONFIG_DIR


JOBS_FILE = CONFIG_DIR / "jobs.json"


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


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


def create_job(display_id, job_type, payload=None):
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
    }

    data["jobs"].append(job)
    save_jobs(data)
    return job


def list_jobs(limit=100):
    return list(reversed(load_jobs()["jobs"][-limit:]))


def get_next_job(display_id):
    data = load_jobs()

    for job in data["jobs"]:
        if job.get("status") != "queued":
            continue

        if job.get("display_id") not in [display_id, "all"]:
            continue

        job["status"] = "running"
        job["progress"] = 1
        job["started_at"] = now_iso()
        job["updated_at"] = now_iso()
        save_jobs(data)
        return job

    return None


def update_job(job_id, status=None, progress=None, message=None):
    data = load_jobs()

    for job in data["jobs"]:
        if job.get("id") != job_id:
            continue

        if status:
            job["status"] = status

        if progress is not None:
            try:
                job["progress"] = int(progress)
            except Exception:
                pass

        if message is not None:
            job["message"] = str(message)

        job["updated_at"] = now_iso()

        if status in ["success", "failed", "cancelled"]:
            job["completed_at"] = now_iso()

        save_jobs(data)
        return job

    return None


