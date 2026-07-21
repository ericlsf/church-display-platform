from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from services.config import load_config, save_config, slugify, normalize_host
from services.display_client import test_display
from services.events import log_event
from services.fleet_state import build_fleet_state
from services.groups import list_groups, update_group
from services.display_profiles import apply_profile, load_profiles
from services.media_index import cached_drive_folders
from services.config import load_hub_settings
from services.jobs import create_job, list_jobs


displays_bp = Blueprint("displays", __name__, url_prefix="/displays")


def _bool_form(name):
    return request.form.get(name) in {"1", "true", "yes", "on"}


def _presentation_defaults(display):
    settings = display.setdefault("presentation", {})
    overlay = settings.setdefault("overlay", {})
    overlay.setdefault("enabled", True)
    overlay.setdefault("text", "Welcome")

    clock = settings.setdefault("clock", {})
    clock.setdefault("enabled", True)

    countdown = settings.setdefault("countdown", {})
    countdown.setdefault("enabled", True)
    countdown.setdefault("start_minutes", 20)

    timings = settings.setdefault("timings", {})
    timings.setdefault("image_duration", 8)

    return settings


def _display_job_summary(display_id, jobs):
    active = [
        job for job in jobs
        if job.get("display_id") in {display_id, "all"}
        and job.get("status") in {"queued", "running"}
    ]
    failed = [
        job for job in jobs
        if job.get("display_id") in {display_id, "all"}
        and job.get("status") in {"failed", "timed_out"}
        and not job.get("acknowledged")
    ]
    current = active[0] if active else None
    return {
        "active_count": len(active),
        "failed_count": len(failed),
        "status": current.get("status", "idle") if current else "idle",
        "type": current.get("type", "") if current else "",
        "progress": current.get("progress", 0) if current else 0,
        "message": current.get("message", "") if current else "",
    }


def _system_value(system, *keys, default="Unknown"):
    for key in keys:
        value = system.get(key)
        if value not in (None, ""):
            return value
    return default

def display_rows(test_message=""):
    cfg = load_config()
    fleet_rows = {
        row.get("id"): row
        for row in build_fleet_state().get("rows", [])
    }
    rows = []
    jobs = list_jobs(limit=500)

    for display in cfg.get("displays", []):
        display_id = display.get("id", "")
        fleet = fleet_rows.get(display_id, {})
        presentation = _presentation_defaults(display)
        system = fleet.get("system", {}) or {}
        job_summary = _display_job_summary(display_id, jobs)
        attention = (
            not fleet.get("online", False)
            or not fleet.get("display_app_running", False)
            or str(fleet.get("sync_state", "")).lower() == "error"
            or bool(fleet.get("update_available"))
            or job_summary["failed_count"] > 0
        )

        rows.append({
            "id": display_id,
            "name": display.get("name", ""),
            "host": display.get("host", ""),
            "username": display.get("username", ""),
            "password": display.get("password", ""),
            "online": fleet.get("online", False),
            "message": fleet.get("error", "") or (
                "Online" if fleet.get("online") else "No recent heartbeat"
            ),
            "heartbeat_fresh": fleet.get("heartbeat_fresh", False),
            "display_app_running": fleet.get("display_app_running", False),
            "display_app_state": fleet.get("display_app_state", "unknown"),
            "presentation": presentation,
            "sync_remote": "gdrive",
            "sync_folder": (
                display.get("assigned_folder")
                or display.get("sync_folder")
                or fleet.get("sync_folder")
                or ""
            ),
            "profile_id": display.get("profile_id", ""),
            "version": fleet.get("current_tag") or fleet.get("version", "Unknown"),
            "heartbeat": fleet.get("heartbeat_age") or fleet.get("heartbeat", "Unknown"),
            "current_media": fleet.get("current_media", "Unknown"),
            "media_count": fleet.get("media_count", 0),
            "sync_state": fleet.get("sync_state", "unknown"),
            "preview_url": fleet.get("preview_url", ""),
            "update_available": bool(fleet.get("update_available")),
            "latest_tag": fleet.get("latest_tag", "Unknown"),
            "cpu_temp": _system_value(system, "cpu_temp", "temperature"),
            "disk_usage": _system_value(system, "disk_usage", "disk_percent", "storage_usage", "disk"),
            "memory_usage": _system_value(system, "memory_usage", "memory_percent", "ram_usage", "memory"),
            "ip_address": _system_value(system, "ip_address", "ip", "address", default=""),
            "job": job_summary,
            "attention": attention,
        })

    save_config(cfg)
    return rows, test_message


