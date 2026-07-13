from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"
GITIGNORE = ROOT / ".gitignore"


def patch_app():
    text = APP.read_text()
    imports = [
        "from routes.setup import setup_bp",
        "from routes.system import system_bp",
    ]
    for line in imports:
        if line not in text:
            insert = text.find("\n\n")
            text = text[:insert] + "\n" + line + text[insert:]

    marker = "    return app"
    registrations = [
        "    app.register_blueprint(setup_bp)",
        "    app.register_blueprint(system_bp)",
    ]
    for line in registrations:
        if line not in text:
            text = text.replace(marker, line + "\n" + marker)
    APP.write_text(text)


def patch_base():
    text = BASE.read_text()
    links = [
        ('href="/setup"', '            <a class="{{ \'active\' if active == \'setup\' else \'\' }}" href="/setup">Setup</a>\n'),
        ('href="/system"', '            <a class="{{ \'active\' if active == \'system\' else \'\' }}" href="/system">System</a>\n'),
    ]
    for needle, link in links:
        if needle not in text:
            text = text.replace("        </nav>", link + "        </nav>")
    BASE.write_text(text)


def patch_gitignore():
    existing = GITIGNORE.read_text() if GITIGNORE.exists() else ""
    entries = ["hub/data/", "hub/config/.setup-complete", "*.tar.gz"]
    for entry in entries:
        if entry not in existing.splitlines():
            existing += ("\n" if existing and not existing.endswith("\n") else "") + entry + "\n"
    GITIGNORE.write_text(existing)


patch_app()
patch_base()
patch_gitignore()
print("v2.5.0 production-readiness routes and navigation applied")
