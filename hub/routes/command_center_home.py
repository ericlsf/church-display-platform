from flask import Blueprint, redirect, url_for


command_center_home_bp = Blueprint(
    "command_center_home",
    __name__,
)


@command_center_home_bp.route("/")
def home():
    return redirect(
        url_for("fleet_dashboard.page"),
        code=302,
    )
