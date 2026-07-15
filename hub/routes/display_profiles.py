import json

from flask import (
    Blueprint,
    Response,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.config import load_config
from services.display_groups import load_groups
from services.display_profiles import (
    apply_profile,
    clone_profile,
    delete_profile,
    export_profile,
    import_profile,
    load_profiles,
    restore_revision,
    save_profile,
    set_default_profile,
)


display_profiles_bp = Blueprint(
    "display_profiles",
    __name__,
    url_prefix="/display-profiles",
)


def _actor():
    user = getattr(g, "user", None)

    if isinstance(user, dict):
        return (
            user.get("username")
            or user.get("display_name")
            or "unknown"
        )

    if user:
        return (
            getattr(user, "username", None)
            or getattr(user, "display_name", None)
            or str(user)
        )

    return (
        session.get("username")
        or session.get("user")
        or session.get("display_name")
        or "unknown"
    )


def _settings_from_form():
    return {
        "overlay": {
            "enabled": request.form.get("overlay_enabled") == "on",
            "text": request.form.get("overlay_text", ""),
        },
        "clock": {
            "enabled": request.form.get("clock_enabled") == "on",
        },
        "countdown": {
            "enabled": (
                request.form.get("countdown_enabled") == "on"
            ),
            "start_minutes": request.form.get(
                "countdown_start_minutes",
                "20",
            ),
        },
        "timings": {
            "image_duration": request.form.get(
                "image_duration",
                "8",
            ),
        },
    }


@display_profiles_bp.route("")
def page():
    data = load_profiles()

    return render_template(
        "display_profiles.html",
        active="display_profiles",
        profiles=data.get("profiles", []),
        default_profile_id=data.get(
            "default_profile_id",
            "",
        ),
        displays=load_config().get("displays", []),
        groups=load_groups().get("groups", []),
    )


@display_profiles_bp.route("/save", methods=["POST"])
def save():
    try:
        profile = save_profile(
            request.form.get("profile_id", ""),
            request.form.get("name", ""),
            request.form.get("description", ""),
            _settings_from_form(),
            actor=_actor(),
        )
        flash(
            f"Profile '{profile['name']}' saved.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_profiles.page"))


@display_profiles_bp.route("/clone", methods=["POST"])
def clone():
    try:
        profile = clone_profile(
            request.form.get("profile_id", ""),
            request.form.get("name", ""),
            actor=_actor(),
        )
        flash(
            f"Created profile '{profile['name']}'.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_profiles.page"))


@display_profiles_bp.route("/delete", methods=["POST"])
def delete():
    try:
        delete_profile(
            request.form.get("profile_id", "")
        )
        flash("Profile deleted.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_profiles.page"))


@display_profiles_bp.route("/default", methods=["POST"])
def default():
    try:
        set_default_profile(
            request.form.get("profile_id", "")
        )
        flash("Default profile updated.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_profiles.page"))


@display_profiles_bp.route("/apply", methods=["POST"])
def apply():
    try:
        result = apply_profile(
            request.form.get("profile_id", ""),
            request.form.getlist("display_ids"),
            request.form.getlist("group_ids"),
        )
        flash(
            f"Queued '{result['profile']['name']}' for "
            f"{len(result['display_ids'])} display(s).",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_profiles.page"))


@display_profiles_bp.route(
    "/restore",
    methods=["POST"],
)
def restore():
    try:
        profile = restore_revision(
            request.form.get("profile_id", ""),
            request.form.get("revision_index", ""),
            actor=_actor(),
        )
        flash(
            f"Restored an earlier revision of "
            f"'{profile['name']}'.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_profiles.page"))


@display_profiles_bp.route(
    "/<profile_id>/export.json",
)
def export_json(profile_id):
    try:
        payload = export_profile(profile_id)
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }, 404

    filename = (
        payload["profile"]["id"]
        or "display-profile"
    )

    return Response(
        json.dumps(payload, indent=2) + "\n",
        mimetype="application/json",
        headers={
            "Content-Disposition": (
                f"attachment; filename={filename}.json"
            ),
            "Cache-Control": "no-store",
        },
    )


@display_profiles_bp.route(
    "/import",
    methods=["POST"],
)
def import_json():
    try:
        upload = request.files.get("profile_file")
        if not upload:
            raise ValueError("Choose a profile JSON file")

        payload = json.load(upload.stream)
        profile = import_profile(
            payload,
            actor=_actor(),
        )
        flash(
            f"Imported profile '{profile['name']}'.",
            "success",
        )
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(url_for("display_profiles.page"))
