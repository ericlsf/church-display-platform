from flask import Blueprint, redirect, request, url_for
from services.config import get_display, load_config
from services.display_client import set_sync_folder, sync_now, restart_display, reboot_display
from services.events import log_event

fleet_bp = Blueprint("fleet", __name__, url_prefix="/fleet")


@fleet_bp.route("/<display_id>/set-sync", methods=["POST"])
def fleet_set_sync(display_id):
    display = get_display(display_id)
    if not display:
        return redirect(url_for("dashboard.dashboard"))
    remote = request.form.get("sync_remote", "gdrive").strip() or "gdrive"
    folder = request.form.get("sync_folder", "Weekly").strip() or "Weekly"
    run_now = request.form.get("run_now") == "1"
    set_sync_folder(display, remote, folder)
    log_event(f"{display.get('name', display_id)} sync folder set to {folder}")
    if run_now:
        sync_now(display)
        log_event(f"{display.get('name', display_id)} sync started")
    return redirect(url_for("dashboard.dashboard"))


@fleet_bp.route("/<display_id>/sync-now", methods=["POST"])
def fleet_sync_now(display_id):
    display = get_display(display_id)
    if display:
        sync_now(display)
        log_event(f"{display.get('name', display_id)} sync started")
    return redirect(url_for("dashboard.dashboard"))


@fleet_bp.route("/<display_id>/restart", methods=["POST"])
def fleet_restart(display_id):
    display = get_display(display_id)
    if display:
        restart_display(display)
        log_event(f"{display.get('name', display_id)} restart requested")
    return redirect(url_for("dashboard.dashboard"))


@fleet_bp.route("/<display_id>/reboot", methods=["POST"])
def fleet_reboot(display_id):
    display = get_display(display_id)
    if display:
        reboot_display(display)
        log_event(f"{display.get('name', display_id)} reboot requested")
    return redirect(url_for("dashboard.dashboard"))


@fleet_bp.route("/bulk/set-sync", methods=["POST"])
def bulk_set_sync():
    ids = request.form.getlist("display_ids")
    remote = request.form.get("sync_remote", "gdrive").strip() or "gdrive"
    folder = request.form.get("sync_folder", "Weekly").strip() or "Weekly"
    run_now = request.form.get("run_now") == "1"
    cfg = load_config()
    for display in cfg.get("displays", []):
        if display.get("id") in ids:
            set_sync_folder(display, remote, folder)
            log_event(f"{display.get('name')} sync folder set to {folder}")
            if run_now:
                sync_now(display)
                log_event(f"{display.get('name')} sync started")
    return redirect(url_for("dashboard.dashboard"))


@fleet_bp.route("/bulk/sync-now", methods=["POST"])
def bulk_sync_now():
    ids = request.form.getlist("display_ids")
    cfg = load_config()
    for display in cfg.get("displays", []):
        if display.get("id") in ids:
            sync_now(display)
            log_event(f"{display.get('name')} sync started")
    return redirect(url_for("dashboard.dashboard"))


@fleet_bp.route("/bulk/restart", methods=["POST"])
def bulk_restart():
    ids = request.form.getlist("display_ids")
    cfg = load_config()
    for display in cfg.get("displays", []):
        if display.get("id") in ids:
            restart_display(display)
            log_event(f"{display.get('name')} restart requested")
    return redirect(url_for("dashboard.dashboard"))
