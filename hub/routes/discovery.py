from datetime import datetime
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from services.config import load_config, save_config, load_pending, save_pending, slugify, normalize_host
from services.events import log_event

discovery_bp = Blueprint("discovery", __name__, url_prefix="/discovery")


@discovery_bp.route("")
def discovery():
    data = load_pending()
    return render_template("discovery.html", pending=data.get("pending", []), active="discovery")


@discovery_bp.route("/register", methods=["POST"])
def register_display():
    payload = request.get_json(silent=True) or request.form.to_dict()
    host = normalize_host(payload.get("host", ""))
    name = (payload.get("name") or payload.get("hostname") or "New Display").strip()
    hostname = (payload.get("hostname") or "").strip()
    version = (payload.get("version") or "").strip()
    ip = (payload.get("ip") or "").strip()
    if not host:
        return jsonify({"ok": False, "error": "missing host"}), 400
    cfg = load_config()
    for display in cfg.get("displays", []):
        if normalize_host(display.get("host", "")) == host:
            return jsonify({"ok": True, "status": "already-approved"})
    data = load_pending()
    pending = data.setdefault("pending", [])
    existing = None
    for item in pending:
        if normalize_host(item.get("host", "")) == host:
            existing = item
            break
    item = {"name": name, "host": host, "hostname": hostname, "ip": ip, "version": version, "last_seen": datetime.now().isoformat(timespec="seconds")}
    if existing:
        existing.update(item)
    else:
        pending.append(item)
        log_event(f"New display discovered: {name} at {host}")
    save_pending(data)
    return jsonify({"ok": True, "status": "pending"})


@discovery_bp.route("/approve", methods=["POST"])
def approve_display():
    host = normalize_host(request.form.get("host", ""))
    friendly_name = request.form.get("name", "").strip()
    data = load_pending()
    pending = data.get("pending", [])
    match = None
    for item in pending:
        if normalize_host(item.get("host", "")) == host:
            match = item
            break
    if not match:
        return redirect(url_for("discovery.discovery"))
    name = friendly_name or match.get("name", "Display")
    cfg = load_config()
    existing_ids = {d.get("id") for d in cfg.get("displays", [])}
    base_id = slugify(name)
    display_id = base_id
    counter = 2
    while display_id in existing_ids:
        display_id = f"{base_id}-{counter}"
        counter += 1
    cfg["displays"].append({"id": display_id, "name": name, "host": host, "username": "", "password": ""})
    save_config(cfg)
    data["pending"] = [p for p in pending if normalize_host(p.get("host", "")) != host]
    save_pending(data)
    log_event(f"Approved discovered display {name} at {host}")
    return redirect(url_for("discovery.discovery"))


@discovery_bp.route("/ignore", methods=["POST"])
def ignore_display():
    host = normalize_host(request.form.get("host", ""))
    data = load_pending()
    data["pending"] = [p for p in data.get("pending", []) if normalize_host(p.get("host", "")) != host]
    save_pending(data)
    log_event(f"Ignored discovered display at {host}")
    return redirect(url_for("discovery.discovery"))
