#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"
CSS = ROOT / "hub" / "static" / "style.css"
CSS_APPEND = ROOT / "hub" / "static" / "style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = "from routes.fleet_operations import fleet_operations_bp"
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(fleet_operations_bp)"
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

    if 'href="/fleet-operations"' in text:
        return

    candidates = [
        '<a href="/displays"',
        '<a href="/fleet"',
    ]

    for candidate in candidates:
        index = text.find(candidate)
        if index >= 0:
            end = text.find("</a>", index)
            if end >= 0:
                end += len("</a>")
                text = (
                    text[:end]
                    + '\n<a href="/fleet-operations">Fleet Operations</a>'
                    + text[end:]
                )
                BASE.write_text(text, encoding="utf-8")
                return

    raise SystemExit(
        "Could not locate Fleet/Displays navigation in hub/templates/base.html"
    )


def patch_css():
    if not CSS_APPEND.exists():
        return
    marker = "/* v4.5.0 fleet operations */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        text += "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")
    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_navigation()
    patch_css()
    print("v4.5.0 Fleet Operations applied.")


if __name__ == "__main__":
    main()
