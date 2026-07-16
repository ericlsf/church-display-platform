from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    session,
    url_for,
)

from services.alert_acknowledgements import (
    acknowledge_alert,
    clear_acknowledgement,
)


alert_acknowledgements_bp = Blueprint(
    "alert_acknowledgements",
    __name__,
    url_prefix="/alerts",
)


def _current_user():
    return (
        session.get("username")
        or session.get("user")
        or session.get("email")
        or ""
    )


@alert_acknowledgements_bp.route(
    "/acknowledge",
    methods=["POST"],
)
def acknowledge():
    key = request.form.get("key", "")
    note = request.form.get("note", "")

    try:
        acknowledge_alert(
            key,
            user=_current_user(),
            note=note,
        )
        flash("Alert acknowledged.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(
        url_for("alert_center.page")
    )


@alert_acknowledgements_bp.route(
    "/restore",
    methods=["POST"],
)
def restore():
    key = request.form.get("key", "")

    try:
        clear_acknowledgement(key)
        flash("Alert restored to active alerts.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(
        url_for("alert_center.page")
    )
