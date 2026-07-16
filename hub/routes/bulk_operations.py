from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from services.bulk_operations import queue_bulk_jobs
from services.config import load_config
from services.fleet_operations import fleet_rows


bulk_operations_bp = Blueprint(
    "bulk_operations",
    __name__,
    url_prefix="/bulk-operations",
)


@bulk_operations_bp.route("/", methods=["GET"])
def page():
    config = load_config()

    return render_template(
        "bulk_operations.html",
        displays=list(fleet_rows()),
        folders=config.get("folder_options", []),
        profiles=config.get("display_profiles", []),
        releases=config.get("display_releases", []),
    )


@bulk_operations_bp.route("/run", methods=["POST"])
def run():
    display_ids = request.form.getlist("display_ids")
    operation = request.form.get("operation", "").strip()

    maintenance_value = request.form.get("maintenance_enabled")
    maintenance_enabled = None

    if maintenance_value == "true":
        maintenance_enabled = True
    elif maintenance_value == "false":
        maintenance_enabled = False

    try:
        result = queue_bulk_jobs(
            display_ids,
            operation,
            folder=request.form.get("folder", ""),
            profile_id=request.form.get("profile_id", ""),
            target=request.form.get("target", ""),
            maintenance_enabled=maintenance_enabled,
        )

        flash(
            (
                f'Queued {result["queued_count"]} job(s); '
                f'skipped {result["skipped_count"]} duplicate(s).'
            ),
            "success",
        )

    except Exception as exc:
        flash(str(exc), "error")

    return redirect(
        url_for("bulk_operations.page")
    )
