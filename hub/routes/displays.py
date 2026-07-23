from flask import Blueprint, redirect, render_template, request, url_for
from services.config import load_config, save_config, slugify, normalize_host
from services.display_client import test_display
from services.events import log_event
from services.fleet_state import build_fleet_state

displays_bp = Blueprint("displays", __name__, url_prefix="/displays")


def render_fleet_overview(test_message=""):
    cfg = load_config()
    configured = {display.get("id", ""): display for display in cfg.get("displays", [])}
    state = build_fleet_state()
    rows = []
    for row in state.get("rows", []):
        display = configured.get(row.get("id", ""), {})
        rows.append({
            **row,
            "username": display.get("username", ""),
            "password": display.get("password", ""),
        })
    return render_template(
        "displays.html",
        rows=rows,
        groups=sorted({row.get("group") for row in rows if row.get("group")}),
        alerts=state.get("alerts", []),
        notifications=state.get("notifications", []),
        event_records=state.get("event_records", []),
        latest_tag=state.get("latest_tag", ""),
        test_message=test_message,
        active="displays",
    )


@displays_bp.route("")
def displays():
    return render_fleet_overview()


@displays_bp.route("/add", methods=["POST"])
def add_display():
    cfg = load_config()
    name = request.form.get("name", "").strip()
    host = normalize_host(request.form.get("host", ""))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    group = request.form.get("group", "").strip()
    if not name or not host:
        return redirect(url_for("displays.displays"))
    existing_ids = {d.get("id") for d in cfg.get("displays", [])}
    base_id = slugify(name)
    display_id = base_id
    counter = 2
    while display_id in existing_ids:
        display_id = f"{base_id}-{counter}"
        counter += 1
    cfg["displays"].append({"id": display_id, "name": name, "host": host, "username": username, "password": password, "group": group})
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
    group = request.form.get("group", "").strip()
    for display in cfg.get("displays", []):
        if display.get("id") == display_id:
            if name:
                display["name"] = name
            if host:
                display["host"] = host
            display["username"] = username
            display["password"] = password
            display["group"] = group
            log_event(f"Updated display {display.get('name', display_id)}")
            break
    save_config(cfg)
    return redirect(url_for("displays.displays"))


@displays_bp.route("/remove", methods=["POST"])
def remove_display():
    cfg = load_config()
    display_id = request.form.get("id", "")
    cfg["displays"] = [d for d in cfg.get("displays", []) if d.get("id") != display_id]
    save_config(cfg)
    log_event(f"Removed display {display_id}")
    return redirect(url_for("displays.displays"))


@displays_bp.route("/test", methods=["POST"])
def test_display_route():
    host = normalize_host(request.form.get("host", ""))
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    ok, result = test_display(host, username, password)
    message = "Display is online and responding." if ok else f"Display test failed: {result}"
    return render_fleet_overview(message)
