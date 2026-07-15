from services.jobs import list_jobs


ACTIVE_STATUSES = {
    "queued",
    "pending",
    "running",
    "retrying",
    "in_progress",
}


def normalize_dry_run(value):
    return str(value).strip().lower() not in {"0", "false", "no"}


def existing_deployment(display_id, target, dry_run):
    wanted_dry_run = normalize_dry_run(dry_run)

    for job in list_jobs(1000):
        if job.get("type") != "deploy_update":
            continue
        if job.get("display_id") != display_id:
            continue
        if str(job.get("status", "")).lower() not in ACTIVE_STATUSES:
            continue

        payload = job.get("payload", {})
        if payload.get("target") != target:
            continue
        if normalize_dry_run(payload.get("dry_run", True)) != wanted_dry_run:
            continue

        return job

    return None


def unique_display_ids(values):
    result = []
    seen = set()

    for value in values:
        display_id = str(value or "").strip()
        if not display_id or display_id in seen:
            continue
        seen.add(display_id)
        result.append(display_id)

    return result
