from services.config import load_config, load_hub_settings
from services.display_groups import group_members
from services.display_artifacts import create_artifact
from services.fleet_state import build_fleet_state
from services.jobs import create_job
from services.maintenance import in_maintenance
from services.telemetry_normalization import normalize_fleet_telemetry


def _fleet_rows_base():
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
        telemetry = normalize_fleet_telemetry(health, display)
        device_role = display.get("device_role", "display")
        controller = device_role == "controller"
        maintenance = display.get(
            "maintenance",
            {"enabled": False, "reason": ""},
        )

        version = telemetry["version"]
        assigned_folder = (
            display.get("assigned_folder")
            or display.get("sync_folder")
            or ""
        )

        media_count = telemetry["media_count"]

        online = bool(health.get("online", False))
        player_running = telemetry["player_running"]
        sync_ok = telemetry["sync_ok"]

        checks = ({"online": online} if controller else {
            "online": online,
            "player": player_running,
            "playlist": bool(assigned_folder),
            "media": media_count > 0,
            "sync": sync_ok,
        })
        score = round(
            sum(1 for value in checks.values() if value)
            / len(checks)
            * 100
        )

        if in_maintenance(display):
            readiness = "maintenance"
        elif all(checks.values()):
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
            "device_role": device_role,
            "version": version,
            "assigned_folder": assigned_folder,
            "media_count": media_count,
            "health_score": score,
            "readiness": readiness,
            "checks": checks,
            "maintenance": maintenance,
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


def resolve_targets(display_ids=None, group_ids=None):
    combined = list(display_ids or [])
    combined.extend(group_members(group_ids or []))

    result = []
    seen = set()
    for display_id in combined:
        display_id = str(display_id or "").strip()
        if not display_id or display_id in seen:
            continue
        seen.add(display_id)
        result.append(display_id)
    return result


def queue_bulk_action(
    display_ids,
    action,
    payload=None,
    group_ids=None,
    allow_maintenance=False,
):
    payload = payload or {}
    targets = resolve_targets(display_ids, group_ids)

    config = load_config()
    displays = {
        item.get("id"): item
        for item in config.get("displays", [])
    }

    blocked = []
    role_blocked = []
    eligible = []

    for display_id in targets:
        display = displays.get(display_id)
        if not display:
            continue

        if in_maintenance(display) and not allow_maintenance:
            blocked.append(display_id)
        elif display.get("device_role") == "controller":
            role_blocked.append(display_id)
        else:
            eligible.append(display_id)

    if not eligible and blocked and not role_blocked:
        raise ValueError(
            "All selected displays are in maintenance mode. "
            "Enable the maintenance override to continue."
        )
    if not eligible and role_blocked:
        raise ValueError(
            "The selected machines are controllers. Display actions only apply to display devices."
        )

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

        for display_id in eligible:
            queued.append(
                create_job(
                    display_id,
                    "deploy_update",
                    dict(common),
                )
            )
    else:
        for display_id in eligible:
            if action == "sync_now":
                queued.append(create_job(display_id, "sync_now", {}))
            elif action == "restart_display":
                queued.append(
                    create_job(display_id, "restart_display", {})
                )
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
                raise ValueError(
                    f"Unsupported bulk action: {action}"
                )

    return {
        "jobs": queued,
        "queued_display_ids": eligible,
        "blocked_display_ids": blocked,
        "role_blocked_display_ids": role_blocked,
    }


# v6.4.0 authoritative fleet-row wrapper
def fleet_rows(*args, **kwargs):
    from services.fleet_truth import enrich_fleet_rows

    return enrich_fleet_rows(
        _fleet_rows_base(*args, **kwargs)
    )
