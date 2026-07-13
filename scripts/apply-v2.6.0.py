#!/usr/bin/env python3
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / 'hub' / 'app.py'
BASE = ROOT / 'hub' / 'templates' / 'base.html'
GITIGNORE = ROOT / '.gitignore'


def patch_app():
    text = APP.read_text()
    for line in [
        'import os',
        'from flask import g, redirect, request, session, url_for',
        'from routes.auth import auth_bp',
        'from services.auth import init_auth_db, load_current_user, log_audit, user_count',
    ]:
        if line not in text:
            text = line + '\n' + text

    register = '    app.register_blueprint(auth_bp)'
    if register not in text:
        lines = text.splitlines()
        positions = [i for i, line in enumerate(lines) if 'app.register_blueprint(' in line]
        if not positions:
            raise SystemExit('Could not find blueprint registrations in hub/app.py')
        lines.insert(max(positions) + 1, register)
        text = '\n'.join(lines) + '\n'

    marker = '# v2.6.0 auth hooks'
    if marker not in text:
        insert = '''
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

        if request.path.startswith(("/users", "/audit", "/system")) and role != "admin":
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
        return {"current_user": getattr(g, "current_user", None)}
'''
        if '    return app' not in text:
            raise SystemExit("Could not find 'return app' in hub/app.py")
        text = text.replace('    return app', insert + '\n    return app', 1)

    APP.write_text(text)


def patch_base():
    if not BASE.exists():
        return
    text = BASE.read_text()
    if 'href="/users"' not in text:
        link = '''{% if current_user and current_user.role == 'admin' %}<a class="{{ 'active' if active == 'users' else '' }}" href="/users">Users</a><a class="{{ 'active' if active == 'audit' else '' }}" href="/audit">Audit</a>{% endif %}'''
        nav_end = text.find('</nav>')
        if nav_end != -1:
            text = text[:nav_end] + link + '\n' + text[nav_end:]
    if 'action="/logout"' not in text:
        logout = '''{% if current_user %}<form method="POST" action="/logout" style="position:fixed;right:16px;top:12px;z-index:1000;"><button type="submit">Sign Out</button></form>{% endif %}'''
        body_end = text.find('</body>')
        if body_end != -1:
            text = text[:body_end] + logout + '\n' + text[body_end:]
    BASE.write_text(text)


def patch_gitignore():
    lines = GITIGNORE.read_text().splitlines() if GITIGNORE.exists() else []
    for item in ['hub/data/auth.db', 'hub/data/auth.db-*']:
        if item not in lines:
            lines.append(item)
    GITIGNORE.write_text('\n'.join(lines) + '\n')


def patch_env():
    env_dir = Path('/etc/church-display')
    env_file = env_dir / 'hub.env'
    env_dir.mkdir(parents=True, exist_ok=True)
    existing = env_file.read_text() if env_file.exists() else ''
    if 'CHURCH_DISPLAY_SECRET_KEY=' not in existing:
        with env_file.open('a') as handle:
            handle.write(f'CHURCH_DISPLAY_SECRET_KEY={secrets.token_urlsafe(48)}\n')


def main():
    patch_app(); patch_base(); patch_gitignore(); patch_env()
    print('v2.6.0 security patch applied.')

if __name__ == '__main__': main()
