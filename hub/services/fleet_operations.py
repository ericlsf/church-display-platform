from services.config import load_config
from services.fleet_state import build_fleet_state
from services.jobs import create_job
from services.display_artifacts import create_artifact
from services.config import load_hub_settings


def fleet_rows():
    config = load_config()
    state = build_fleet_state()
    state_rows = {
        row.get("id"): row
        for row in state.get("rows", [])
    }

    rows = []
    for display in config.get("displays", []):
        display_id = display.get("id", "")
        health = state_rows.get(display_id, {})
        version = (
            health.get("version")
            or display.get("version")
            or "unknown"
        )

        assigned_folder = (
            display.get("assigned_folder")
            or display.get("sync_folder")
            or ""
        )

        media_count = int(
            health.get("media_count")
            or health.get("media", {}).get("total", 0)
            if isinstance(health.get("media"), dict)
            else 0
        )

        online = bool(health.get("online", False))
        player_running = bool(
            health.get("display_app_running")
            or health.get("player_running")
        )
        sync_ok = bool(
            health.get("sync_state") == "success"
            or health.get("last_sync_status") == "success"
        )

        checks = {
            "online": online,
            "player": player_running,
            "playlist": bool(assigned_folder),
            "media": media_count > 0,
            "sync": sync_ok,
        }
        score = round(
            sum(1 for value in checks.values() if value)
            / len(checks)
            * 100
        )

        if all(checks.values()):
            readiness = "ready"
        elif not online:
            readiness = "offline"
        elif not assigned_folder:
            readiness = "needs_playlist"
        elif not player_running or not sync_ok:
            readiness = "needs_attention"
        else:
            readiness = "provisioning"

        rows.append({
            **display,
            **health,
            "id": display_id,
            "version": version,
            "assigned_folder": assigned_folder,
            "media_count": media_count,
            "health_score": score,
            "readiness": readiness,
            "checks": checks,
        })

    return rows


def _package_url(sha256):
    hub_url = (
        load_hub_settings().get("hub_url")
        or "http://church-display-hub.local:8090"
    ).rstrip("/")
    return (
        f"{hub_url}/api/v1/display-releases/"
        f"artifacts/{sha256}.tar.gz"
    )


def queue_bulk_action(display_ids, action, payload=None):
    payload = payload or {}
    queued = []

    if action == "deploy_update":
        target = (payload.get("target") or "").strip()
        if not target:
            raise ValueError("A target version is required")

        artifact = create_artifact(target)
        common = {
            "target": target,
            "dry_run": payload.get("dry_run", "true"),
            "package_url": _package_url(artifact["sha256"]),
            "sha256": artifact["sha256"],
            "commit": artifact.get("commit", ""),
            "package_size": artifact["size"],
            "deployment_mode": "immutable_hub_artifact",
        }

        for display_id in display_ids:
            queued.append(
                create_job(
                    display_id,
                    "deploy_update",
                    dict(common),
                )
            )
        return queued

    for display_id in display_ids:
        if action == "sync_now":
            queued.append(create_job(display_id, "sync_now", {}))
        elif action == "restart_display":
            queued.append(create_job(display_id, "restart_display", {}))
        elif action == "apply_display_settings":
            queued.append(
                create_job(
                    display_id,
                    "apply_display_settings",
                    {
                        "settings": payload.get("settings", {}),
                    },
                )
            )
        else:
            raise ValueError(f"Unsupported bulk action: {action}")

    return queued
