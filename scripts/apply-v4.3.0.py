#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = "from routes.display_releases import display_releases_bp"
    if import_line not in text:
        lines = text.splitlines()
        route_imports = [
            i for i, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(route_imports, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(display_releases_bp)"
    if register_line not in text:
        lines = text.splitlines()
        registrations = [
            i for i, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]
        if not registrations:
            raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(registrations) + 1, register_line)
        text = "\n".join(lines) + "\n"

    api_prefix = '        "/api/v1/display-releases/",'
    if api_prefix not in text:
        anchor = '        "/api/v1/content/",'
        if anchor not in text:
            raise SystemExit("Could not find API prefix list")
        text = text.replace(anchor, anchor + "\n" + api_prefix, 1)

    APP.write_text(text, encoding="utf-8")


def main():
    patch_app()
    print("v4.3.0 Hub package deployment registered.")


if __name__ == "__main__":
    main()
