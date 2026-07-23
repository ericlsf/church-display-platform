from flask import Blueprint, flash, redirect, request, url_for

from services.provisioning import retry_initial_provisioning


provisioning_bp = Blueprint(
    "provisioning",
    __name__,
    url_prefix="/provisioning",
)


@provisioning_bp.route("/<display_id>/retry", methods=["POST"])
def retry(display_id):
    try:
        retry_initial_provisioning(display_id)
        flash(
            f"Initial provisioning was requeued for {display_id}.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(request.referrer or url_for("setup.setup_page"))
