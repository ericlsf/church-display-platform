#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "hub" / "static" / "style.css"
CSS_APPEND = ROOT / "hub" / "static" / "style.css.append"


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.0.1 display folder picker */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")

    CSS_APPEND.unlink()


def main():
    patch_css()
    print("v5.0.1 display folder picker applied.")


if __name__ == "__main__":
    main()
