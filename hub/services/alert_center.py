"""Build actionable alerts from authoritative fleet state."""
from services.fleet_operations import fleet_rows
from services.fleet_truth import enrich_fleet_rows
from services.jobs import list_jobs

FAILED_STATES = {"failed", "timed_out", "cancelled"}

def _alert(key, severity, title, detail, display_id="", action_url="",
           action_label="View", category="system"):
    return {
        "key": key,
        "severity": severity,
        "title": title,
        "detail": detail,
        "display_id": display_id,
        "action_url": action_url,
        "action_label": action_label,
        "category": category,
    }

def build_alert_center():
    rows = enrich_fleet_rows(fleet_rows())
    jobs = list_jobs(1000)
    alerts = []

    for row in rows:
        display_id = row.get("id", "")
        name = row.get("name") or display_id
        url = f"/display/{display_id}"
        online = bool(row.get("online") or row.get("status_online"))
        health = int(row.get("health_score", 0) or 0)

        if not online:
            alerts.append(_alert(
                f"{display_id}:offline", "critical",
                f"{name} is offline",
                "No current heartbeat is available. Check power, networking, and the display agent.",
                display_id, url, "Open diagnostics", "connectivity",
            ))
        elif health < 60:
            alerts.append(_alert(
                f"{display_id}:health-critical", "critical",
                f"{name} health is {health}%",
                "One or more critical device checks are failing.",
                display_id, f"{url}#health-diagnostics", "Fix health", "health",
            ))
        elif health < 100:
            alerts.append(_alert(
                f"{display_id}:health-warning", "warning",
                f"{name} health is {health}%",
                "Review failed checks and available quick actions.",
                display_id, f"{url}#health-diagnostics", "Review health", "health",
            ))

        sync_state = str(row.get("sync_state", "")).strip().lower()
        if sync_state not in {"", "success", "complete", "completed", "ok"}:
            alerts.append(_alert(
                f"{display_id}:sync:{sync_state}", "warning",
                f"{name} media sync needs attention",
                f"Current sync state: {sync_state or 'unknown'}.",
                display_id, f"{url}#content-settings", "Review content", "content",
            ))

        if not row.get("sync_folder"):
            alerts.append(_alert(
                f"{display_id}:folder-missing", "warning",
                f"{name} has no content folder",
                "Assign a Drive content folder to this display.",
                display_id, f"{url}#content-settings", "Assign folder", "content",
            ))

        media_count = int(row.get("media_count", 0) or 0)
        if online and row.get("sync_folder") and media_count == 0:
            alerts.append(_alert(
                f"{display_id}:no-media", "critical",
                f"{name} has no local media",
                "A folder is assigned, but the latest heartbeat reports zero playable files.",
                display_id, f"{url}#content-settings", "Sync media", "content",
            ))

        if row.get("update_available"):
            alerts.append(_alert(
                f"{display_id}:update", "info",
                f"{name} has an update available",
                f'Installed {row.get("version", "unknown")}; latest {row.get("latest_tag", "available")}.',
                display_id, f"{url}#software-upgrade", "Upgrade", "software",
            ))

        disk_text = str((row.get("system") or {}).get("disk", "")).strip().rstrip("%")
        try:
            disk = int(disk_text)
        except ValueError:
            disk = 0

        if disk >= 90:
            alerts.append(_alert(
                f"{display_id}:disk", "critical",
                f"{name} storage is {disk}% full",
                "Free storage before media sync or software updates fail.",
                display_id, f"{url}#health-diagnostics", "Review storage", "system",
            ))
        elif disk >= 80:
            alerts.append(_alert(
                f"{display_id}:disk-warning", "warning",
                f"{name} storage is {disk}% full",
                "Plan cleanup before the device reaches critical capacity.",
                display_id, f"{url}#health-diagnostics", "Review storage", "system",
            ))

    failed_jobs = [
        job for job in jobs
        if str(job.get("status", "")).lower() in FAILED_STATES
    ]
    failed_jobs.sort(
        key=lambda job: job.get("updated_at") or job.get("created_at") or "",
        reverse=True,
    )

    for job in failed_jobs[:20]:
        display_id = job.get("display_id", "")
        alerts.append(_alert(
            f'job:{job.get("id")}', "warning",
            f'{job.get("type", "Job")} failed' + (f" on {display_id}" if display_id else ""),
            job.get("message") or "Review the job record for failure details.",
            display_id, "/jobs", "View job", "jobs",
        ))

    order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda item: (order.get(item["severity"], 9), item["title"].lower()))

    counts = {
        "critical": sum(a["severity"] == "critical" for a in alerts),
        "warning": sum(a["severity"] == "warning" for a in alerts),
        "info": sum(a["severity"] == "info" for a in alerts),
        "total": len(alerts),
    }
    return {"alerts": alerts, "counts": counts, "rows": rows}
