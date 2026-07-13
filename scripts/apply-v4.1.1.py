#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = "from routes.display_installer import display_installer_bp"
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(display_installer_bp)"
    if register_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]
        if not indexes:
            raise SystemExit("Could not find blueprint registrations in hub/app.py")
        lines.insert(max(indexes) + 1, register_line)
        text = "\n".join(lines) + "\n"

    entries = [
        '        "/install/display",',
        '        "/install/display/package.tar.gz",',
        '        "/install/display/command",',
    ]

    if entries[0] not in text:
        anchor = '        "/api/v1/preview",'
        if anchor not in text:
            raise SystemExit("Could not find public_paths in hub/app.py")
        text = text.replace(
            anchor,
            anchor + "\n" + "\n".join(entries),
            1,
        )

    APP.write_text(text, encoding="utf-8")


def main():
    patch_app()
    print("v4.1.1 Hub bootstrap installer registered.")


if __name__ == "__main__":
    main()
