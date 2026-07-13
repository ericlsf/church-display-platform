from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import (
    load_config,
    load_hub_settings,
    load_pending,
    normalize_display_id,
    normalize_host,
    save_config,
    save_pending,
)
from services.content_cache import sync_playlist_from_drive
from services.drive import list_drive_folders
from services.events import log_event
from services.jobs import create_job, list_jobs
from services.platform_admin import (
    mark_setup_complete,
    save_hub_settings,
    setup_complete,
)


setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


def _latest_provisioning_job(display_id):
    for job in list_jobs(250):
        if (
            job.get("display_id") == display_id
            and job.get("type") == "set_sync_folder"
        ):
            return job
    return None


def approve_pending_display(
    host,
    friendly_name="",
    requested_id="",
    initial_folder="",
):
    host = normalize_host(host)
    requested_id = normalize_display_id(requested_id)
    initial_folder = (initial_folder or "").strip().strip("/")

    if not host:
        return False, "The pending display host is missing."

    pending_data = load_pending()
    pending_displays = pending_data.get("pending", [])

    match = None
    for item in pending_displays:
        if normalize_host(item.get("host", "")) == host:
            match = item
            break

    if not match:
        return False, "The display is no longer waiting for approval."

    name = (
        (friendly_name or "").strip()
        or match.get("name", "").strip()
        or match.get("hostname", "").strip()
        or "Display"
    )

    display_id = normalize_display_id(
        requested_id
        or match.get("requested_id")
        or match.get("hostname")
        or name
    )

    cfg = load_config()
    displays = cfg.setdefault("displays", [])

    for display in displays:
        if display.get("id") == display_id:
            return (
                False,
                f"Display ID '{display_id}' is already in use. "
                "Choose a different ID.",
            )

    for display in displays:
        if normalize_host(display.get("host", "")) == host:
            return (
                False,
                "This display host is already approved under "
                f"ID '{display.get('id')}'.",
            )

    remote = load_hub_settings().get("drive_remote", "gdrive")

    display = {
        "id": display_id,
        "name": name,
        "host": host,
        "hostname": match.get("hostname", ""),
        "ip": match.get("ip", ""),
        "version": match.get("version", ""),
        "username": "",
        "password": "",
        "assigned_folder": initial_folder,
        "provisioning_status": (
            "sync_queued" if initial_folder else "needs_playlist"
        ),
    }

    displays.append(display)
    save_config(cfg)

    pending_data["pending"] = [
        item
        for item in pending_displays
        if normalize_host(item.get("host", "")) != host
    ]
    save_pending(pending_data)

    if initial_folder:
        manifest, error = sync_playlist_from_drive(remote, initial_folder)

        if error:
            display["provisioning_status"] = "cache_failed"
            save_config(cfg)
            log_event(
                f"Approved {name} as {display_id}, but initial Hub cache "
                f"sync failed for {remote}:{initial_folder}: {error}",
                level="error",
            )
            return (
                True,
                f"Display approved as {display_id}, but the Hub could not "
                f"prepare '{initial_folder}': {error}",
            )

        create_job(
            display_id,
            "set_sync_folder",
            {
                "remote": remote,
                "folder": initial_folder,
                "run_now": True,
                "source": "hub",
                "playlist_order": manifest.get("order", []),
            },
        )
        log_event(
            f"Approved {name} as {display_id}; initial playlist "
            f"{remote}:{initial_folder} queued"
        )
        return (
            True,
            f"Display approved as {display_id}. Initial playlist "
            f"'{initial_folder}' was queued.",
        )

    log_event(
        f"Approved {name} as {display_id} without an initial playlist"
    )
    return (
        True,
        f"Display approved as {display_id}, but it still needs a playlist.",
    )


@setup_bp.route("", methods=["GET", "POST"])
def setup_page():
    message = ""
    error = ""

    if request.method == "POST":
        settings = {
            "organization_name": (
                request.form.get("organization_name", "").strip()
                or "Church Display"
            ),
            "drive_remote": (
                request.form.get("drive_remote", "").strip()
                or "gdrive"
            ),
            "timezone": (
                request.form.get("timezone", "").strip()
                or "America/Chicago"
            ),
            "hub_url": request.form.get("hub_url", "").strip(),
        }

        try:
            save_hub_settings(settings)
            mark_setup_complete()
            log_event("Hub first-run settings saved")
            message = "Hub settings saved successfully."
        except Exception as exc:
            error = f"Could not save Hub settings: {exc}"

    settings = load_hub_settings()
    remote = settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)

    pending = load_pending().get("pending", [])
    displays = load_config().get("displays", [])

    display_rows = []
    for display in displays:
        job = _latest_provisioning_job(display.get("id"))
        row = dict(display)
        row["provisioning_job"] = job
        display_rows.append(row)

    return render_template(
        "setup.html",
        active="setup",
        setup_complete=setup_complete(),
        settings=settings,
        pending=pending,
        displays=display_rows,
        drive_folders=folders,
        drive_error=drive_error,
        message=message,
        error=error,
    )


@setup_bp.route("/approve", methods=["POST"])
def approve_display():
    success, message = approve_pending_display(
        request.form.get("host", ""),
        request.form.get("name", ""),
        request.form.get("display_id", ""),
        request.form.get("initial_folder", ""),
    )

    flash(message, "success" if success else "error")
    return redirect(url_for("setup.setup_page"))


@setup_bp.route("/ignore", methods=["POST"])
def ignore_display():
    host = normalize_host(request.form.get("host", ""))

    if host:
        pending_data = load_pending()
        pending_data["pending"] = [
            item
            for item in pending_data.get("pending", [])
            if normalize_host(item.get("host", "")) != host
        ]
        save_pending(pending_data)
        log_event(f"Ignored discovered display at {host} during setup")

    return redirect(url_for("setup.setup_page"))


@setup_bp.route("/finish", methods=["POST"])
def finish_setup():
    mark_setup_complete()
    log_event("First-run setup completed")
    return redirect(url_for("dashboard.dashboard"))
