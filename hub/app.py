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

from routes.media import media_bp
from routes.content import content_bp
from routes.content_api import content_api_bp
from routes.schedules import schedules_bp
from routes.releases import releases_bp
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
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, threaded=True)
