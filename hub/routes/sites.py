from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.fleet_state import build_fleet_state
from services.groups import list_groups
from services.jobs import create_job
from services.releases import list_git_tags
from services.sites import create_site, delete_site, get_site, list_sites, resolve_site_display_ids, update_site

sites_bp = Blueprint("sites", __name__, url_prefix="/sites")


def queue_for_site(site, job_type, payload=None):
    display_ids = resolve_site_display_ids(site, list_groups())
    for display_id in display_ids:
        create_job(display_id, job_type, payload or {})
    log_event(f"Queued {job_type} for site {site.get('name')} ({len(display_ids)} display(s))")
    return len(display_ids)


@sites_bp.route("")
def sites_page():
    displays = load_config().get("displays", [])
    groups = list_groups()
    fleet = build_fleet_state()
    rows_by_id = {row.get("id"): row for row in fleet.get("rows", [])}
    site_rows = []
    for site in list_sites():
        ids = resolve_site_display_ids(site, groups)
        members = [rows_by_id[i] for i in ids if i in rows_by_id]
        site_rows.append({
            **site,
            "member_count": len(ids),
            "online_count": sum(1 for row in members if row.get("online")),
            "outdated_count": sum(1 for row in members if row.get("update_available")),
            "active_playlist_count": len({row.get("sync_folder") for row in members if row.get("sync_folder")}),
        })
    settings = load_hub_settings()
    remote = settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)
    return render_template("sites.html", active="sites", sites=site_rows, displays=displays,
                           groups=groups, drive_remote=remote, drive_folders=folders,
                           drive_error=drive_error, release_tags=list_git_tags())


@sites_bp.route("/create", methods=["POST"])
def create_site_route():
    try:
        site = create_site(request.form.get("name"), request.form.get("description"),
                           request.form.getlist("display_ids"), request.form.getlist("group_ids"))
        log_event(f"Created site {site['name']}")
        flash("Site created.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("sites.sites_page"))


@sites_bp.route("/<site_id>/update", methods=["POST"])
def update_site_route(site_id):
    try:
        site = update_site(site_id, request.form.get("name"), request.form.get("description"),
                           request.form.getlist("display_ids"), request.form.getlist("group_ids"))
        log_event(f"Updated site {site['name']}")
        flash("Site updated.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("sites.sites_page"))


@sites_bp.route("/<site_id>/delete", methods=["POST"])
def delete_site_route(site_id):
    site = get_site(site_id)
    if site and delete_site(site_id):
        log_event(f"Deleted site {site.get('name')}")
        flash("Site deleted.", "success")
    return redirect(url_for("sites.sites_page"))


@sites_bp.route("/<site_id>/action", methods=["POST"])
def site_action(site_id):
    site = get_site(site_id)
    if not site:
        flash("Site not found.", "error")
        return redirect(url_for("sites.sites_page"))
    action = request.form.get("action", "").strip()
    if action in {"sync_now", "heartbeat", "restart_display", "reboot"}:
        count = queue_for_site(site, action)
    elif action == "set_sync_folder":
        folder = request.form.get("folder", "").strip()
        if not folder:
            flash("Select a folder.", "error")
            return redirect(url_for("sites.sites_page"))
        count = queue_for_site(site, action, {"folder": folder,
            "remote": request.form.get("remote", "gdrive").strip() or "gdrive", "run_now": True})
    elif action == "deploy_update":
        target = request.form.get("target", "").strip()
        if not target:
            flash("Select a version.", "error")
            return redirect(url_for("sites.sites_page"))
        count = queue_for_site(site, action, {"target": target,
            "dry_run": request.form.get("dry_run", "true").strip()})
    else:
        flash("Unknown site action.", "error")
        return redirect(url_for("sites.sites_page"))
    flash(f"Queued {action.replace('_', ' ')} for {count} display(s).", "success")
    return redirect(url_for("sites.sites_page"))
