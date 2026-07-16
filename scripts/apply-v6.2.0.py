#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
BASE = ROOT / "hub/templates/base.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.bulk_operations import "
        "bulk_operations_bp"
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
        "    app.register_blueprint(bulk_operations_bp)"
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

        lines.insert(max(indexes) + 1, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")


def patch_navigation():
    text = BASE.read_text(encoding="utf-8")

    if "/bulk-operations/" in text:
        return

    marker = '<a href="/fleet-dashboard">Dashboard</a>'

    if marker not in text:
        raise SystemExit(
            "Could not find Fleet Dashboard navigation link"
        )

    replacement = (
        marker
        + '\n'
        + '<a href="/bulk-operations/">Bulk Operations</a>'
    )

    BASE.write_text(
        text.replace(marker, replacement, 1),
        encoding="utf-8",
    )


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v6.2.0 bulk operations */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")

    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_navigation()
    patch_css()
    print("v6.2.0 bulk operations applied.")


if __name__ == "__main__":
    main()
