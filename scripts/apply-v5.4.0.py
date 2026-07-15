#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
DETAILS_SERVICE = (
    ROOT
    / "hub"
    / "services"
    / "display_details.py"
)
DETAILS_TEMPLATE = (
    ROOT
    / "hub"
    / "templates"
    / "display_details.html"
)
DETAILS_APPEND = (
    ROOT
    / "hub"
    / "templates"
    / "display_details.upgrades.append.html"
)
CSS = ROOT / "hub" / "static" / "style.css"
CSS_APPEND = ROOT / "hub" / "static" / "style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")
    import_line = (
        "from routes.display_upgrades import "
        "display_upgrades_bp"
    )

    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(
            max(indexes, default=0) + 1,
            import_line,
        )
        text = "\n".join(lines) + "\n"

    register_line = (
        "    app.register_blueprint(display_upgrades_bp)"
    )
    if register_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]
        if not indexes:
            raise SystemExit(
                "Could not find blueprint registrations"
            )
        lines.insert(
            max(indexes) + 1,
            register_line,
        )
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")


def patch_details_service():
    text = DETAILS_SERVICE.read_text(
        encoding="utf-8"
    )

    import_line = (
        "from services.display_upgrades import "
        "display_upgrade_state"
    )
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if line.startswith("from services.")
        ]
        lines.insert(
            max(indexes, default=0) + 1,
            import_line,
        )
        text = "\n".join(lines) + "\n"

    marker = '"folder_error": folder_error,'
    if '"upgrade": display_upgrade_state(' not in text:
        replacement = (
            marker
            + "\n"
            + '        "upgrade": display_upgrade_state(\n'
            + "            display_id,\n"
            + '            fleet.get("version", ""),\n'
            + "        ),"
        )
        if marker not in text:
            raise SystemExit(
                "Could not find display details return marker"
            )
        text = text.replace(
            marker,
            replacement,
            1,
        )

    DETAILS_SERVICE.write_text(
        text,
        encoding="utf-8",
    )


def patch_details_template():
    text = DETAILS_TEMPLATE.read_text(
        encoding="utf-8"
    )

    if "Software Upgrade" in text:
        return

    block = DETAILS_APPEND.read_text(
        encoding="utf-8"
    )
    end = text.rfind("{% endblock %}")

    if end < 0:
        raise SystemExit(
            "Could not find display-details block ending"
        )

    DETAILS_TEMPLATE.write_text(
        text[:end] + block + "\n" + text[end:],
        encoding="utf-8",
    )
    DETAILS_APPEND.unlink()


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.4.0 safe upgrades */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += (
            "\n"
            + marker
            + "\n"
            + CSS_APPEND.read_text(
                encoding="utf-8"
            )
        )
        CSS.write_text(
            text,
            encoding="utf-8",
        )

    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_details_service()
    patch_details_template()
    patch_css()
    print("v5.4.0 Safe One-Click Upgrades applied.")


if __name__ == "__main__":
    main()
