from pathlib import Path


def test_remote_access_blueprint_registered():
    source = Path('hub/app.py').read_text(encoding='utf-8')
    assert 'remote_access_bp' in source
    assert 'register_blueprint(remote_access_bp)' in source


def test_remote_access_navigation_and_assets():
    shell = Path('hub/templates/application_shell.html').read_text(encoding='utf-8')
    page = Path('hub/templates/remote_access.html').read_text(encoding='utf-8')
    assert '/remote-access' in shell
    assert 'remote-access-v1320.css' in page
    assert 'configure-remote-access.sh' in page


def test_remote_access_scripts_do_not_expose_port():
    script = Path('scripts/configure-remote-access.sh').read_text(encoding='utf-8')
    assert 'cloudflared service install "$TOKEN"' in script
    assert 'iptables' not in script
    assert 'ufw allow' not in script
