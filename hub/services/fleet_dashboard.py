"""Fleet-level operational summary for the Hub landing page."""

from __future__ import annotations

from services.fleet_operations import fleet_rows
from services.jobs import list_jobs


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
        if str(row.get("sync_state", "")).lower()
        not in {"success", "completed", "complete", "ok", ""}
    )

    failed_jobs = [
        job
        for job in jobs
        if str(job.get("status", "")).lower()
        in FAILED_JOB_STATES
        and not job.get("resolved")
    ]
    active_jobs = [
        job
        for job in jobs
        if str(job.get("status", "")).lower()
        in ACTIVE_JOB_STATES
    ]

    attention = []

    for row in rows:
        reasons = []

        if not (
            row.get("online")
            or row.get("status_online")
        ):
            reasons.append("Offline")

        if int(row.get("health_score", 0) or 0) < 100:
            failed_checks = [
                label
                for key, label in (
                    ("online", "Hub connection"),
                    ("player", "Player stopped"),
                    ("playlist", "No content assigned"),
                    ("media", "No local media"),
                    ("sync", "Sync incomplete"),
                )
                if not (row.get("checks", {}) or {}).get(key, False)
            ]
            reasons.extend(
                failed_checks
                or [f'Health {int(row.get("health_score", 0) or 0)}%']
            )

        if row.get("update_available"):
            reasons.append("Display software update")

        sync_state = str(
            row.get("sync_state", "")
        ).strip().lower()

        if sync_state not in {
            "",
            "success",
            "completed",
            "complete",
            "ok",
        }:
            reasons.append(
                f"Sync {sync_state}"
            )

        if reasons:
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
                "reasons": reasons,
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
