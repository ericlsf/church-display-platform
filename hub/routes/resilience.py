from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.events import log_event
from services.platform_admin import create_backup, list_backups, prune_backups
from services.resilience import load_resilience, save_resilience, set_maintenance

resilience_bp = Blueprint("resilience", __name__, url_prefix="/resilience")


def as_bool(name):
    return request.form.get(name) == "1"


def as_int(name, default, minimum=0, maximum=100000):
    try:
        value = int(request.form.get(name, default))
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


@resilience_bp.route("")
def resilience_page():
    return render_template(
        "resilience.html",
        active="resilience",
        settings=load_resilience(),
        backups=list_backups(),
    )


@resilience_bp.route("/maintenance", methods=["POST"])
def update_maintenance():
    enabled = as_bool("enabled")
    set_maintenance(enabled, request.form.get("message", ""))
    log_event(f"Maintenance mode {'enabled' if enabled else 'disabled'}")
    flash(f"Maintenance mode {'enabled' if enabled else 'disabled'}.", "success")
    return redirect(url_for("resilience.resilience_page"))


@resilience_bp.route("/policy", methods=["POST"])
def update_policy():
    data = load_resilience()
    data["recovery"].update({
        "enabled": as_bool("recovery_enabled"),
        "display_failure_threshold": as_int("display_failure_threshold", 2, 1, 20),
        "restart_cooldown_seconds": as_int("restart_cooldown_seconds", 300, 30, 86400),
        "max_restart_attempts": as_int("max_restart_attempts", 3, 1, 20),
        "allow_reboot": as_bool("allow_reboot"),
        "sync_repair_enabled": as_bool("sync_repair_enabled"),
        "sync_failure_threshold": as_int("sync_failure_threshold", 2, 1, 20),
    })
    data["backups"].update({
        "enabled": as_bool("backup_enabled"),
        "include_media": as_bool("backup_include_media"),
        "retain": as_int("backup_retain", 6, 1, 52),
        "interval_days": 14,
    })
    save_resilience(data)
    log_event("Resilience policy updated")
    flash("Recovery and backup policy saved.", "success")
    return redirect(url_for("resilience.resilience_page"))


@resilience_bp.route("/backup", methods=["POST"])
def backup_now():
    settings = load_resilience()["backups"]
    path = create_backup(include_media=settings.get("include_media", False))
    prune_backups(settings.get("retain", 6))
    log_event(f"Manual resilience backup created: {path.name}")
    flash(f"Backup created: {path.name}", "success")
    return redirect(url_for("resilience.resilience_page"))
