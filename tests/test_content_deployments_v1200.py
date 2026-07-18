import os, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_files_and_registration():
    assert (ROOT / 'hub/routes/content_deployments.py').exists()
    assert (ROOT / 'hub/services/content_deployments.py').exists()
    assert (ROOT / 'hub/templates/content_deployments.html').exists()
    assert (ROOT / 'hub/static/content-deployments-v1200.css').exists()
    app = (ROOT / 'hub/app.py').read_text()
    assert 'content_deployments_bp' in app
    nav = (ROOT / 'hub/templates/application_shell.html').read_text()
    assert '/content-deployments' in nav
    assert 'Content Deployments' in nav

def test_store_lifecycle():
    import sys
    sys.path.insert(0, str(ROOT / 'hub'))
    from services import content_deployments as svc
    with tempfile.TemporaryDirectory() as td:
        os.environ['CHURCH_DISPLAY_CONTENT_DEPLOYMENTS'] = str(Path(td) / 'store.json')
        draft = svc.create_draft('Sunday', 'Weekly', ['a'], {'a': 'Old'}, 'tester')
        assert svc.get_draft(draft['id'])['folder'] == 'Weekly'
        published = svc.publish_draft(draft['id'], 'tester')
        assert published['status'] == 'published'
        assert svc.find_history(published['id'])['before']['a'] == 'Old'
        rollback = svc.record_rollback(published, 'tester')
        assert rollback['status'] == 'rolled_back'
        del os.environ['CHURCH_DISPLAY_CONTENT_DEPLOYMENTS']


def test_content_deployments_uses_shared_base_layout():
    template = (ROOT / 'hub/templates/content_deployments.html').read_text()
    assert template.lstrip().startswith('{% extends "base.html" %}')
    assert '{% block head %}' in template
    assert 'content-deployments-v1200.css' in template
    assert '{% block content %}' in template
    assert 'application_shell.html' not in template.splitlines()[0]
