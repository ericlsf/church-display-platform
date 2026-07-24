from pathlib import Path


def test_deployments_are_one_primary_destination():
    shell = Path("hub/templates/application_shell.html").read_text(encoding="utf-8")
    assert '("/content-deployments", "⇧", "Deployments")' in shell
    assert '("/deployment-center",' not in shell
    assert '("/deployments",' not in shell
    assert '("/bulk-operations/' not in shell


def test_deployment_pages_share_workflow_tabs():
    content = Path("hub/templates/content_deployments.html").read_text(encoding="utf-8")
    software = Path("hub/templates/deployments.html").read_text(encoding="utf-8")
    for template in (content, software):
        assert "workflow-tabs" in template
        assert "Content" in template
        assert "Software" in template
        assert "Scheduled" in template


def test_legacy_deployment_center_redirects_but_api_remains():
    route = Path("hub/routes/deployment_center.py").read_text(encoding="utf-8")
    assert '@deployment_center_bp.route("/deployment-center")' in route
    assert 'redirect(url_for("content_deployments.page"), code=302)' in route
    assert '@deployment_center_bp.route("/api/v1/deployment-center")' in route


def test_content_deployments_has_specific_title():
    template = Path("hub/templates/content_deployments.html").read_text(encoding="utf-8")
    assert "<h1>Content</h1>" in template
