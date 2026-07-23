#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub" / "app.py"
BASE = ROOT / "hub" / "templates" / "base.html"
CSS = ROOT / "hub" / "static" / "style.css"
CSS_APPEND = ROOT / "hub" / "static" / "style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = "from routes.rollouts import rollouts_bp"
    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if line.startswith("from routes.")
        ]
        lines.insert(max(indexes, default=0) + 1, import_line)
        text = "\n".join(lines) + "\n"

    register_line = "    app.register_blueprint(rollouts_bp)"
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


def patch_navigation():
    text = BASE.read_text(encoding="utf-8")
    if 'href="/rollouts"' in text:
        return

    link = '<a href="/rollouts">Scheduled Rollouts</a>'
    for marker in [
        'href="/deployments"',
        'href="/operations-center"',
        'href="/fleet-operations"',
    ]:
        index = text.find(marker)
        if index < 0:
            continue
        end = text.find("</a>", index)
        if end >= 0:
            end += len("</a>")
            BASE.write_text(
                text[:end] + "\n" + link + text[end:],
                encoding="utf-8",
            )
            return


def patch_css():
    if not CSS_APPEND.exists():
        return
    marker = "/* v4.7.0 scheduled rollouts */"
    text = CSS.read_text(encoding="utf-8")
    if marker not in text:
        text += "\n" + marker + "\n" + CSS_APPEND.read_text(encoding="utf-8")
        CSS.write_text(text, encoding="utf-8")
    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_navigation()
    patch_css()
    print("v4.7.0 Scheduled Rollouts applied.")


if __name__ == "__main__":
    main()
