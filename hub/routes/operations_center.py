from flask import Blueprint, flash, redirect, render_template, request, url_for
from services.operations_center import dashboard_data, retry_contextual_action, update_display_quick_settings

operations_center_bp = Blueprint("operations_center", __name__, url_prefix="/operations-center")

@operations_center_bp.route("")
def page():
    return render_template("operations_center.html", active="operations_center", **dashboard_data())

@operations_center_bp.route("/quick-update", methods=["POST"])
def quick_update():
    try:
        update_display_quick_settings(
            request.form.get("display_id", "").strip(),
            request.form.get("folder", "").strip(),
            request.form.get("overlay_text", ""),
            request.form.get("overlay_enabled") == "on",
        )
        flash("Folder and presentation settings were queued successfully.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("operations_center.page"))

@operations_center_bp.route("/recover", methods=["POST"])
def recover():
    try:
        display_id = request.form.get("display_id", "").strip()
        action = request.form.get("action", "").strip()
        retry_contextual_action(display_id, action)
        flash(f"Queued {action} for {display_id}.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("operations_center.page"))
