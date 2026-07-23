from services.notifications import (
    build_notifications,
    notification_summary,
)
from services.auth import init_auth_db, load_current_user, log_audit, user_count
from routes.auth import auth_bp
from flask import g, redirect, request, session, url_for
import os
from flask import Flask, render_template
from routes.dashboard import dashboard_bp
from routes.displays import displays_bp
from routes.fleet import fleet_bp
from routes.discovery import discovery_bp
from routes.health import health_bp
from routes.heartbeat import heartbeat_bp
from routes.live import live_bp
from routes.jobs import jobs_bp, jobs_api_bp
from routes.deployments import deployments_bp
from routes.content_deployments import content_deployments_bp
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
from routes.resilience import resilience_bp
from routes.history import history_bp
from routes.simulation import simulation_bp
from routes.display_installer import display_installer_bp
from routes.provisioning import provisioning_bp
from routes.display_releases import display_releases_bp
from routes.fleet_operations import fleet_operations_bp
from routes.operations_center import operations_center_bp
from routes.rollouts import rollouts_bp
from routes.audit import audit_bp
from routes.groups_maintenance import groups_maintenance_bp
from routes.fleet_map import fleet_map_bp
from routes.display_profiles import display_profiles_bp
from routes.display_details import display_details_bp
from routes.operator_experience import operator_experience_bp
from routes.command_center import command_center_bp
from routes.command_center_home import command_center_home_bp
from routes.display_upgrades import display_upgrades_bp
from routes.health_diagnostics import health_diagnostics_bp
from routes.deployment_verification import deployment_verification_bp
from routes.deployment_timeline import deployment_timeline_bp
from routes.automatic_rollback import automatic_rollback_bp
from routes.fleet_dashboard import fleet_dashboard_bp
from routes.bulk_operations import bulk_operations_bp
from routes.alert_center import alert_center_bp
from routes.alert_acknowledgements import alert_acknowledgements_bp
from routes.alert_rules import alert_rules_bp
from routes.fleet_command_center import fleet_command_center_bp
from services.startup import run_startup_checks
from services.request_context import assign_request_id, log_exception, request_id


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
    app.register_blueprint(content_deployments_bp)
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
    app.register_blueprint(resilience_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(display_installer_bp)
    app.register_blueprint(provisioning_bp)
    app.register_blueprint(display_releases_bp)
    app.register_blueprint(fleet_operations_bp)
    app.register_blueprint(operations_center_bp)
    app.register_blueprint(rollouts_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(groups_maintenance_bp)
    app.register_blueprint(fleet_map_bp)
    app.register_blueprint(display_profiles_bp)
    app.register_blueprint(display_details_bp)
    app.register_blueprint(operator_experience_bp)
    app.register_blueprint(command_center_bp)
    app.register_blueprint(command_center_home_bp)
    app.register_blueprint(display_upgrades_bp)
    app.register_blueprint(health_diagnostics_bp)
    app.register_blueprint(deployment_verification_bp)
    app.register_blueprint(deployment_timeline_bp)
    app.register_blueprint(automatic_rollback_bp)
    app.register_blueprint(fleet_dashboard_bp)
    app.register_blueprint(bulk_operations_bp)
    app.register_blueprint(alert_center_bp)
    app.register_blueprint(alert_acknowledgements_bp)
    app.register_blueprint(alert_rules_bp)
    app.register_blueprint(fleet_command_center_bp)

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
        "/install/display",
        "/install/display/package.tar.gz",
        "/install/display/command",
    }

    api_prefixes = (
        "/api/v1/jobs/next",
        "/api/v1/jobs/",
        "/api/v1/content/",
        "/api/v1/display-releases/",
    )

    @app.before_request
    def church_display_request_context():
        assign_request_id()

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

        if request.path.startswith(("/users", "/audit", "/system", "/resilience")) and role != "admin":
            return ("Administrator access required.", 403)

        if request.path.startswith(("/deployments", "/jobs", "/schedules")) and mutating:
            if role not in {"admin", "editor"}:
                return ("Editor or administrator access required.", 403)
        return None

    @app.after_request
    def church_display_audit_response(response):
        response.headers["X-Request-ID"] = request_id()
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            try:
                log_audit(status_code=response.status_code)
            except Exception:
                pass
        return response

    @app.errorhandler(403)
    def church_display_forbidden(error):
        return render_template(
            "error.html",
            title="Access denied",
            message="Your account does not have permission to perform this action.",
            status_code=403,
            request_id=request_id(),
        ), 403

    @app.errorhandler(404)
    def church_display_not_found(error):
        return render_template(
            "error.html",
            title="Page not found",
            message="The requested page or resource could not be found.",
            status_code=404,
            request_id=request_id(),
        ), 404

    @app.errorhandler(500)
    def church_display_internal_error(error):
        log_exception(error)
        return render_template(
            "error.html",
            title="Something went wrong",
            message="The Hub could not complete this request. Use the reference ID when reviewing logs or requesting support.",
            status_code=500,
            request_id=request_id(),
        ), 500

    @app.context_processor
    def church_display_auth_context():
        return {"current_user": getattr(g, "current_user", None), "notification_summary": notification_summary()}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, threaded=True)
