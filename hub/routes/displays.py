from flask import Blueprint, redirect, render_template, request, url_for
from services.config import load_config, save_config, slugify, normalize_host
from services.display_client import test_display
from services.events import log_event

displays_bp = Blueprint("displays", __name__, url_prefix="/displays")


@displays_bp.route("")
def displays():
    cfg = load_config()
    rows = []
    for display in cfg.get("displays", []):
        ok, result = test_display(display.get("host", ""), display.get("username", ""), display.get("password", ""))
        rows.append({"id": display.get("id", ""), "name": display.get("name", ""), "host": display.get("host", ""), "username": display.get("username", ""), "password": display.get("password", ""), "online": ok, "message": "Online" if ok else result})
    return render_template("displays.html", rows=rows, test_message="", active="displays")


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
    cfg["displays"].append({"id": display_id, "name": name, "host": host, "username": username, "password": password})
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
    cfg = load_config()
    rows = []
    for display in cfg.get("displays", []):
        row_ok, row_result = test_display(display.get("host", ""), display.get("username", ""), display.get("password", ""))
        rows.append({"id": display.get("id", ""), "name": display.get("name", ""), "host": display.get("host", ""), "username": display.get("username", ""), "password": display.get("password", ""), "online": row_ok, "message": "Online" if row_ok else row_result})
    return render_template("displays.html", rows=rows, test_message=message, active="displays")
