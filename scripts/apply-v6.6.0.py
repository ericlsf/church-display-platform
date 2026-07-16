#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
BASE = ROOT / "hub/templates/base.html"
ALERT_ROUTE = ROOT / "hub/routes/alert_center.py"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.alert_rules import "
        "alert_rules_bp"
    )

    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i
            for i, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(
            max(indexes, default=0) + 1,
            import_line,
        )
        text = "\n".join(lines) + "\n"

    register_line = (
        "    app.register_blueprint(alert_rules_bp)"
    )

    if register_line not in text:
        lines = text.splitlines()
        indexes = [
            i
            for i, line in enumerate(lines)
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


def patch_alert_route():
    text = ALERT_ROUTE.read_text(encoding="utf-8")

    import_line = (
        "from services.alert_policy import "
        "apply_alert_policy"
    )

    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i
            for i, line in enumerate(lines)
            if line.startswith("from services.")
        ]
        lines.insert(
            max(indexes, default=0) + 1,
            import_line,
        )
        text = "\n".join(lines) + "\n"

    text = text.replace(
        "build_alert_center_state()",
        (
            "apply_alert_policy("
            "build_alert_center_state())"
        ),
    )

    ALERT_ROUTE.write_text(
        text,
        encoding="utf-8",
    )


def patch_navigation():
    text = BASE.read_text(encoding="utf-8")

    if 'href="/alerts/rules/"' in text:
        return

    marker = '<a href="/alerts/">Alert Center</a>'

    if marker not in text:
        raise SystemExit(
            "Could not find Alert Center navigation link"
        )

    text = text.replace(
        marker,
        (
            marker
            + '\n'
            + '<a href="/alerts/rules/">Alert Rules</a>'
        ),
        1,
    )

    BASE.write_text(
        text,
        encoding="utf-8",
    )


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v6.6.0 alert rules */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += (
            "\n"
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
    patch_alert_route()
    patch_navigation()
    patch_css()

    print("v6.6.0 alert rules applied.")


if __name__ == "__main__":
    main()
