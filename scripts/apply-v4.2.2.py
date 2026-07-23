#!/usr/bin/env python3
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "display" / "app" / "main.py"
APP = ROOT / "hub" / "app.py"


def patch_player():
    text = MAIN.read_text(encoding="utf-8")

    # Remove any prior bad/duplicate cursor imports and calls.
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if line.strip() == "from app.cursor import hide_cursor":
            continue
        if line.strip() == "hide_cursor(app)":
            continue
        cleaned.append(line)

    lines = cleaned

    # Add import after the final import statement.
    import_line = "from app.cursor import hide_cursor"
    import_indexes = [
        index
        for index, line in enumerate(lines)
        if line.startswith("import ") or line.startswith("from ")
    ]
    insert_at = max(import_indexes, default=-1) + 1
    lines.insert(insert_at, import_line)

    # Find the real QApplication creation and preserve its indentation.
    app_line_index = None
    app_indent = ""
    pattern = re.compile(r"^(\s*)app\s*=\s*QApplication\s*\(")

    for index, line in enumerate(lines):
        match = pattern.search(line)
        if match:
            app_line_index = index
            app_indent = match.group(1)
            break

    if app_line_index is None:
        raise SystemExit(
            "Could not find `app = QApplication(...)` in display/app/main.py"
        )

    lines.insert(app_line_index + 1, f"{app_indent}hide_cursor(app)")

    MAIN.write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_hub_app():
    text = APP.read_text(encoding="utf-8")

    import_line = "from routes.provisioning import provisioning_bp"
    if import_line not in text:
        lines = text.splitlines()
        route_imports = [
            index
            for index, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(route_imports, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(provisioning_bp)"
    if register_line not in text:
        lines = text.splitlines()
        registrations = [
            index
            for index, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]
        if not registrations:
            raise SystemExit("Could not find blueprint registrations in hub/app.py")
        lines.insert(max(registrations) + 1, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")


def main():
    patch_player()
    patch_hub_app()
    print("v4.2.2 safe provisioning and cursor fix applied.")


if __name__ == "__main__":
    main()
