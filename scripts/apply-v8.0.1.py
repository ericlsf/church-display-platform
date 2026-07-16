#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "hub/templates/base.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_base():
    text = BASE.read_text(encoding="utf-8")
    script = (
        '<script src="/static/'
        'breadcrumb-v8.1.js"></script>'
    )

    if script in text:
        return

    existing = (
        '<script src="/static/'
        'navigation-v8.js"></script>'
    )

    if existing in text:
        text = text.replace(
            existing,
            existing + "\n" + script,
            1,
        )
    else:
        close = text.lower().rfind("</body>")

        if close < 0:
            raise SystemExit(
                "Could not find </body> in base.html"
            )

        text = (
            text[:close]
            + "\n"
            + script
            + "\n"
            + text[close:]
        )

    BASE.write_text(
        text,
        encoding="utf-8",
    )


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = (
        "/* v8.0.1 breadcrumb layout fix */"
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
    patch_base()
    patch_css()

    print(
        "v8.0.1 breadcrumb layout fix applied."
    )


if __name__ == "__main__":
    main()
