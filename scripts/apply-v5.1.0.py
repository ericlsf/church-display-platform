#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
DETAILS = ROOT / "hub" / "templates" / "display_details.html"
APPEND = ROOT / "hub" / "templates" / "display_details.activity.append.html"
CSS = ROOT / "hub" / "static" / "style.css"
CSS_APPEND = ROOT / "hub" / "static" / "style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.operator_experience import "
        "operator_experience_bp"
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
        "    app.register_blueprint(operator_experience_bp)"
    )
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


def patch_display_details():
    text = DETAILS.read_text(encoding="utf-8")
    marker = "id=\"display-activity\""

    if marker in text:
        return

    block = APPEND.read_text(encoding="utf-8")
    end = text.rfind("{% endblock %}")
    if end < 0:
        raise SystemExit(
            "Could not find content block ending in display_details.html"
        )

    DETAILS.write_text(
        text[:end] + block + "\n" + text[end:],
        encoding="utf-8",
    )
    APPEND.unlink()


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.1.0 operator experience */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        text += "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")
    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_display_details()
    patch_css()
    print("v5.1.0 Operator Experience applied.")


if __name__ == "__main__":
    main()
