"""Automatically queue rollback after deployment verification timeout."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.deployment_verification import (
    deployment_verification_state,
)
from services.jobs import create_job, list_jobs


DEFAULT_TIMEOUT_SECONDS = 180
ACTIVE_STATUSES = {
    "queued",
    "pending",
    "running",
    "retrying",
    "in_progress",
}


def _parse_datetime(value):
    text = str(value or "").strip()

    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        result = datetime.fromisoformat(text)
    except ValueError:
        return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


def _rollback_already_exists(display_id, source_job_id):
    for job in list_jobs(1000):
        if (
            job.get("display_id") == display_id
            and job.get("type") == "rollback_update"
            and job.get("payload", {}).get("source_job_id")
            == source_job_id
        ):
            return job

    return None


def automatic_rollback_state(
    display_id,
    *,
    timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    now=None,
):
    now = now or datetime.now(timezone.utc)
    verification = deployment_verification_state(
        display_id
    )
    job = verification.get("job") or {}

    result = {
        "enabled": True,
        "timeout_seconds": timeout_seconds,
        "verification": verification,
        "eligible": False,
        "queued": False,
        "rollback_job": None,
        "seconds_remaining": None,
        "message": "",
    }

    if verification.get("state") != "verification_failed":
        result["message"] = (
            "Automatic rollback is waiting for a verification failure."
        )
        return result

    source_job_id = job.get("id")
    if not source_job_id:
        result["message"] = (
            "The failed deployment does not have a job identifier."
        )
        return result

    existing = _rollback_already_exists(
        display_id,
        source_job_id,
    )
    if existing:
        result["queued"] = True
        result["rollback_job"] = existing
        result["message"] = (
            "Automatic rollback has already been queued."
        )
        return result

    completed_at = _parse_datetime(
        job.get("updated_at")
        or job.get("completed_at")
        or job.get("created_at")
    )

    if not completed_at:
        result["message"] = (
            "The deployment completion time is unavailable."
        )
        return result

    deadline = completed_at + timedelta(
        seconds=timeout_seconds
    )
    seconds_remaining = max(
        0,
        int((deadline - now).total_seconds()),
    )
    result["seconds_remaining"] = seconds_remaining

    if now < deadline:
        result["message"] = (
            "Waiting for the target version heartbeat before rollback."
        )
        return result

    result["eligible"] = True

    rollback_job = create_job(
        display_id,
        "rollback_update",
        {
            "source_job_id": source_job_id,
            "failed_target": verification.get(
                "target_version",
                "",
            ),
            "reported_version": verification.get(
                "reported_version",
                "",
            ),
            "reason": (
                "Automatic rollback after deployment "
                "verification timeout"
            ),
            "automatic": True,
            "verification_timeout_seconds": timeout_seconds,
        },
    )

    result["queued"] = True
    result["rollback_job"] = rollback_job
    result["message"] = (
        "Automatic rollback queued after verification timeout."
    )

    return result
