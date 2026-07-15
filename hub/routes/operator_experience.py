from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_config, save_config
from services.display_profiles import apply_profile
from services.jobs import create_job
from services.operator_experience import (
    display_cards,
    recent_activity,
    wizard_options,
)
from services.operations_center import update_display_quick_settings


operator_experience_bp = Blueprint(
    "operator_experience",
    __name__,
    url_prefix="/operator",
)


@operator_experience_bp.route("/displays")
def displays():
    return render_template(
        "operator_displays.html",
        active="operator_displays",
        cards=display_cards(),
    )


@operator_experience_bp.route("/setup/<display_id>")
def setup_wizard(display_id):
    config = load_config()
    display = next(
        (
            item
            for item in config.get("displays", [])
            if item.get("id") == display_id
        ),
        None,
    )
    if not display:
        flash("Display not found.", "error")
        return redirect(url_for("operator_experience.displays"))

    return render_template(
        "display_setup_wizard.html",
        active="operator_displays",
        display=display,
        **wizard_options(),
    )


@operator_experience_bp.route("/setup/<display_id>/finish", methods=["POST"])
def finish_setup(display_id):
    folder = request.form.get("folder", "").strip()
    profile_id = request.form.get("profile_id", "").strip()
    group_id = request.form.get("group_id", "").strip()
    overlay_text = request.form.get("overlay_text", "").strip()
    overlay_enabled = request.form.get("overlay_enabled") == "on"

    try:
        update_display_quick_settings(
            display_id,
            folder,
            overlay_text,
            overlay_enabled,
        )

        if profile_id:
            apply_profile(
                profile_id,
                display_ids=[display_id],
            )

        if group_id:
            from services.display_groups import load_groups, save_groups

            data = load_groups()
            group = next(
                (
                    item
                    for item in data.get("groups", [])
                    if item.get("id") == group_id
                ),
                None,
            )
            if not group:
                raise ValueError("Selected display group was not found")
            members = group.setdefault("members", [])
            if display_id not in members:
                members.append(display_id)
                save_groups(data)

        create_job(display_id, "sync_now", {})
        create_job(display_id, "restart_display", {})

        config = load_config()
        display = next(
            (
                item
                for item in config.get("displays", [])
                if item.get("id") == display_id
            ),
            None,
        )
        if display:
            display["provisioning_complete"] = True
            if profile_id:
                display["profile_id"] = profile_id
            save_config(config)

        flash("Display setup completed.", "success")
        return redirect(
            url_for(
                "display_details.page",
                display_id=display_id,
            )
        )
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(
            url_for(
                "operator_experience.setup_wizard",
                display_id=display_id,
            )
        )


@operator_experience_bp.route("/activity/<display_id>")
def activity(display_id):
    return {
        "ok": True,
        "events": recent_activity(
            display_id,
            minutes=10,
            limit=50,
        ),
    }
