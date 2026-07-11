from routes.management import management_bp, management_api_bp
from services.notifications import notification_summary
from services.auth import init_auth_db, load_current_user, log_audit, user_count
from routes.auth import auth_bp
from flask import g, redirect, request, session, url_for
import os
from flask import Flask
from routes.dashboard import dashboard_bp
from routes.displays import displays_bp
from routes.fleet import fleet_bp
from routes.discovery import discovery_bp
from routes.health import health_bp
from routes.heartbeat import heartbeat_bp
from routes.live import live_bp
from routes.jobs import jobs_bp, jobs_api_bp
from routes.deployments import deployments_bp
from routes.setup import setup_bp
from routes.system import system_bp

from routes.media import media_bp
from routes.content import content_bp
from routes.content_api import content_api_bp
from routes.schedules import schedules_bp
from routes.releases import releases_bp
from routes.groups import groups_bp
from routes.operations import operations_bp
from routes.sites import sites_bp
from routes.notifications import notifications_bp
from routes.search import search_bp
from services.startup import run_startup_checks


def create_app():
    app = Flask(__name__)
    app.config["STARTUP_PROBLEMS"] = run_startup_checks()
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(displays_bp)
    app.register_blueprint(fleet_bp)
    app.register_blueprint(discovery_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(heartbeat_bp)
    app.register_blueprint(live_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(jobs_api_bp)
    app.register_blueprint(deployments_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(content_api_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(releases_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(operations_bp)
    app.register_blueprint(sites_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(management_bp)
    app.register_blueprint(management_api_bp)

    # v2.6.0 auth hooks
    app.secret_key = os.environ.get(
        "CHURCH_DISPLAY_SECRET_KEY",
        app.config.get("SECRET_KEY") or "REPLACE_ME",
    )

    init_auth_db()

    public_paths = {
        "/login",
        "/setup",
        "/discovery/register",
        "/api/v1/heartbeat",
        "/api/v1/preview",
    }

    api_prefixes = (
        "/api/v1/jobs/next",
        "/api/v1/jobs/",
        "/api/v1/content/",
        "/api/v1/management/",
    )

    @app.before_request
    def church_display_auth_guard():
        load_current_user()

        if request.path.startswith("/static/"):
            return None
        if request.path in public_paths:
            return None
        if any(request.path.startswith(prefix) for prefix in api_prefixes):
            return None

        if user_count() == 0:
            if request.path.startswith("/setup"):
                return None
            return redirect(url_for("setup.setup_page"))

        if not g.current_user:
            return redirect(url_for("auth.login", next=request.full_path))

        role = g.current_user.get("role")
        mutating = request.method in {"POST", "PUT", "PATCH", "DELETE"}

        if mutating and role == "viewer":
            return ("Viewer accounts are read-only.", 403)

        if request.path.startswith(("/users", "/audit", "/system", "/management")) and role != "admin":
            return ("Administrator access required.", 403)

        if request.path.startswith(("/deployments", "/jobs", "/schedules")) and mutating:
            if role not in {"admin", "editor"}:
                return ("Editor or administrator access required.", 403)
        return None

    @app.after_request
    def church_display_audit_response(response):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            try:
                log_audit(status_code=response.status_code)
            except Exception:
                pass
        return response

    @app.context_processor
    def church_display_auth_context():
        return {"current_user": getattr(g, "current_user", None), "notification_summary": notification_summary()}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, threaded=True)
