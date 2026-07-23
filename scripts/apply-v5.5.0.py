#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
DETAILS_SERVICE = ROOT / "hub/services/display_details.py"
DETAILS_TEMPLATE = ROOT / "hub/templates/display_details.html"
DETAILS_APPEND = ROOT / "hub/templates/display_details.health.append.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")
    import_line = (
        "from routes.health_diagnostics import "
        "health_diagnostics_bp"
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
        "    app.register_blueprint(health_diagnostics_bp)"
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


def patch_details_service():
    text = DETAILS_SERVICE.read_text(encoding="utf-8")
    import_line = (
        "from services.health_diagnostics import "
        "build_health_diagnostics"
    )

    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if line.startswith("from services.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    if '"health_diagnostics": build_health_diagnostics(' not in text:
        marker = '"fleet": fleet,'
        if marker not in text:
            raise SystemExit("Could not find fleet return value")
        replacement = (
            marker
            + "\n"
            + '        "health_diagnostics": '
            + "build_health_diagnostics(fleet),"
        )
        text = text.replace(marker, replacement, 1)

    DETAILS_SERVICE.write_text(text, encoding="utf-8")


def patch_details_template():
    text = DETAILS_TEMPLATE.read_text(encoding="utf-8")

    if 'id="health-diagnostics"' in text:
        return

    block = DETAILS_APPEND.read_text(encoding="utf-8")

    target = text.find("<h2>Recent Jobs</h2>")
    if target < 0:
        raise SystemExit("Could not find Recent Jobs section")

    target_start = text.rfind('<div class="section"', 0, target)
    if target_start < 0:
        raise SystemExit("Could not locate Recent Jobs section start")

    DETAILS_TEMPLATE.write_text(
        text[:target_start] + block + "\n\n" + text[target_start:],
        encoding="utf-8",
    )
    DETAILS_APPEND.unlink()


def patch_content_anchor():
    text = DETAILS_TEMPLATE.read_text(encoding="utf-8")
    heading = text.find("<h2>Content & Overlay</h2>")
    if heading >= 0:
        start = text.rfind('<div class="section"', 0, heading)
        if start >= 0:
            opening_end = text.find(">", start)
            opening = text[start:opening_end + 1]
            if 'id="content-settings"' not in opening:
                text = (
                    text[:opening_end]
                    + ' id="content-settings"'
                    + text[opening_end:]
                )
                DETAILS_TEMPLATE.write_text(text, encoding="utf-8")


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.5.0 health diagnostics */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        text += "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")
    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_details_service()
    patch_details_template()
    patch_content_anchor()
    patch_css()
    print("v5.5.0 Health Diagnostics applied.")


if __name__ == "__main__":
    main()
