from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.notifications import (
    clear_resolved,
    dismiss,
    mark_read,
    resolve_notification,
    unread_count,
    visible_notifications,
)


notifications_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications",
)


@notifications_bp.route("")
def page():
    return render_template(
        "notifications.html",
        active="notifications",
        notifications=visible_notifications(250),
        unread=unread_count(),
    )


@notifications_bp.route("/summary")
def summary():
    rows = visible_notifications(20)
    return jsonify({
        "ok": True,
        "unread": unread_count(),
        "notifications": rows[:5],
    })


@notifications_bp.route("/read", methods=["POST"])
def read():
    mark_read(
        request.form.get("notification_id", "").strip() or None,
        all_notifications=request.form.get("all") == "1",
    )
    return redirect(request.referrer or url_for("notifications.page"))


@notifications_bp.route("/dismiss", methods=["POST"])
def dismiss_one():
    dismiss(request.form.get("notification_id", "").strip())
    return redirect(request.referrer or url_for("notifications.page"))


@notifications_bp.route("/clear-resolved", methods=["POST"])
def clear_resolved_route():
    clear_resolved()
    return redirect(url_for("notifications.page"))


@notifications_bp.route("/resolve", methods=["POST"])
def resolve():
    resolve_notification(request.form.get("notification_id", ""))
    return redirect(url_for("notifications.page"))
