#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "hub/templates/fleet_operations.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_template():
    text = TEMPLATE.read_text(encoding="utf-8")
    script = (
        '<script src="/static/'
        'fleet-operations-layout.js"></script>'
    )

    if script in text:
        return

    end = text.rfind("{% endblock %}")

    if end < 0:
        raise SystemExit(
            "Could not find Fleet Operations block ending"
        )

    text = (
        text[:end]
        + script
        + "\n"
        + text[end:]
    )

    TEMPLATE.write_text(
        text,
        encoding="utf-8",
    )


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = (
        "/* v6.4.2 Fleet Operations grouped controls */"
    )
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
    patch_template()
    patch_css()

    print(
        "v6.4.2 Fleet Operations control groups applied."
    )


if __name__ == "__main__":
    main()
