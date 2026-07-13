from urllib.parse import quote

from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.display_releases import build_release_package
from services.events import log_event
from services.fleet_state import build_fleet_state
from services.jobs import create_job, list_jobs
from services.releases import latest_git_tag, list_git_tags


deployments_bp = Blueprint("deployments", __name__, url_prefix="/deployments")


def deploy_jobs(limit=100):
    return [
        job
        for job in list_jobs(limit)
        if job.get("type") == "deploy_update"
    ]


def package_base_url():
    settings = load_hub_settings()
    return (
        settings.get("hub_url")
        or "http://church-display-hub.local:8090"
    ).rstrip("/")


def queue_deploy_job(display_id, target, dry_run):
    release = build_release_package(target)
    encoded_target = quote(target, safe="")
    package_url = (
        f"{package_base_url()}/api/v1/display-releases/"
        f"{encoded_target}/package.tar.gz"
    )

    create_job(
        display_id,
        "deploy_update",
        {
            "target": target,
            "dry_run": dry_run,
            "package_url": package_url,
            "sha256": release["sha256"],
            "commit": release["commit"],
            "package_size": release["size"],
            "deployment_mode": "hub_package",
        },
    )

    mode = "dry run" if str(dry_run).lower() != "false" else "real deploy"
    log_event(
        f"Queued {mode} display-package deployment of "
        f"{target} for {display_id}"
    )


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
        deployment_mode="Hub package",
    )


@deployments_bp.route("/queue", methods=["POST"])
def queue_deployment():
    display_ids = request.form.getlist("display_ids")
    target = request.form.get("target", "").strip()
    dry_run = request.form.get("dry_run", "true").strip()

    if not target or not display_ids:
        flash("Select a version and at least one display.", "error")
        return redirect(url_for("deployments.deployments_page"))

    try:
        for display_id in display_ids:
            queue_deploy_job(display_id, target, dry_run)
        flash(
            f"Queued {target} for {len(display_ids)} display(s).",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("deployments.deployments_page"))


@deployments_bp.route("/queue-latest", methods=["POST"])
def queue_latest_deployment():
    display_id = request.form.get("display_id", "").strip()
    dry_run = request.form.get("dry_run", "true").strip()
    target = request.form.get("target", "").strip() or latest_git_tag()

    if not display_id or not target:
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    try:
        queue_deploy_job(display_id, target, dry_run)
        flash(f"Queued {target} for {display_id}.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(request.referrer or url_for("dashboard.dashboard"))


@deployments_bp.route("/queue-outdated", methods=["POST"])
def queue_outdated_deployment():
    dry_run = request.form.get("dry_run", "true").strip()
    target = request.form.get("target", "").strip() or latest_git_tag()

    if not target:
        return redirect(request.referrer or url_for("deployments.deployments_page"))

    state = build_fleet_state()
    outdated_rows = state.get("outdated_rows", [])

    try:
        for row in outdated_rows:
            display_id = row.get("id")
            if display_id:
                queue_deploy_job(display_id, target, dry_run)
        flash(
            f"Queued {target} for {len(outdated_rows)} outdated display(s).",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(request.referrer or url_for("deployments.deployments_page"))
