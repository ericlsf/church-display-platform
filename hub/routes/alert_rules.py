from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from services.alert_rules import (
    load_alert_rules,
    save_alert_rules,
)


alert_rules_bp = Blueprint(
    "alert_rules",
    __name__,
    url_prefix="/alerts/rules",
)


@alert_rules_bp.route("/", methods=["GET"])
def page():
    return render_template(
        "alert_rules.html",
        rules=load_alert_rules(),
    )


@alert_rules_bp.route("/save", methods=["POST"])
def save():
    categories = {
        key: request.form.get(
            f"category_{key}"
        )
        == "on"
        for key in (
            "connectivity",
            "health",
            "content",
            "software",
            "system",
            "jobs",
        )
    }

    try:
        save_alert_rules({
            "offline_delay_minutes": request.form.get(
                "offline_delay_minutes",
                5,
            ),
            "disk_warning_percent": request.form.get(
                "disk_warning_percent",
                80,
            ),
            "disk_critical_percent": request.form.get(
                "disk_critical_percent",
                90,
            ),
            "health_warning_percent": request.form.get(
                "health_warning_percent",
                100,
            ),
            "health_critical_percent": request.form.get(
                "health_critical_percent",
                60,
            ),
            "quiet_hours_enabled": (
                request.form.get(
                    "quiet_hours_enabled"
                )
                == "on"
            ),
            "quiet_hours_start": request.form.get(
                "quiet_hours_start",
                "22:00",
            ),
            "quiet_hours_end": request.form.get(
                "quiet_hours_end",
                "07:00",
            ),
            "categories": categories,
        })

        flash("Alert rules saved.", "success")

    except Exception as exc:
        flash(str(exc), "error")

    return redirect(
        url_for("alert_rules.page")
    )
