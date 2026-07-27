import time

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, session, url_for

from services.auth import authenticate, role_required
from services.config import load_config
from services.events import log_event
from services.jobs import create_job, list_jobs
from services.remote_terminal import get_session, list_sessions, start_hub_command

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")
UNLOCK_SECONDS = 10 * 60


def _terminal_unlocked():
    return float(session.get("terminal_unlocked_until", 0)) > time.time()


def _require_unlocked():
    if not _terminal_unlocked():
        abort(403)


@maintenance_bp.route("")
@role_required("admin")
def maintenance_page():
    displays = [
        item for item in load_config().get("displays", [])
        if item.get("device_role", item.get("role", "display")) != "controller"
    ]
    remote_jobs = [job for job in list_jobs(100) if job.get("type") == "remote_command"][:20]
    return render_template(
        "maintenance.html", active="maintenance", unlocked=_terminal_unlocked(),
        displays=displays, sessions=list_sessions(), remote_jobs=remote_jobs,
    )


@maintenance_bp.route("/unlock", methods=["POST"])
@role_required("admin")
def unlock_terminal():
    user = authenticate(g.current_user.get("username"), request.form.get("password", ""))
    if not user:
        flash("Password verification failed.", "error")
        return redirect(url_for("maintenance.maintenance_page"))
    session["terminal_unlocked_until"] = time.time() + UNLOCK_SECONDS
    log_event(f"Remote terminal unlocked by {g.current_user.get('username')}", category="security")
    flash("Remote terminal unlocked for 10 minutes.", "success")
    return redirect(url_for("maintenance.maintenance_page"))


@maintenance_bp.route("/lock", methods=["POST"])
@role_required("admin")
def lock_terminal():
    session.pop("terminal_unlocked_until", None)
    flash("Remote terminal locked.", "success")
    return redirect(url_for("maintenance.maintenance_page"))


@maintenance_bp.route("/hub/run", methods=["POST"])
@role_required("admin")
def run_hub_command():
    _require_unlocked()
    command = request.form.get("command", "")
    try:
        terminal_session = start_hub_command(
            command, g.current_user.get("username", "admin"),
            cwd=request.form.get("cwd", "") or None,
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    log_event(
        f"Remote Hub command started by {g.current_user.get('username')}",
        category="security",
        metadata={"terminal_session_id": terminal_session["id"], "command": command[:500]},
    )
    return jsonify({"ok": True, "session": terminal_session})


@maintenance_bp.route("/hub/update", methods=["POST"])
@role_required("admin")
def update_hub():
    _require_unlocked()
    terminal_session = start_hub_command(
        "sudo /usr/local/sbin/church-display-hub-update",
        g.current_user.get("username", "admin"),
    )
    log_event("Remote Hub update requested", category="security")
    return jsonify({"ok": True, "session": terminal_session})


@maintenance_bp.route("/hub/session/<session_id>")
@role_required("admin")
def hub_session(session_id):
    terminal_session = get_session(session_id)
    if not terminal_session:
        return jsonify({"ok": False, "error": "Session not found"}), 404
    return jsonify({"ok": True, "session": terminal_session})


@maintenance_bp.route("/display/run", methods=["POST"])
@role_required("admin")
def run_display_command():
    _require_unlocked()
    display_id = request.form.get("display_id", "").strip()
    command = request.form.get("command", "").strip()
    known_ids = {item.get("id") for item in load_config().get("displays", [])}
    if display_id not in known_ids or not command:
        return jsonify({"ok": False, "error": "Choose a display and enter a command."}), 400
    job = create_job(display_id, "remote_command", {"command": command}, max_attempts=1, timeout_seconds=900)
    log_event(
        f"Remote command queued for {display_id} by {g.current_user.get('username')}",
        category="security", metadata={"job_id": job["id"], "command": command[:500]},
    )
    return jsonify({"ok": True, "job": job})
