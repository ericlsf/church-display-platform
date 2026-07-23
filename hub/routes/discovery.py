from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.config import (
    load_config,
    load_pending,
    normalize_display_id,
    normalize_host,
    save_config,
    save_pending,
)
from services.events import log_event


discovery_bp = Blueprint("discovery", __name__, url_prefix="/discovery")


def _requested_id(payload):
    return normalize_display_id(
        payload.get("id")
        or payload.get("display_id")
        or payload.get("hostname")
        or payload.get("name")
        or "display"
    )


@discovery_bp.route("")
def discovery():
    data = load_pending()
    return render_template(
        "discovery.html",
        pending=data.get("pending", []),
        active="discovery",
    )


@discovery_bp.route("/register", methods=["POST"])
def register_display():
    payload = request.get_json(silent=True) or request.form.to_dict()

    host = normalize_host(payload.get("host", ""))
    name = (
        payload.get("name")
        or payload.get("hostname")
        or "New Display"
    ).strip()
    hostname = (payload.get("hostname") or "").strip()
    version = (payload.get("version") or "").strip()
    ip = (payload.get("ip") or "").strip()
    requested_id = _requested_id(payload)

    if not host:
        return jsonify({"ok": False, "error": "missing host"}), 400

    cfg = load_config()

    for display in cfg.get("displays", []):
        same_host = normalize_host(display.get("host", "")) == host
        same_id = display.get("id") == requested_id

        if same_host or same_id:
            # Keep live metadata current without changing the stable ID.
            display.update({
                "host": host,
                "hostname": hostname or display.get("hostname", ""),
                "ip": ip or display.get("ip", ""),
                "version": version or display.get("version", ""),
            })
            save_config(cfg)

            return jsonify({
                "ok": True,
                "status": "approved",
                "display_id": display.get("id"),
                "name": display.get("name"),
                "assigned_folder": display.get("assigned_folder", ""),
            })

    data = load_pending()
    pending = data.setdefault("pending", [])

    existing = None
    for item in pending:
        if (
            normalize_host(item.get("host", "")) == host
            or item.get("requested_id") == requested_id
        ):
            existing = item
            break

    item = {
        "name": name,
        "requested_id": requested_id,
        "host": host,
        "hostname": hostname,
        "ip": ip,
        "version": version,
        "last_seen": datetime.now().isoformat(timespec="seconds"),
    }

    if existing:
        existing.update(item)
    else:
        pending.append(item)
        log_event(
            f"New display discovered: {name} "
            f"({requested_id}) at {host}"
        )

    save_pending(data)

    return jsonify({
        "ok": True,
        "status": "pending",
        "display_id": requested_id,
    })


@discovery_bp.route("/status")
def enrollment_status():
    requested_id = normalize_display_id(request.args.get("display_id", ""))
    host = normalize_host(request.args.get("host", ""))

    cfg = load_config()
    for display in cfg.get("displays", []):
        if (
            (requested_id and display.get("id") == requested_id)
            or (host and normalize_host(display.get("host", "")) == host)
        ):
            return jsonify({
                "ok": True,
                "status": "approved",
                "display_id": display.get("id"),
                "name": display.get("name"),
                "assigned_folder": display.get("assigned_folder", ""),
                "provisioning_status": display.get(
                    "provisioning_status",
                    "approved",
                ),
            })

    data = load_pending()
    for item in data.get("pending", []):
        if (
            (requested_id and item.get("requested_id") == requested_id)
            or (host and normalize_host(item.get("host", "")) == host)
        ):
            return jsonify({
                "ok": True,
                "status": "pending",
                "display_id": item.get("requested_id"),
            })

    return jsonify({"ok": True, "status": "unknown"})


@discovery_bp.route("/approve", methods=["POST"])
def approve_display():
    # The setup page is now the canonical approval workflow.
    return redirect(url_for("setup.setup_page"))


@discovery_bp.route("/ignore", methods=["POST"])
def ignore_display():
    host = normalize_host(request.form.get("host", ""))
    data = load_pending()
    data["pending"] = [
        item
        for item in data.get("pending", [])
        if normalize_host(item.get("host", "")) != host
    ]
    save_pending(data)
    log_event(f"Ignored discovered display at {host}")
    return redirect(url_for("discovery.discovery"))
