from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_config, save_config, slugify, normalize_host
from services.display_client import test_display
from services.events import log_event
from services.fleet_state import build_fleet_state
from services.groups import list_groups, update_group
from services.display_profiles import apply_profile, load_profiles
from services.media_index import cached_drive_folders
from services.config import load_hub_settings
from services.jobs import create_job


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


def display_rows(test_message=""):
    cfg = load_config()
    fleet_rows = {
        row.get("id"): row
        for row in build_fleet_state().get("rows", [])
    }
    rows = []

    for display in cfg.get("displays", []):
        display_id = display.get("id", "")
        fleet = fleet_rows.get(display_id, {})
        presentation = _presentation_defaults(display)

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
            "sync_remote": display.get("sync_remote", "gdrive"),
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
        drive_remote=remote,
        media_index=media_index,
    )


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

    remote = request.form.get("sync_remote", "gdrive").strip() or "gdrive"
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
