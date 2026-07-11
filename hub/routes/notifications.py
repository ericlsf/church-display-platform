from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.notifications import build_notifications, clear_dismissals, dismiss, notification_summary

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("")
def notifications_page():
    return render_template(
        "notifications.html",
        active="notifications",
        notifications=build_notifications(include_dismissed=request.args.get("dismissed") == "1"),
        summary=notification_summary(),
    )


@notifications_bp.route("/dismiss", methods=["POST"])
def dismiss_notification():
    notification_id = request.form.get("notification_id", "").strip()
    if notification_id:
        dismiss(notification_id)
    return redirect(request.form.get("next") or url_for("notifications.notifications_page"))


@notifications_bp.route("/reset", methods=["POST"])
def reset_notifications():
    clear_dismissals()
    return redirect(url_for("notifications.notifications_page"))


@notifications_bp.route("/api")
def notifications_api():
    items = build_notifications()
    return jsonify({"ok": True, "summary": notification_summary(), "notifications": items})
