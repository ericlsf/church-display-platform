#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"
CSS = ROOT / "hub" / "static" / "style.css"
CSS_APPEND = ROOT / "hub" / "static" / "style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = "from routes.notifications import notifications_bp"
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(notifications_bp)"
    if register_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]
        if not indexes:
            raise SystemExit("Could not find blueprint registrations")
        lines.insert(max(indexes) + 1, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")


def patch_navigation():
    text = BASE.read_text(encoding="utf-8")

    if 'data-notification-link' not in text:
        link = (
            '<a class="notification-nav" data-notification-link '
            'href="/notifications" aria-label="Notifications">'
            'Notifications'
            '<span class="notification-badge" '
            'data-notification-badge hidden>0</span>'
            '</a>'
        )

        marker = 'href="/audit"'
        index = text.find(marker)
        if index >= 0:
            end = text.find("</a>", index)
            if end >= 0:
                end += len("</a>")
                text = text[:end] + "\n" + link + text[end:]
        else:
            body_end = text.rfind("</body>")
            if body_end >= 0:
                text = text[:body_end] + link + "\n" + text[body_end:]

    script_tag = '<script src="/static/notifications.js"></script>'
    if script_tag not in text:
        body_end = text.rfind("</body>")
        if body_end >= 0:
            text = text[:body_end] + script_tag + "\n" + text[body_end:]

    BASE.write_text(text, encoding="utf-8")


def patch_css():
    if not CSS_APPEND.exists():
        return
    marker = "/* v4.10.0 notification center */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        text += "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")
    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_navigation()
    patch_css()
    print("v4.10.0 Notification Center applied.")


if __name__ == "__main__":
    main()
