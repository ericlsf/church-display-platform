from flask import Blueprint, redirect, render_template, request, url_for

from services.config import (
    load_config,
    load_hub_settings,
    load_pending,
    normalize_host,
    save_config,
    save_pending,
    slugify,
)
from services.events import log_event
from services.platform_admin import (
    mark_setup_complete,
    save_hub_settings,
    setup_complete,
)


setup_bp = Blueprint("setup", __name__, url_prefix="/setup")


def approve_pending_display(host: str, friendly_name: str = "") -> bool:
    """Approve one pending display and add it to displays.json."""
    host = normalize_host(host)

    if not host:
        return False

    pending_data = load_pending()
    pending_displays = pending_data.get("pending", [])

    match = None

    for item in pending_displays:
        if normalize_host(item.get("host", "")) == host:
            match = item
            break

    if not match:
        return False

    config = load_config()
    displays = config.setdefault("displays", [])

    # Do not add the same host twice.
    for display in displays:
        if normalize_host(display.get("host", "")) == host:
            pending_data["pending"] = [
                item
                for item in pending_displays
                if normalize_host(item.get("host", "")) != host
            ]
            save_pending(pending_data)
            return True

    name = (
        friendly_name.strip()
        or match.get("name", "").strip()
        or match.get("hostname", "").strip()
        or "Display"
    )

    existing_ids = {
        display.get("id")
        for display in displays
        if display.get("id")
    }

    base_id = slugify(name)
    display_id = base_id
    counter = 2

    while display_id in existing_ids:
        display_id = f"{base_id}-{counter}"
        counter += 1

    displays.append(
        {
            "id": display_id,
            "name": name,
            "host": host,
            "username": "",
            "password": "",
        }
    )

    save_config(config)

    pending_data["pending"] = [
        item
        for item in pending_displays
        if normalize_host(item.get("host", "")) != host
    ]
    save_pending(pending_data)

    log_event(f"Approved discovered display {name} at {host} during setup")
    return True


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
    pending = load_pending().get("pending", [])
    displays = load_config().get("displays", [])

    return render_template(
        "setup.html",
        active="setup",
        setup_complete=setup_complete(),
        settings=settings,
        pending=pending,
        displays=displays,
        message=message,
        error=error,
    )


@setup_bp.route("/approve", methods=["POST"])
def approve_display():
    host = request.form.get("host", "")
    friendly_name = request.form.get("name", "")

    if approve_pending_display(host, friendly_name):
        return redirect(url_for("setup.setup_page", approved="1"))

    return redirect(url_for("setup.setup_page", approval_error="1"))


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
