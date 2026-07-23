"""Bulk fleet operations with validation and duplicate-job protection."""

from __future__ import annotations

from services.config import load_config
from services.jobs import create_job, list_jobs


ACTIVE_STATES = {
    "queued",
    "pending",
    "running",
    "retrying",
    "in_progress",
}


def _display_map():
    return {
        item.get("id"): item
        for item in load_config().get("displays", [])
        if item.get("id")
    }


def _active_duplicate(display_id, job_type, payload):
    target = str(payload.get("target", ""))
    folder = str(payload.get("folder", ""))
    profile = str(payload.get("profile_id", ""))

    for job in list_jobs(1000):
        if (
            job.get("display_id") != display_id
            or job.get("type") != job_type
            or str(job.get("status", "")).lower()
            not in ACTIVE_STATES
        ):
            continue

        existing = job.get("payload", {})

        if (
            str(existing.get("target", "")) == target
            and str(existing.get("folder", "")) == folder
            and str(existing.get("profile_id", "")) == profile
        ):
            return job

    return None


def queue_bulk_jobs(
    display_ids,
    operation,
    *,
    folder="",
    profile_id="",
    target="",
    maintenance_enabled=None,
):
    displays = _display_map()
    selected = []

    for display_id in display_ids:
        display_id = str(display_id or "").strip()
        if display_id and display_id in displays:
            selected.append(display_id)

    selected = list(dict.fromkeys(selected))

    if not selected:
        raise ValueError("Select at least one valid display")

    mapping = {
        "sync_now": ("sync_now", {}),
        "restart_display": ("restart_display", {}),
        "reboot": ("reboot", {}),
        "collect_logs": ("collect_logs", {}),
    }

    if operation in mapping:
        job_type, payload = mapping[operation]

    elif operation == "assign_folder":
        folder = str(folder or "").strip()
        if not folder:
            raise ValueError("Choose a content folder")
        job_type = "set_sync_folder"
        payload = {"folder": folder}

    elif operation == "assign_profile":
        profile_id = str(profile_id or "").strip()
        if not profile_id:
            raise ValueError("Choose a display profile")
        job_type = "apply_display_profile"
        payload = {"profile_id": profile_id}

    elif operation == "deploy_update":
        target = str(target or "").strip()
        if not target:
            raise ValueError("Choose a software release")
        job_type = "deploy_update"
        payload = {
            "target": target,
            "dry_run": False,
            "restart_after_install": True,
            "verify_health": True,
        }

    elif operation == "maintenance":
        if maintenance_enabled is None:
            raise ValueError("Choose maintenance mode on or off")
        job_type = "set_maintenance"
        payload = {"enabled": bool(maintenance_enabled)}

    else:
        raise ValueError("Unsupported bulk operation")

    queued = []
    skipped = []

    for display_id in selected:
        duplicate = _active_duplicate(
            display_id,
            job_type,
            payload,
        )

        if duplicate:
            skipped.append({
                "display_id": display_id,
                "reason": "matching active job already exists",
                "job_id": duplicate.get("id"),
            })
            continue

        job = create_job(
            display_id,
            job_type,
            dict(payload),
        )
        queued.append(job)

    return {
        "operation": operation,
        "selected_count": len(selected),
        "queued_count": len(queued),
        "skipped_count": len(skipped),
        "queued": queued,
        "skipped": skipped,
    }
