from flask import Blueprint, flash, redirect, request, url_for

from services.health_diagnostics import queue_health_action


health_diagnostics_bp = Blueprint(
    "health_diagnostics",
    __name__,
    url_prefix="/display",
)


@health_diagnostics_bp.route(
    "/<display_id>/health-action",
    methods=["POST"],
)
def health_action(display_id):
    action = request.form.get("action", "").strip()

    if action == "settings":
        return redirect(
            url_for(
                "display_details.page",
                display_id=display_id,
                _anchor="content-settings",
            )
        )

    try:
        queue_health_action(display_id, action)
        flash(
            f"Queued {action} for {display_id}.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(
        url_for(
            "display_details.page",
            display_id=display_id,
            _anchor="health-diagnostics",
        )
    )
