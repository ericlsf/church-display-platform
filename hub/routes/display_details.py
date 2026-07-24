import subprocess
import sys
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.display_details import get_display_details
from services.display_profiles import apply_profile
from services.jobs import create_job
from services.maintenance import set_maintenance
from services.operations_center import update_display_quick_settings
from services.operator_workflow import apply_operator_changes, editor_data


display_details_bp = Blueprint(
    "display_details",
    __name__,
    url_prefix="/display",
)


@display_details_bp.route("/<display_id>")
def page(display_id):
    try:
        return render_template(
            "display_details.html",
            active="display_details",
            **get_display_details(display_id),
        )
    except ValueError:
        flash("Display not found.", "error")
        return redirect(url_for("fleet_map.page"))


@display_details_bp.route("/<display_id>/operator")
def operator(display_id):
    try:
        return render_template(
            "display_operator.html",
            active="display_operator",
            **editor_data(display_id, request.args.get("folder", "")),
        )
    except ValueError:
        flash("Display not found.", "error")
        return redirect(url_for("displays.displays"))


def _bounded_int(name, default, minimum, maximum):
    try:
        value = int(request.form.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


@display_details_bp.route("/<display_id>/operator/apply", methods=["POST"])
def operator_apply(display_id):
    folder = request.form.get("folder", "").strip()
    order = [
        value.strip()
        for value in request.form.get("playlist_order", "").splitlines()
        if value.strip()
    ]
    days = request.form.getlist("service_day")
    times = request.form.getlist("service_time")
    services = [
        {"day": day.strip(), "time": time.strip()}
        for day, time in zip(days, times)
        if day.strip() and time.strip()
    ]
    settings = {
        "overlay": {
            "enabled": request.form.get("overlay_enabled") == "on",
            "text": request.form.get("overlay_text", "").strip()[:160],
        },
        "clock": {
            "enabled": request.form.get("clock_enabled") == "on",
        },
        "countdown": {
            "enabled": request.form.get("countdown_enabled") == "on",
            "text": request.form.get("countdown_text", "").strip()[:80],
            "takeover_text": request.form.get(
                "takeover_text", ""
            ).strip()[:80],
            "start_minutes": _bounded_int(
                "countdown_start_minutes", 20, 0, 180
            ),
            "takeover_seconds": _bounded_int(
                "takeover_seconds", 30, 0, 300
            ),
            "services": services,
        },
        "timings": {
            "image_duration": _bounded_int(
                "image_duration", 8, 1, 300
            ),
        },
    }
    try:
        media_count = apply_operator_changes(
            display_id, folder, order, settings
        )
        flash(
            f"Changes applied: {media_count} media items synced and display "
            "settings queued.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(
        url_for(
            "display_details.operator",
            display_id=display_id,
            folder=folder,
        )
    )


@display_details_bp.route("/<display_id>/operator/refresh", methods=["POST"])
def operator_refresh(display_id):
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    folder = request.form.get("folder", "").strip()
    script = (
        Path(__file__).resolve().parent.parent
        / "scripts"
        / "refresh_media_index.py"
    )
    try:
        subprocess.Popen(
            [sys.executable, str(script), "--remote", remote],
            cwd=str(script.parent.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        flash(
            "Refreshing Google Drive. New images will appear shortly.",
            "success",
        )
    except Exception as exc:
        flash(f"Could not refresh Google Drive: {exc}", "error")
    return redirect(
        url_for(
            "display_details.operator",
            display_id=display_id,
            folder=folder,
        )
    )


@display_details_bp.route("/<display_id>/quick-settings", methods=["POST"])
def quick_settings(display_id):
    try:
        update_display_quick_settings(
            display_id,
            request.form.get("folder", "").strip(),
            request.form.get("overlay_text", ""),
            request.form.get("overlay_enabled") == "on",
        )
        flash("Display settings queued.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))


@display_details_bp.route("/<display_id>/profile", methods=["POST"])
def profile(display_id):
    try:
        apply_profile(
            request.form.get("profile_id", ""),
            display_ids=[display_id],
        )
        flash("Display profile queued.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))


@display_details_bp.route("/<display_id>/action", methods=["POST"])
def action(display_id):
    action_name = request.form.get("action", "").strip()

    job_types = {
        "sync": "sync_now",
        "restart": "restart_display",
        "reboot": "reboot",
        "update_check": "update_check",
        "collect_logs": "collect_logs",
        "screenshot": "upload_preview",
    }

    try:
        job_type = job_types.get(action_name)
        if not job_type:
            raise ValueError("Unsupported display action")

        create_job(display_id, job_type, {})
        flash(f"Queued {action_name} for {display_id}.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))


@display_details_bp.route("/<display_id>/maintenance", methods=["POST"])
def maintenance(display_id):
    try:
        enabled = request.form.get("enabled") == "on"
        reason = request.form.get("reason", "")
        set_maintenance(display_id, enabled, reason)
        flash("Maintenance state updated.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_details.page", display_id=display_id))
