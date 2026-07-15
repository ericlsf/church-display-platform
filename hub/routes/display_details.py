from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.display_details import get_display_details
from services.display_profiles import apply_profile
from services.jobs import create_job
from services.maintenance import set_maintenance
from services.operations_center import update_display_quick_settings


display_details_bp = Blueprint(
    "display_details",
    __name__,
    url_prefix="/display",
)


@display_details_bp.route("/<display_id>")
def page(display_id):
    try:
        return render_template(
            "display_details.html",
            active="display_details",
            **get_display_details(display_id),
        )
    except ValueError:
        flash("Display not found.", "error")
        return redirect(url_for("fleet_map.page"))


@display_details_bp.route("/<display_id>/quick-settings", methods=["POST"])
def quick_settings(display_id):
    try:
        update_display_quick_settings(
            display_id,
            request.form.get("folder", "").strip(),
            request.form.get("overlay_text", ""),
            request.form.get("overlay_enabled") == "on",
        )
        flash("Display settings queued.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))


@display_details_bp.route("/<display_id>/profile", methods=["POST"])
def profile(display_id):
    try:
        apply_profile(
            request.form.get("profile_id", ""),
            display_ids=[display_id],
        )
        flash("Display profile queued.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))


@display_details_bp.route("/<display_id>/action", methods=["POST"])
def action(display_id):
    action_name = request.form.get("action", "").strip()

    job_types = {
        "sync": "sync_now",
        "restart": "restart_display",
        "reboot": "reboot",
        "update_check": "update_check",
        "collect_logs": "collect_logs",
    }

    try:
        job_type = job_types.get(action_name)
        if not job_type:
            raise ValueError("Unsupported display action")

        create_job(display_id, job_type, {})
        flash(f"Queued {action_name} for {display_id}.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))


@display_details_bp.route("/<display_id>/maintenance", methods=["POST"])
def maintenance(display_id):
    try:
        enabled = request.form.get("enabled") == "on"
        reason = request.form.get("reason", "")
        set_maintenance(display_id, enabled, reason)
        flash("Maintenance state updated.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))
