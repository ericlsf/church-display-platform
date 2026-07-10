from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from services.platform_admin import (
    BACKUP_DIR,
    build_support_bundle,
    create_backup,
    list_backups,
    platform_status,
    restore_backup,
)

system_bp = Blueprint("system", __name__, url_prefix="/system")


@system_bp.route("")
def system_page():
    return render_template("system.html", active="system", status=platform_status(), backups=list_backups())


@system_bp.route("/backup", methods=["POST"])
def backup_now():
    path = create_backup(include_media=request.form.get("include_media") == "1")
    return send_file(path, as_attachment=True, download_name=path.name)


@system_bp.route("/restore", methods=["POST"])
def restore_now():
    name = Path(request.form.get("backup", "")).name
    try:
        restore_backup(BACKUP_DIR / name)
    except Exception as exc:
        return f"Restore failed: {exc}", 400
    return redirect(url_for("system.system_page"))


@system_bp.route("/support")
def support_bundle():
    path = build_support_bundle()
    return send_file(path, as_attachment=True, download_name=path.name)
