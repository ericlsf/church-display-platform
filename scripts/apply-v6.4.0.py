#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
BASE = ROOT / "hub/templates/base.html"
FLEET_OPS = ROOT / "hub/services/fleet_operations.py"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"

def patch_app():
    text = APP.read_text(encoding="utf-8")
    import_line = "from routes.alert_center import alert_center_bp"
    if import_line not in text:
        lines = text.splitlines()
        indexes = [i for i, line in enumerate(lines) if line.startswith("from routes.")]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(alert_center_bp)"
    if register_line not in text:
        lines = text.splitlines()
        indexes = [i for i, line in enumerate(lines) if "app.register_blueprint(" in line]
        if not indexes:
            raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(indexes) + 1, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")

def patch_navigation():
    text = BASE.read_text(encoding="utf-8")
    if 'href="/alerts/"' in text:
        return

    marker = '<a href="/bulk-operations/">Bulk Operations</a>'
    if marker not in text:
        marker = '<a href="/fleet-dashboard">Dashboard</a>'
    if marker not in text:
        raise SystemExit("Could not find dashboard navigation insertion point")

    replacement = marker + '\n<a href="/alerts/">Alert Center</a>'
    BASE.write_text(text.replace(marker, replacement, 1), encoding="utf-8")

def patch_fleet_operations():
    text = FLEET_OPS.read_text(encoding="utf-8")

    if "def _fleet_rows_base(" not in text:
        if "def fleet_rows(" not in text:
            raise SystemExit("Could not find fleet_rows definition")
        text = text.replace("def fleet_rows(", "def _fleet_rows_base(", 1)

    wrapper_marker = "# v6.4.0 authoritative fleet-row wrapper"
    if wrapper_marker not in text:
        wrapper = (
            "\n\n# v6.4.0 authoritative fleet-row wrapper\n"
            "def fleet_rows(*args, **kwargs):\n"
            "    from services.fleet_truth import enrich_fleet_rows\n\n"
            "    return enrich_fleet_rows(\n"
            "        _fleet_rows_base(*args, **kwargs)\n"
            "    )\n"
        )
        text += wrapper

    FLEET_OPS.write_text(text, encoding="utf-8")

def patch_css():
    if not CSS_APPEND.exists():
        return
    marker = "/* v6.4.0 alert center */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        text += "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")
    CSS_APPEND.unlink()

def main():
    patch_app()
    patch_navigation()
    patch_fleet_operations()
    patch_css()
    print("v6.4.0 alert center and authoritative media count applied.")

if __name__ == "__main__":
    main()