@displays_bp.route("")
def displays():
    rows, message = display_rows()
    settings = load_hub_settings()
    remote = settings.get("drive_remote", "gdrive")
    folders, media_index = cached_drive_folders(remote)
    groups = list_groups()
    profiles_data = load_profiles()

    memberships = {}
    for group in groups:
        for display_id in group.get("display_ids", []):
            memberships.setdefault(display_id, []).append(group.get("id"))

    for row in rows:
        row["group_ids"] = memberships.get(row.get("id"), [])
        current = row.get("sync_folder", "")
        row["folder_options"] = list(folders)
        if current and current not in row["folder_options"]:
            row["folder_options"].insert(0, current)

    return render_template(
        "displays.html",
        rows=rows,
        test_message=message,
        active="displays",
        groups=groups,
        profiles=profiles_data.get("profiles", []),
        drive_remote="gdrive",
        folder_options=folders,
        media_index=media_index,
    )


@displays_bp.route("/api/status")
def display_status_api():
    """Return lightweight live fleet state without touching Google Drive."""
    rows, _ = display_rows()
    payload = []
    for row in rows:
        payload.append({
            "id": row.get("id", ""),
            "online": bool(row.get("online")),
            "heartbeat": row.get("heartbeat", "Unknown"),
            "version": row.get("version", "Unknown"),
            "current_media": row.get("current_media", "Unknown"),
            "media_count": row.get("media_count", 0),
            "sync_state": row.get("sync_state", "unknown"),
            "display_app_running": bool(row.get("display_app_running")),
            "display_app_state": row.get("display_app_state", "unknown"),
            "update_available": bool(row.get("update_available")),
            "latest_tag": row.get("latest_tag", "Unknown"),
            "cpu_temp": row.get("cpu_temp", "Unknown"),
            "disk_usage": row.get("disk_usage", "Unknown"),
            "memory_usage": row.get("memory_usage", "Unknown"),
            "job": row.get("job", {}),
            "attention": bool(row.get("attention")),
            "preview_url": row.get("preview_url", ""),
        })
    return jsonify({
        "ok": True,
        "online": sum(1 for row in payload if row["online"]),
        "offline": sum(1 for row in payload if not row["online"]),
        "attention": sum(1 for row in payload if row["attention"]),
        "active_jobs": sum(row.get("job", {}).get("active_count", 0) for row in payload),
        "rows": payload,
    })


@displays_bp.route("/add", methods=["POST"])
def add_display():
    cfg = load_config()
    name = request.form.get("name", "").strip()
    host = normalize_host(request.form.get("host", ""))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not host:
        return redirect(url_for("displays.displays"))

    existing_ids = {d.get("id") for d in cfg.get("displays", [])}
    base_id = slugify(name)
    display_id = base_id
    counter = 2

    while display_id in existing_ids:
        display_id = f"{base_id}-{counter}"
        counter += 1

    cfg["displays"].append({
        "id": display_id,
        "name": name,
        "host": host,
        "username": username,
        "password": password,
        "presentation": {
            "overlay": {"enabled": True, "text": "Welcome"},
            "clock": {"enabled": True},
            "countdown": {"enabled": True, "start_minutes": 20},
            "timings": {"image_duration": 8},
        },
    })
    save_config(cfg)
    log_event(f"Added display {name} at {host}")
    return redirect(url_for("displays.displays"))


@displays_bp.route("/update", methods=["POST"])
def update_display():
    cfg = load_config()
    display_id = request.form.get("id", "")
    name = request.form.get("name", "").strip()
    host = normalize_host(request.form.get("host", ""))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    for display in cfg.get("displays", []):
        if display.get("id") == display_id:
            if name:
                display["name"] = name
            if host:
                display["host"] = host
            display["username"] = username
            display["password"] = password
            log_event(f"Updated display {display.get('name', display_id)}")
            break

    save_config(cfg)
    return redirect(url_for("displays.displays"))


@displays_bp.route("/presentation", methods=["POST"])
def update_presentation():
    cfg = load_config()
    display_id = request.form.get("id", "").strip()
    display = next(
        (d for d in cfg.get("displays", []) if d.get("id") == display_id),
        None,
    )

    if not display:
        flash("Display not found.", "error")
        return redirect(url_for("displays.displays"))

    try:
        start_minutes = max(
            0,
            min(180, int(request.form.get("countdown_start_minutes", "20"))),
        )
        image_duration = max(
            1,
            min(300, int(request.form.get("image_duration", "8"))),
        )
    except ValueError:
        flash("Countdown and image duration must be whole numbers.", "error")
        return redirect(url_for("displays.displays"))

    settings = {
        "overlay": {
            "enabled": _bool_form("overlay_enabled"),
            "text": request.form.get("overlay_text", "").strip(),
        },
        "clock": {
            "enabled": _bool_form("clock_enabled"),
        },
        "countdown": {
            "enabled": _bool_form("countdown_enabled"),
            "start_minutes": start_minutes,
        },
        "timings": {
            "image_duration": image_duration,
        },
    }

    display["presentation"] = settings
    save_config(cfg)

    create_job(
        display_id,
        "apply_display_settings",
        {"settings": settings},
        max_attempts=3,
        timeout_seconds=120,
    )

    log_event(
        f"Queued presentation settings for "
        f"{display.get('name', display_id)}"
    )
    flash(
        f"Presentation settings queued for "
        f"{display.get('name', display_id)}.",
        "success",
    )
    return redirect(url_for("displays.displays"))


