from pathlib import Path


def test_operations_navigation_owns_deployments():
    shell = Path("hub/templates/application_shell.html").read_text()
    operations = shell.split('("operations",', 1)[1].split('("schedules",', 1)[0]
    schedules = shell.split('("schedules",', 1)[1].split('("settings",', 1)[0]
    assert "/deployment-center" in operations
    assert "/content-deployments" in operations
    assert "/deployments" in operations
    assert "/bulk-operations/" in operations
    assert "/content-deployments" not in schedules
    assert "/deployments" not in schedules


def test_deployment_center_is_registered():
    app_source = Path("hub/app.py").read_text()
    assert "from routes.deployment_center import deployment_center_bp" in app_source
    assert "app.register_blueprint(deployment_center_bp)" in app_source


def test_deployment_center_assets_and_api_exist():
    template = Path("hub/templates/deployment_center.html").read_text()
    route = Path("hub/routes/deployment_center.py").read_text()
    assert "deployment-center-v1310.css" in template
    assert "deployment-center-v1310.js" in template
    assert '@deployment_center_bp.route("/deployment-center")' in route
    assert '@deployment_center_bp.route("/api/v1/deployment-center")' in route


def test_content_deployments_has_specific_title():
    template = Path("hub/templates/content_deployments.html").read_text()
    assert "<h1>Content Deployments</h1>" in template
