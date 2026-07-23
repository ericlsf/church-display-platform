"""Verify deployment success against the display's next heartbeat."""

from __future__ import annotations

from services.jobs import list_jobs
from services.live_display_telemetry import exact_live_telemetry
from services.version_compare import versions_match


SUCCESS_STATUSES = {
    "success",
    "succeeded",
    "complete",
    "completed",
}

ACTIVE_STATUSES = {
    "queued",
    "pending",
    "running",
    "retrying",
    "in_progress",
}


def deployment_verification_state(
    display_id,
    current_version="",
):
    jobs = [
        job
        for job in list_jobs(1000)
        if job.get("display_id") == display_id
        and job.get("type") == "deploy_update"
    ]

    jobs.sort(
        key=lambda job: (
            job.get("updated_at")
            or job.get("created_at")
            or ""
        ),
        reverse=True,
    )

    latest_job = jobs[0] if jobs else None

    telemetry = exact_live_telemetry(
        display_id,
        fallback={"version": current_version},
    )

    reported_version = (
        telemetry.get("heartbeat_version")
        or telemetry.get("version")
        or current_version
        or "unknown"
    )

    result = {
        "state": "idle",
        "target_version": "",
        "reported_version": reported_version,
        "job": latest_job,
        "verified": False,
        "message": "",
    }

    if not latest_job:
        return result

    status = str(
        latest_job.get("status", "")
    ).strip().lower()

    payload = latest_job.get("payload", {})
    target = str(
        payload.get("target", "")
    ).strip()

    result["target_version"] = target

    if status in ACTIVE_STATUSES:
        result["state"] = "deploying"
        result["message"] = (
            "Deployment is still running."
        )
        return result

    if status in SUCCESS_STATUSES:
        if target and versions_match(reported_version, target):
            result["state"] = "verified"
            result["verified"] = True
            result["message"] = (
                f"Heartbeat confirms {target}."
            )
        else:
            result["state"] = "verification_failed"
            result["message"] = (
                "Installer reported success, but the latest heartbeat "
                f"reports {reported_version} instead of {target or 'the target version'}."
            )
        return result

    result["state"] = "failed"
    result["message"] = (
        latest_job.get("message")
        or f"Deployment ended with status {status or 'unknown'}."
    )

    return result
