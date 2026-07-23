#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
ALERT_ROUTE = ROOT / "hub/routes/alert_center.py"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.alert_acknowledgements import "
        "alert_acknowledgements_bp"
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
        "    app.register_blueprint("
        "alert_acknowledgements_bp)"
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

    text = text.replace(
        "from services.alert_center import build_alert_center",
        (
            "from services.alert_center_state import "
            "build_alert_center_state"
        ),
    )

    text = text.replace(
        "build_alert_center()",
        "build_alert_center_state()",
    )

    if "build_alert_center_state" not in text:
        raise SystemExit(
            "Could not patch Alert Center state builder"
        )

    ALERT_ROUTE.write_text(
        text,
        encoding="utf-8",
    )


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v6.5.0 alert acknowledgement */"
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
    patch_css()

    print(
        "v6.5.0 alert acknowledgement applied."
    )


if __name__ == "__main__":
    main()
