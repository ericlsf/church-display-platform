from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_config
from services.display_groups import (
    delete_group,
    load_groups,
    upsert_group,
)
from services.maintenance import set_maintenance


groups_maintenance_bp = Blueprint(
    "groups_maintenance",
    __name__,
    url_prefix="/fleet-config",
)


@groups_maintenance_bp.route("")
def page():
    return render_template(
        "groups_maintenance.html",
        active="fleet_config",
        displays=load_config().get("displays", []),
        groups=load_groups().get("groups", []),
    )


@groups_maintenance_bp.route("/groups/save", methods=["POST"])
def save_group():
    try:
        upsert_group(
            request.form.get("group_id", "").strip(),
            request.form.get("name", "").strip(),
            request.form.getlist("members"),
        )
        flash("Display group saved.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("groups_maintenance.page"))


@groups_maintenance_bp.route("/groups/delete", methods=["POST"])
def remove_group():
    try:
        delete_group(request.form.get("group_id", "").strip())
        flash("Display group removed.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("groups_maintenance.page"))


@groups_maintenance_bp.route("/maintenance", methods=["POST"])
def maintenance():
    display_id = request.form.get("display_id", "").strip()
    enabled = request.form.get("enabled") == "on"
    reason = request.form.get("reason", "").strip()

    try:
        set_maintenance(display_id, enabled, reason)
        flash(
            f"Maintenance {'enabled' if enabled else 'disabled'} for {display_id}.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("groups_maintenance.page"))
