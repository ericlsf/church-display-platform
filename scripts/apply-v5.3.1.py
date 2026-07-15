#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
DASHBOARD = ROOT / "hub" / "routes" / "dashboard.py"
BASE = ROOT / "hub" / "templates" / "base.html"


def patch_dashboard_route():
    text = DASHBOARD.read_text(encoding="utf-8")

    # Preserve the previous dashboard at /legacy-dashboard.
    text = text.replace(
        '@dashboard_bp.route("/")',
        '@dashboard_bp.route("/legacy-dashboard")',
    )
    text = text.replace(
        "@dashboard_bp.route('/')",
        "@dashboard_bp.route('/legacy-dashboard')",
    )

    DASHBOARD.write_text(text, encoding="utf-8")


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.command_center_home import "
        "command_center_home_bp"
    )
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = (
        "    app.register_blueprint(command_center_home_bp)"
    )
    if register_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]
        if not indexes:
            raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(indexes) + 1, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")


def patch_navigation():
    text = BASE.read_text(encoding="utf-8")

    # Rename the existing command-center link to Dashboard.
    text = text.replace(
        '<a href="/command-center">Command Center</a>',
        '<a href="/command-center">Dashboard</a>',
    )

    # Ensure logo/home links point to the new default root.
    text = text.replace(
        'href="/legacy-dashboard"',
        'href="/"',
    )

    BASE.write_text(text, encoding="utf-8")


def main():
    patch_dashboard_route()
    patch_app()
    patch_navigation()
    print("v5.3.1 default Command Center applied.")


if __name__ == "__main__":
    main()
