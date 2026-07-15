from services.config import load_config, load_hub_settings
from services.deployment_guard import existing_deployment
from services.display_artifacts import create_artifact
from services.jobs import create_job, list_jobs
from services.maintenance import in_maintenance
from services.releases import latest_git_tag, list_git_tags


ACTIVE = {
    "queued",
    "pending",
    "running",
    "retrying",
    "in_progress",
}


def _package_url(sha256):
    hub_url = (
        load_hub_settings().get("hub_url")
        or "http://church-display-hub.local:8090"
    ).rstrip("/")
    return (
        f"{hub_url}/api/v1/display-releases/"
        f"artifacts/{sha256}.tar.gz"
    )


def display_upgrade_state(display_id, current_version=""):
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

    latest = latest_git_tag()
    active_job = next(
        (
            job
            for job in jobs
            if str(job.get("status", "")).lower()
            in ACTIVE
        ),
        None,
    )

    last_job = jobs[0] if jobs else None

    return {
        "latest_version": latest,
        "release_tags": list_git_tags(),
        "current_version": current_version or "unknown",
        "update_available": bool(
            latest
            and current_version
            and current_version != "unknown"
            and str(latest) != str(current_version)
        ),
        "active_job": active_job,
        "last_job": last_job,
    }


def queue_display_upgrade(
    display_id,
    target,
    dry_run=True,
    override_maintenance=False,
):
    config = load_config()
    display = next(
        (
            item
            for item in config.get("displays", [])
            if item.get("id") == display_id
        ),
        None,
    )

    if not display:
        raise ValueError("Display not found")

    if in_maintenance(display) and not override_maintenance:
        raise ValueError(
            "This display is in maintenance mode. "
            "Enable the maintenance override to deploy."
        )

    target = str(target or "").strip()
    if not target:
        raise ValueError("Choose a target version")

    existing = existing_deployment(
        display_id,
        target,
        dry_run,
    )
    if existing:
        return {
            "job": existing,
            "reused": True,
        }

    artifact = create_artifact(target)

    job = create_job(
        display_id,
        "deploy_update",
        {
            "target": target,
            "dry_run": bool(dry_run),
            "package_url": _package_url(
                artifact["sha256"]
            ),
            "sha256": artifact["sha256"],
            "commit": artifact.get("commit", ""),
            "package_size": artifact["size"],
            "deployment_mode": (
                "display_details_one_click"
            ),
            "rollback_on_failure": True,
            "restart_after_install": True,
            "health_check_after_install": True,
        },
    )

    return {
        "job": job,
        "reused": False,
    }


def queue_rollback(display_id, failed_job_id=""):
    failed_job = None

    for job in list_jobs(1000):
        if (
            job.get("id") == failed_job_id
            and job.get("display_id") == display_id
            and job.get("type") == "deploy_update"
        ):
            failed_job = job
            break

    if failed_job_id and not failed_job:
        raise ValueError(
            "The failed deployment could not be found"
        )

    payload = {
        "source_job_id": failed_job_id,
        "reason": "Administrator requested rollback",
    }

    if failed_job:
        failed_payload = failed_job.get("payload", {})
        payload["failed_target"] = failed_payload.get(
            "target",
            "",
        )
        payload["previous_version"] = failed_payload.get(
            "previous_version",
            "",
        )

    return create_job(
        display_id,
        "rollback_update",
        payload,
    )
