#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
BASE = ROOT / "hub/templates/base.html"
CSS = ROOT / "hub/static/style.css"
APPEND = ROOT / "hub/static/style.css.append"

def patch_app():
    text = APP.read_text(encoding="utf-8")
    imp = "from routes.command_center import command_center_bp"
    if imp not in text:
        lines = text.splitlines()
        idx = [i for i, line in enumerate(lines) if line.startswith("from routes.")]
        lines.insert(max(idx, default=0) + 1, imp)
        text = "\n".join(lines) + "\n"
    reg = "    app.register_blueprint(command_center_bp)"
    if reg not in text:
        lines = text.splitlines()
        idx = [i for i, line in enumerate(lines) if "app.register_blueprint(" in line]
        if not idx:
            raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(idx) + 1, reg)
        text = "\n".join(lines) + "\n"
    APP.write_text(text, encoding="utf-8")

def patch_nav():
    text = BASE.read_text(encoding="utf-8")
    if 'href="/command-center"' in text:
        return
    link = '<a href="/command-center">Command Center</a>'
    for marker in ['href="/"', 'href="/operations-center"', 'href="/operator/displays"']:
        i = text.find(marker)
        if i < 0:
            continue
        end = text.find("</a>", i)
        if end >= 0:
            end += 4
            BASE.write_text(text[:end] + "\n" + link + text[end:], encoding="utf-8")
            return

def patch_css():
    if not APPEND.exists():
        return
    marker = "/* v5.3.0 command center */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        CSS.write_text(text + "\n" + marker + "\n" + APPEND.read_text(encoding="utf-8"), encoding="utf-8")
    APPEND.unlink()

patch_app()
patch_nav()
patch_css()
print("v5.3.0 Command Center applied.")
