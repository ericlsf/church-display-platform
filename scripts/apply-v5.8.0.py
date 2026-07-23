#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
DETAILS = ROOT / "hub/templates/display_details.html"
APPEND = (
    ROOT
    / "hub/templates/display_details.rollback-watch.append.html"
)
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.automatic_rollback import "
        "automatic_rollback_bp"
    )
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = (
        "    app.register_blueprint(automatic_rollback_bp)"
    )
    if register_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]

        if not indexes:
            raise SystemExit(
                "Could not find blueprint registrations"
            )

        lines.insert(max(indexes) + 1, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")


def patch_template():
    text = DETAILS.read_text(encoding="utf-8")

    if "data-automatic-rollback" in text:
        return

    heading = text.find("<h2>Software Upgrade</h2>")
    if heading < 0:
        raise SystemExit(
            "Could not find Software Upgrade section"
        )

    start = text.rfind(
        '<div class="section',
        0,
        heading,
    )
    if start < 0:
        raise SystemExit(
            "Could not find Software Upgrade section start"
        )

    block = APPEND.read_text(encoding="utf-8")

    DETAILS.write_text(
        text[:start] + block + "\n\n" + text[start:],
        encoding="utf-8",
    )

    APPEND.unlink()


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.8.0 automatic rollback */"
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
    patch_template()
    patch_css()
    print(
        "v5.8.0 automatic verification rollback applied."
    )


if __name__ == "__main__":
    main()
