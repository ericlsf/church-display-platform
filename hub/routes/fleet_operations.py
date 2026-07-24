from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.display_groups import load_groups
from services.fleet_operations import fleet_rows, queue_bulk_action
from services.releases import latest_git_tag, list_git_tags


fleet_operations_bp = Blueprint(
    "fleet_operations",
    __name__,
    url_prefix="/fleet-operations",
)


@fleet_operations_bp.route("")
def page():
    return redirect(url_for("displays.page"), code=302)


@fleet_operations_bp.route("/bulk", methods=["POST"])
def bulk():
    display_ids = request.form.getlist("display_ids")
    group_ids = request.form.getlist("group_ids")
    action = request.form.get("action", "").strip()
    allow_maintenance = (
        request.form.get("allow_maintenance") == "on"
    )

    if not display_ids and not group_ids:
        flash("Select at least one display or group.", "error")
        return redirect(url_for("fleet_operations.page"))

    try:
        if action == "deploy_update":
            payload = {
                "target": request.form.get("target", "").strip(),
                "dry_run": request.form.get("dry_run", "true"),
            }
        elif action == "apply_display_settings":
            payload = {
                "settings": {
                    "overlay": {
                        "enabled": (
                            request.form.get("overlay_enabled") == "on"
                        ),
                        "text": request.form.get(
                            "overlay_text",
                            "",
                        ).strip(),
                    },
                    "clock": {
                        "enabled": (
                            request.form.get("clock_enabled") == "on"
                        ),
                    },
                    "countdown": {
                        "enabled": (
                            request.form.get("countdown_enabled") == "on"
                        ),
                        "start_minutes": int(
                            request.form.get(
                                "countdown_start_minutes",
                                "20",
                            )
                        ),
                    },
                    "timings": {
                        "image_duration": int(
                            request.form.get(
                                "image_duration",
                                "8",
                            )
                        ),
                    },
                },
            }
        else:
            payload = {}

        result = queue_bulk_action(
            display_ids,
            action,
            payload,
            group_ids=group_ids,
            allow_maintenance=allow_maintenance,
        )

        message = (
            f"Queued {action} for "
            f"{len(result['queued_display_ids'])} display(s)."
        )
        if result["blocked_display_ids"]:
            message += (
                " Skipped maintenance displays: "
                + ", ".join(result["blocked_display_ids"])
            )

        flash(message, "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("fleet_operations.page"))
