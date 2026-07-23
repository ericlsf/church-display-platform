from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_config
from services.releases import latest_git_tag, list_git_tags
from services.rollouts import (
    cancel_rollout,
    create_rollout,
    resume_rollout,
    rollout_rows,
)


rollouts_bp = Blueprint("rollouts", __name__, url_prefix="/rollouts")


@rollouts_bp.route("")
def page():
    return render_template(
        "rollouts.html",
        active="rollouts",
        displays=load_config().get("displays", []),
        release_tags=list_git_tags(),
        latest_tag=latest_git_tag(),
        rollouts=rollout_rows(),
    )


@rollouts_bp.route("/create", methods=["POST"])
def create():
    try:
        scheduled_for = request.form.get("scheduled_for", "").strip()
        if scheduled_for:
            scheduled_for = datetime.fromisoformat(scheduled_for).isoformat()

        create_rollout(
            target=request.form.get("target", "").strip(),
            display_ids=request.form.getlist("display_ids"),
            scheduled_for=scheduled_for,
            canary_display_id=request.form.get("canary_display_id", "").strip(),
            pause_on_failure=request.form.get("pause_on_failure") == "on",
            dry_run=request.form.get("dry_run") == "on",
        )
        flash("Rollout scheduled successfully.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("rollouts.page"))


@rollouts_bp.route("/<rollout_id>/cancel", methods=["POST"])
def cancel(rollout_id):
    try:
        cancel_rollout(rollout_id)
        flash("Rollout cancelled.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("rollouts.page"))


@rollouts_bp.route("/<rollout_id>/resume", methods=["POST"])
def resume(rollout_id):
    try:
        resume_rollout(rollout_id)
        flash("Rollout resumed.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("rollouts.page"))
