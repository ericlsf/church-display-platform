from flask import Flask

from routes.dashboard import dashboard_bp
from routes.displays import displays_bp
from routes.fleet import fleet_bp
from routes.discovery import discovery_bp
from routes.health import health_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(displays_bp)
    app.register_blueprint(fleet_bp)
    app.register_blueprint(discovery_bp)
    app.register_blueprint(health_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
