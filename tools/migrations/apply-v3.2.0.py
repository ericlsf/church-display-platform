#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"
STYLE = ROOT / "hub" / "static" / "style.css"
IGNORE = ROOT / ".gitignore"


def patch_app():
    text = APP.read_text()
    import_line = "from routes.management import management_bp, management_api_bp"
    if import_line not in text:
        text = import_line + "\n" + text

    for register_line in (
        "    app.register_blueprint(management_bp)",
        "    app.register_blueprint(management_api_bp)",
    ):
        if register_line not in text:
            lines = text.splitlines()
            indices = [i for i, line in enumerate(lines) if "app.register_blueprint(" in line]
            if not indices:
                raise SystemExit("Could not find blueprint registration block")
            lines.insert(max(indices) + 1, register_line)
            text = "\n".join(lines) + "\n"

    if '"/api/v1/management/"' not in text:
        anchor = '        "/api/v1/content/",'
        if anchor in text:
            text = text.replace(anchor, anchor + '\n        "/api/v1/management/",', 1)
        else:
            raise SystemExit("Could not find API prefix block")

    if '"/management"' not in text:
        old = '("/users", "/audit", "/system")'
        new = '("/users", "/audit", "/system", "/management")'
        if old in text:
            text = text.replace(old, new, 1)

    APP.write_text(text)


def patch_base():
    text = BASE.read_text()
    if 'href="/management"' in text:
        return

    link = '<a href="/management">Remote Management</a>'
    manage_marker = 'href="/system"'
    pos = text.find(manage_marker)
    if pos != -1:
        line_end = text.find("\n", pos)
        if line_end == -1:
            line_end = pos + len(manage_marker)
        text = text[:line_end] + "\n" + link + text[line_end:]
    else:
        nav_end = text.find("</nav>")
        if nav_end == -1:
            raise SystemExit("Could not find navigation in base.html")
        text = text[:nav_end] + link + "\n" + text[nav_end:]
    BASE.write_text(text)


def patch_style():
    style = STYLE.read_text() if STYLE.exists() else ""
    css = (ROOT / "hub" / "static" / "management.css").read_text()
    if ".remote-output" not in style:
        STYLE.write_text(style.rstrip() + "\n\n" + css.strip() + "\n")


def patch_ignore():
    lines = IGNORE.read_text().splitlines() if IGNORE.exists() else []
    entry = "hub/data/management/"
    if entry not in lines:
        lines.append(entry)
    IGNORE.write_text("\n".join(lines) + "\n")


def main():
    patch_app()
    patch_base()
    patch_style()
    patch_ignore()
    print("v3.2.0 applied")


if __name__ == "__main__":
    main()
