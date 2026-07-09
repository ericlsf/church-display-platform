from flask import Blueprint, redirect, render_template, request, url_for

from services.config import load_config
from services.events import log_event
from services.jobs import create_job, list_jobs
from services.releases import list_git_tags


deployments_bp = Blueprint("deployments", __name__, url_prefix="/deployments")


@deployments_bp.route("")
def deployments_page():
    cfg = load_config()
    tags = list_git_tags()

    deploy_jobs = [
        job for job in list_jobs(100)
        if job.get("type") == "deploy_update"
    ]

    return render_template(
        "deployments.html",
        active="deployments",
        displays=cfg.get("displays", []),
        release_tags=tags,
        deploy_jobs=deploy_jobs,
    )


@deployments_bp.route("/queue", methods=["POST"])
def queue_deployment():
    display_ids = request.form.getlist("display_ids")
    target = request.form.get("target", "").strip()
    dry_run = request.form.get("dry_run", "true").strip()

    if not target or not display_ids:
        return redirect(url_for("deployments.deployments_page"))

    for display_id in display_ids:
        create_job(display_id, "deploy_update", {
            "target": target,
            "dry_run": dry_run,
        })
        log_event(f"Queued deployment of {target} for {display_id}")

    return redirect(url_for("deployments.deployments_page"))
