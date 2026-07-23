#!/usr/bin/env python3
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
DISPATCHER = ROOT / "display/agent/dispatcher.py"
DETAILS = ROOT / "hub/templates/display_details.html"
APPEND = ROOT / "hub/templates/display_details.timeline.append.html"
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.deployment_timeline import "
        "deployment_timeline_bp"
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
        "    app.register_blueprint(deployment_timeline_bp)"
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


def patch_dispatcher_import(text):
    if re.search(
        r"from\s+agent\.jobs\s+import[^\n]*\brollback\b",
        text,
    ):
        return text

    pattern = re.compile(
        r"^(from\s+agent\.jobs\s+import\s+)([^\n]+)$",
        re.MULTILINE,
    )
    match = pattern.search(text)

    if not match:
        raise SystemExit(
            "Could not find agent.jobs import in dispatcher.py"
        )

    modules = [
        item.strip()
        for item in match.group(2).split(",")
        if item.strip()
    ]

    if "rollback" not in modules:
        insert_at = (
            modules.index("preview") + 1
            if "preview" in modules
            else len(modules)
        )
        modules.insert(insert_at, "rollback")

    replacement = (
        match.group(1)
        + ", ".join(modules)
    )

    return (
        text[:match.start()]
        + replacement
        + text[match.end():]
    )


def patch_dispatcher_branch(text):
    if re.search(
        r"""job_type\s*==\s*["']rollback_update["']""",
        text,
    ):
        return text

    pattern = re.compile(
        r"""(?P<indent>^[ \t]*)elif\s+job_type\s*==\s*["']deploy_update["']\s*:\s*\n"""
        r"""(?P<body_indent>[ \t]+)(?P<call>update\.handle_deploy_update\s*\(\s*job\s*,\s*report\s*\)\s*)""",
        re.MULTILINE,
    )

    match = pattern.search(text)

    if not match:
        raise SystemExit(
            "Could not identify deploy_update branch in dispatcher.py"
        )

    branch = (
        match.group(0)
        + "\n"
        + match.group("indent")
        + 'elif job_type == "rollback_update":\n'
        + match.group("body_indent")
        + "rollback.handle_rollback_update(job, report)"
    )

    return (
        text[:match.start()]
        + branch
        + text[match.end():]
    )


def patch_dispatcher():
    text = DISPATCHER.read_text(encoding="utf-8")
    text = patch_dispatcher_import(text)
    text = patch_dispatcher_branch(text)
    DISPATCHER.write_text(text, encoding="utf-8")


def patch_template():
    text = DETAILS.read_text(encoding="utf-8")

    if "data-deployment-timeline" in text:
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

    marker = "/* v5.7.0 deployment timeline */"
    text = CSS.read_text(encoding="utf-8")

    if marker not in text:
        text += (
            "\n"
            + marker
            + "\n"
            + CSS_APPEND.read_text(encoding="utf-8")
        )
        CSS.write_text(text, encoding="utf-8")

    CSS_APPEND.unlink()


def main():
    patch_app()
    patch_dispatcher()
    patch_template()
    patch_css()
    print(
        "v5.7.1 dispatcher integration fix applied."
    )


if __name__ == "__main__":
    main()
