import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from services.config import load_config
from services.deployment_guard import unique_display_ids
from services.display_artifacts import create_artifact
from services.jobs import create_job, list_jobs
from services.config import load_hub_settings


ROOT = Path(__file__).resolve().parents[2]
ROLLOUTS_FILE = ROOT / "hub" / "config" / "rollouts.json"

ACTIVE = {"scheduled", "running", "waiting_canary", "paused"}
TERMINAL = {"success", "failed", "cancelled"}


def _now():
    return datetime.now(timezone.utc)


def _parse_time(value):
    if not value:
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_rollouts():
    if not ROLLOUTS_FILE.exists():
        return {"rollouts": []}
    try:
        data = json.loads(ROLLOUTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {"rollouts": []}
    data.setdefault("rollouts", [])
    return data


def save_rollouts(data):
    ROLLOUTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = ROLLOUTS_FILE.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(ROLLOUTS_FILE)


def _package_url(sha256):
    hub_url = (
        load_hub_settings().get("hub_url")
        or "http://church-display-hub.local:8090"
    ).rstrip("/")
    return (
        f"{hub_url}/api/v1/display-releases/"
        f"artifacts/{sha256}.tar.gz"
    )


def create_rollout(
    target,
    display_ids,
    scheduled_for,
    canary_display_id="",
    pause_on_failure=True,
    dry_run=False,
):
    display_ids = unique_display_ids(display_ids)
    if not display_ids:
        raise ValueError("Select at least one display")

    artifact = create_artifact(target)
    scheduled = _parse_time(scheduled_for) or _now()

    if canary_display_id and canary_display_id not in display_ids:
        raise ValueError("The canary display must be part of the rollout")

    rollout = {
        "id": str(uuid.uuid4()),
        "target": target,
        "display_ids": display_ids,
        "canary_display_id": canary_display_id,
        "pause_on_failure": bool(pause_on_failure),
        "dry_run": bool(dry_run),
        "scheduled_for": scheduled.isoformat(),
        "status": "scheduled",
        "created_at": _now().isoformat(),
        "updated_at": _now().isoformat(),
        "artifact": {
            "sha256": artifact["sha256"],
            "commit": artifact.get("commit", ""),
            "size": artifact["size"],
            "package_url": _package_url(artifact["sha256"]),
        },
        "jobs": {},
        "message": "Waiting for scheduled start",
    }

    data = load_rollouts()
    data["rollouts"].append(rollout)
    save_rollouts(data)
    return rollout


def _job_for(rollout, display_id):
    job_id = rollout.get("jobs", {}).get(display_id)
    if not job_id:
        return None
    for job in list_jobs(2000):
        if job.get("id") == job_id:
            return job
    return None


def _queue_display(rollout, display_id):
    artifact = rollout["artifact"]
    job = create_job(
        display_id,
        "deploy_update",
        {
            "target": rollout["target"],
            "dry_run": rollout["dry_run"],
            "package_url": artifact["package_url"],
            "sha256": artifact["sha256"],
            "commit": artifact.get("commit", ""),
            "package_size": artifact["size"],
            "deployment_mode": "scheduled_rollout",
            "rollout_id": rollout["id"],
        },
    )
    rollout.setdefault("jobs", {})[display_id] = job["id"]
    return job


def process_rollouts():
    data = load_rollouts()
    changed = False
    now = _now()

    for rollout in data.get("rollouts", []):
        if rollout.get("status") in TERMINAL:
            continue

        scheduled = _parse_time(rollout.get("scheduled_for"))
        if scheduled and scheduled > now:
            continue

        canary = rollout.get("canary_display_id")
        display_ids = rollout.get("display_ids", [])

        if rollout.get("status") == "scheduled":
            if canary:
                _queue_display(rollout, canary)
                rollout["status"] = "waiting_canary"
                rollout["message"] = f"Canary deployment queued for {canary}"
            else:
                for display_id in display_ids:
                    _queue_display(rollout, display_id)
                rollout["status"] = "running"
                rollout["message"] = "Deployment jobs queued"
            rollout["updated_at"] = now.isoformat()
            changed = True
            continue

        if rollout.get("status") == "waiting_canary":
            job = _job_for(rollout, canary)
            if not job:
                continue

            status = str(job.get("status", "")).lower()
            if status == "success":
                for display_id in display_ids:
                    if display_id == canary:
                        continue
                    _queue_display(rollout, display_id)
                rollout["status"] = "running"
                rollout["message"] = "Canary succeeded; remaining displays queued"
                rollout["updated_at"] = now.isoformat()
                changed = True
            elif status in {"failed", "timed_out", "cancelled"}:
                rollout["status"] = (
                    "paused" if rollout.get("pause_on_failure", True) else "failed"
                )
                rollout["message"] = f"Canary failed: {job.get('message', status)}"
                rollout["updated_at"] = now.isoformat()
                changed = True
            continue

        if rollout.get("status") == "running":
            jobs = [
                _job_for(rollout, display_id)
                for display_id in display_ids
                if rollout.get("jobs", {}).get(display_id)
            ]
            jobs = [job for job in jobs if job]

            statuses = [str(job.get("status", "")).lower() for job in jobs]
            failures = [
                job for job in jobs
                if str(job.get("status", "")).lower()
                in {"failed", "timed_out", "cancelled"}
            ]

            if failures and rollout.get("pause_on_failure", True):
                rollout["status"] = "paused"
                rollout["message"] = (
                    f"Paused after {len(failures)} failed deployment(s)"
                )
                rollout["updated_at"] = now.isoformat()
                changed = True
            elif jobs and all(status == "success" for status in statuses):
                rollout["status"] = "success"
                rollout["message"] = "Rollout completed successfully"
                rollout["updated_at"] = now.isoformat()
                changed = True

    if changed:
        save_rollouts(data)

    return data


def cancel_rollout(rollout_id):
    data = load_rollouts()
    for rollout in data.get("rollouts", []):
        if rollout.get("id") == rollout_id:
            rollout["status"] = "cancelled"
            rollout["message"] = "Cancelled by administrator"
            rollout["updated_at"] = _now().isoformat()
            save_rollouts(data)
            return rollout
    raise ValueError("Rollout not found")


def resume_rollout(rollout_id):
    data = load_rollouts()
    for rollout in data.get("rollouts", []):
        if rollout.get("id") == rollout_id:
            if rollout.get("status") != "paused":
                raise ValueError("Only paused rollouts can be resumed")
            rollout["pause_on_failure"] = False
            rollout["status"] = "running"
            rollout["message"] = "Resumed by administrator"
            rollout["updated_at"] = _now().isoformat()
            save_rollouts(data)
            return rollout
    raise ValueError("Rollout not found")


def rollout_rows():
    data = process_rollouts()
    displays = {
        item.get("id"): item.get("name", item.get("id"))
        for item in load_config().get("displays", [])
    }

    rows = []
    for rollout in reversed(data.get("rollouts", [])):
        job_states = []
        for display_id in rollout.get("display_ids", []):
            job = _job_for(rollout, display_id)
            job_states.append({
                "display_id": display_id,
                "display_name": displays.get(display_id, display_id),
                "status": job.get("status") if job else "waiting",
                "progress": job.get("progress", 0) if job else 0,
                "message": job.get("message", "") if job else "",
            })
        row = dict(rollout)
        row["job_states"] = job_states
        rows.append(row)

    return rows