@displays_bp.route("/<display_id>/workspace", methods=["POST"])
def update_workspace(display_id):
    cfg = load_config()
    display = next(
        (item for item in cfg.get("displays", []) if item.get("id") == display_id),
        None,
    )
    if not display:
        flash("Display not found.", "error")
        return redirect(url_for("displays.displays"))

    remote = "gdrive"
    folder = request.form.get("sync_folder", "").strip().strip("/")
    profile_id = request.form.get("profile_id", "").strip()
    selected_groups = set(request.form.getlist("group_ids"))
    run_now = request.form.get("run_now") == "1"

    previous_folder = (
        display.get("assigned_folder")
        or display.get("sync_folder")
        or ""
    )
    if folder:
        display["sync_remote"] = remote
        display["sync_folder"] = folder
        display["assigned_folder"] = folder
        if folder != previous_folder or run_now:
            create_job(
                display_id,
                "set_sync_folder",
                {"remote": remote, "folder": folder, "run_now": run_now},
            )

    if profile_id:
        apply_profile(profile_id, display_ids=[display_id])
        display["profile_id"] = profile_id
    elif request.form.get("profile_submitted") == "1":
        display["profile_id"] = ""

    save_config(cfg)

    for group in list_groups():
        members = list(group.get("display_ids", []))
        has_display = display_id in members
        should_have = group.get("id") in selected_groups
        if should_have and not has_display:
            members.append(display_id)
        elif has_display and not should_have:
            members = [item for item in members if item != display_id]
        else:
            continue
        update_group(
            group.get("id"),
            group.get("name", "Group"),
            group.get("description", ""),
            members,
        )

    log_event(f"Updated management assignments for {display.get('name', display_id)}")
    flash(f"Updated {display.get('name', display_id)} assignments.", "success")
    return redirect(url_for("displays.displays"))


@displays_bp.route("/bulk-workspace", methods=["POST"])
def bulk_workspace():
    display_ids = [item for item in request.form.getlist("display_ids") if item]
    if not display_ids:
        flash("Select at least one display.", "error")
        return redirect(url_for("displays.displays"))

    cfg = load_config()
    displays_by_id = {
        item.get("id"): item
        for item in cfg.get("displays", [])
        if item.get("id") in display_ids
    }
    folder = request.form.get("sync_folder", "").strip().strip("/")
    profile_id = request.form.get("profile_id", "").strip()
    group_action = request.form.get("group_action", "keep")
    selected_groups = set(request.form.getlist("group_ids"))
    run_now = request.form.get("run_now") == "1"

    for display_id, display in displays_by_id.items():
        if folder:
            previous = display.get("assigned_folder") or display.get("sync_folder") or ""
            display["sync_remote"] = "gdrive"
            display["sync_folder"] = folder
            display["assigned_folder"] = folder
            if folder != previous or run_now:
                create_job(
                    display_id,
                    "set_sync_folder",
                    {"remote": "gdrive", "folder": folder, "run_now": run_now},
                )
        if profile_id:
            apply_profile(profile_id, display_ids=[display_id])
            display["profile_id"] = profile_id

    save_config(cfg)

    if group_action in {"add", "replace", "remove"}:
        for group in list_groups():
            group_id = group.get("id")
            members = set(group.get("display_ids", []))
            targeted = set(display_ids)
            if group_action == "add" and group_id in selected_groups:
                members |= targeted
            elif group_action == "remove" and group_id in selected_groups:
                members -= targeted
            elif group_action == "replace":
                members -= targeted
                if group_id in selected_groups:
                    members |= targeted
            else:
                continue
            update_group(
                group_id,
                group.get("name", "Group"),
                group.get("description", ""),
                sorted(members),
            )

    log_event(f"Updated assignments for {len(displays_by_id)} displays")
    flash(f"Updated {len(displays_by_id)} displays.", "success")
    return redirect(url_for("displays.displays"))


@displays_bp.route("/remove", methods=["POST"])
def remove_display():
    cfg = load_config()
    display_id = request.form.get("id", "")
    cfg["displays"] = [
        d for d in cfg.get("displays", [])
        if d.get("id") != display_id
    ]
    save_config(cfg)
    log_event(f"Removed display {display_id}")
    return redirect(url_for("displays.displays"))


@displays_bp.route("/test", methods=["POST"])
def test_display_route():
    host = normalize_host(request.form.get("host", ""))
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    ok, result = test_display(host, username, password)
    message = (
        "Display is online and responding."
        if ok
        else f"Display test failed: {result}"
    )
    rows, _ = display_rows(message)
    return render_template(
        "displays.html",
        rows=rows,
        test_message=message,
        active="displays",
    )
