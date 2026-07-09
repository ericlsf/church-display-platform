from flask import Blueprint, redirect, render_template, request, url_for

from services.config import load_config
from services.events import log_event
from services.fleet_state import build_fleet_state
from services.jobs import create_job, list_jobs
from services.releases import latest_git_tag, list_git_tags


deployments_bp = Blueprint("deployments", __name__, url_prefix="/deployments")


def deploy_jobs(limit=100):
    return [
        job for job in list_jobs(limit)
        if job.get("type") == "deploy_update"
    ]


def queue_deploy_job(display_id, target, dry_run):
    create_job(display_id, "deploy_update", {
        "target": target,
        "dry_run": dry_run,
    })
    mode = "dry run" if dry_run != "false" else "real deploy"
    log_event(f"Queued {mode} deployment of {target} for {display_id}")


@deployments_bp.route("")
def deployments_page():
    cfg = load_config()
    tags = list_git_tags()
    state = build_fleet_state()

    return render_template(
        "deployments.html",
        active="deployments",
        displays=cfg.get("displays", []),
        release_tags=tags,
        latest_tag=state.get("latest_tag") or latest_git_tag(),
        outdated_rows=state.get("outdated_rows", []),
        outdated_count=state.get("outdated_count", 0),
        deploy_jobs=deploy_jobs(100),
    )


@deployments_bp.route("/queue", methods=["POST"])
def queue_deployment():
    display_ids = request.form.getlist("display_ids")
    target = request.form.get("target", "").strip()
    dry_run = request.form.get("dry_run", "true").strip()

    if not target or not display_ids:
        return redirect(url_for("deployments.deployments_page"))

    for display_id in display_ids:
        queue_deploy_job(display_id, target, dry_run)

    return redirect(url_for("deployments.deployments_page"))


@deployments_bp.route("/queue-latest", methods=["POST"])
def queue_latest_deployment():
    display_id = request.form.get("display_id", "").strip()
    dry_run = request.form.get("dry_run", "true").strip()
    target = request.form.get("target", "").strip() or latest_git_tag()

    if not display_id or not target:
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    queue_deploy_job(display_id, target, dry_run)

    return redirect(request.referrer or url_for("dashboard.dashboard"))


@deployments_bp.route("/queue-outdated", methods=["POST"])
def queue_outdated_deployment():
    dry_run = request.form.get("dry_run", "true").strip()
    target = request.form.get("target", "").strip() or latest_git_tag()

    if not target:
        return redirect(request.referrer or url_for("deployments.deployments_page"))

    state = build_fleet_state()
    outdated_rows = state.get("outdated_rows", [])

    for row in outdated_rows:
        display_id = row.get("id")
        if display_id:
            queue_deploy_job(display_id, target, dry_run)

    return redirect(request.referrer or url_for("deployments.deployments_page"))
