"""Fleet-level operational summary for the Hub landing page."""

from __future__ import annotations

from services.fleet_operations import fleet_rows
from services.jobs import job_is_unresolved_failure, list_jobs


ACTIVE_JOB_STATES = {
    "queued",
    "pending",
    "running",
    "retrying",
    "in_progress",
}

FAILED_JOB_STATES = {
    "failed",
    "timed_out",
    "cancelled",
}


def build_fleet_dashboard():
    rows = list(fleet_rows())
    jobs = list_jobs(1000)

    total = len(rows)
    online = sum(
        1
        for row in rows
        if row.get("online")
        or row.get("status_online")
    )
    offline = total - online

    healthy = sum(
        1
        for row in rows
        if int(row.get("health_score", 0) or 0) >= 100
    )
    warning = sum(
        1
        for row in rows
        if 60 <= int(row.get("health_score", 0) or 0) < 100
    )
    critical = sum(
        1
        for row in rows
        if int(row.get("health_score", 0) or 0) < 60
    )

    updates = sum(
        1
        for row in rows
        if row.get("update_available")
    )
    sync_errors = sum(
        1
        for row in rows
        if row.get("device_role") != "controller"
        if str(row.get("sync_state", "")).lower()
        not in {"success", "completed", "complete", "ok", ""}
    )

    failed_jobs = [
        job
        for job in jobs
        if job_is_unresolved_failure(job)
    ]
    active_jobs = [
        job
        for job in jobs
        if str(job.get("status", "")).lower()
        in ACTIVE_JOB_STATES
    ]

    attention = []

    for row in rows:
        issues = []
        controller = row.get("device_role") == "controller"
        display_id = row.get("id")
        is_online = bool(row.get("online") or row.get("status_online"))

        def add_issue(key, label, action_label, href="", endpoint=""):
            if any(issue["key"] == key for issue in issues):
                return
            issues.append({
                "key": key,
                "label": label,
                "action_label": action_label,
                "href": href,
                "endpoint": endpoint,
            })

        if not is_online:
            add_issue("offline", "Offline", "Open diagnostics", f"/display/{display_id}")

        checks = row.get("checks", {}) or {}
        if is_online and int(row.get("health_score", 0) or 0) < 100:
            if not checks.get("player", False) and not controller:
                add_issue("player", "Player stopped", "Restart player", endpoint=f"/fleet/{display_id}/restart")
            if not checks.get("playlist", False) and not controller:
                add_issue("playlist", "No content assigned", "Manage content", f"/display/{display_id}/operator")
            if not checks.get("media", False) and not controller:
                add_issue("media", "No local media", "Sync now", endpoint=f"/fleet/{display_id}/sync-now")
            if not checks.get("sync", False) and not controller:
                add_issue("sync", "Sync incomplete", "Sync now", endpoint=f"/fleet/{display_id}/sync-now")

        if not controller and row.get("update_available"):
            add_issue("update", "Software update available", "Update display", endpoint="/deployments/queue-latest")

        sync_state = str(
            row.get("sync_state", "")
        ).strip().lower()

        if is_online and not controller and sync_state not in {
            "",
            "success",
            "completed",
            "complete",
            "ok",
        }:
            add_issue("sync", f"Sync {sync_state}", "Sync now", endpoint=f"/fleet/{display_id}/sync-now")

        if issues:
            attention.append({
                "id": row.get("id"),
                "name": row.get("name") or row.get("id"),
                "online": bool(
                    row.get("online")
                    or row.get("status_online")
                ),
                "health_score": int(
                    row.get("health_score", 0)
                    or 0
                ),
                "version": row.get("version", "Unknown"),
                "folder": (
                    row.get("sync_folder")
                    or "None"
                ),
                "issues": issues,
                "primary_issue": issues[0],
                "additional_issue_count": max(0, len(issues) - 1),
                "latest_tag": row.get("latest_tag", ""),
            })

    attention.sort(
        key=lambda item: (
            item["online"],
            item["health_score"],
            item["name"].lower(),
        )
    )

    recent_failed = sorted(
        failed_jobs,
        key=lambda job: (
            job.get("updated_at")
            or job.get("created_at")
            or ""
        ),
        reverse=True,
    )[:8]

    return {
        "metrics": {
            "total": total,
            "online": online,
            "offline": offline,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "updates": updates,
            "sync_errors": sync_errors,
            "failed_jobs": len(failed_jobs),
            "active_jobs": len(active_jobs),
        },
        "rows": rows,
        "attention": attention,
        "active_jobs": active_jobs[:8],
        "failed_jobs": recent_failed,
    }
