from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.fleet_operations import fleet_rows, queue_bulk_action
from services.releases import latest_git_tag, list_git_tags


fleet_operations_bp = Blueprint(
    "fleet_operations",
    __name__,
    url_prefix="/fleet-operations",
)


@fleet_operations_bp.route("")
def page():
    rows = fleet_rows()
    summary = {
        "total": len(rows),
        "ready": sum(1 for row in rows if row["readiness"] == "ready"),
        "offline": sum(1 for row in rows if row["readiness"] == "offline"),
        "attention": sum(
            1
            for row in rows
            if row["readiness"] in {"needs_attention", "needs_playlist"}
        ),
        "provisioning": sum(
            1
            for row in rows
            if row["readiness"] == "provisioning"
        ),
    }

    return render_template(
        "fleet_operations.html",
        active="fleet_operations",
        rows=rows,
        summary=summary,
        release_tags=list_git_tags(),
        latest_tag=latest_git_tag(),
    )


@fleet_operations_bp.route("/bulk", methods=["POST"])
def bulk():
    display_ids = request.form.getlist("display_ids")
    action = request.form.get("action", "").strip()

    if not display_ids:
        flash("Select at least one display.", "error")
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
                        "enabled": request.form.get("overlay_enabled") == "on",
                        "text": request.form.get("overlay_text", "").strip(),
                    },
                    "clock": {
                        "enabled": request.form.get("clock_enabled") == "on",
                    },
                    "countdown": {
                        "enabled": request.form.get("countdown_enabled") == "on",
                        "start_minutes": int(
                            request.form.get(
                                "countdown_start_minutes",
                                "20",
                            )
                        ),
                    },
                    "timings": {
                        "image_duration": int(
                            request.form.get("image_duration", "8")
                        ),
                    },
                },
            }
        else:
            payload = {}

        queue_bulk_action(display_ids, action, payload)
        flash(
            f"Queued {action} for {len(display_ids)} display(s).",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("fleet_operations.page"))
