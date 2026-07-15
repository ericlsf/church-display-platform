from flask import Blueprint, flash, redirect, request, url_for

from services.display_upgrades import (
    queue_display_upgrade,
    queue_rollback,
)


display_upgrades_bp = Blueprint(
    "display_upgrades",
    __name__,
    url_prefix="/display",
)


@display_upgrades_bp.route(
    "/<display_id>/upgrade",
    methods=["POST"],
)
def upgrade(display_id):
    target = request.form.get(
        "target",
        "",
    ).strip()
    dry_run = (
        request.form.get("mode", "dry_run")
        == "dry_run"
    )
    override = (
        request.form.get("override_maintenance")
        == "on"
    )

    try:
        result = queue_display_upgrade(
            display_id,
            target,
            dry_run=dry_run,
            override_maintenance=override,
        )

        if result["reused"]:
            flash(
                "An identical deployment is already active; "
                "the existing job was reused.",
                "success",
            )
        else:
            flash(
                (
                    "Upgrade dry run queued."
                    if dry_run
                    else "Software upgrade queued."
                ),
                "success",
            )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(
        url_for(
            "display_details.page",
            display_id=display_id,
        )
    )


@display_upgrades_bp.route(
    "/<display_id>/rollback",
    methods=["POST"],
)
def rollback(display_id):
    try:
        queue_rollback(
            display_id,
            request.form.get(
                "failed_job_id",
                "",
            ).strip(),
        )
        flash(
            "Rollback job queued.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(
        url_for(
            "display_details.page",
            display_id=display_id,
        )
    )
