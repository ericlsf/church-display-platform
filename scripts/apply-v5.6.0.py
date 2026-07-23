#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "hub/app.py"
DETAILS = ROOT / "hub/templates/display_details.html"
APPEND = (
    ROOT
    / "hub/templates/display_details.verification.append.html"
)
CSS = ROOT / "hub/static/style.css"
CSS_APPEND = ROOT / "hub/static/style.css.append"
DEPLOY_CANDIDATES = [
    ROOT / "display/agent/jobs/deploy.py",
    ROOT / "display/agent/jobs/deploy_update.py",
    ROOT / "display/agent/deploy.py",
    ROOT / "display/agent/dispatcher.py",
]


def patch_app():
    text = APP.read_text(encoding="utf-8")

    import_line = (
        "from routes.deployment_verification import "
        "deployment_verification_bp"
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
        "    app.register_blueprint(deployment_verification_bp)"
    )

    if register_line not in text:
        lines = text.splitlines()
        indexes = [
            i for i, line in enumerate(lines)
            if "app.register_blueprint(" in line
        ]

        if not indexes:
            raise SystemExit(
                "Could not find blueprint registrations"
            )

        lines.insert(max(indexes) + 1, register_line)
        text = "\n".join(lines) + "\n"

    APP.write_text(text, encoding="utf-8")


def patch_display_template():
    text = DETAILS.read_text(encoding="utf-8")

    if "data-deployment-verification" in text:
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

    depth = 0
    pos = start
    end = -1

    while pos < len(text):
        next_open = text.find("<div", pos)
        next_close = text.find("</div>", pos)

        if next_close < 0:
            break

        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            pos = next_close + len("</div>")

            if depth == 0:
                end = pos
                break

    if end < 0:
        raise SystemExit(
            "Could not isolate Software Upgrade section"
        )

    block = APPEND.read_text(encoding="utf-8")

    DETAILS.write_text(
        text[:end] + "\n" + block + text[end:],
        encoding="utf-8",
    )

    APPEND.unlink()


def patch_deployment_handler():
    candidates = [
        path for path in DEPLOY_CANDIDATES
        if path.exists()
    ]

    if not candidates:
        print(
            "WARN  No known deployment handler found. "
            "The authoritative version module and Hub verification "
            "were installed, but deployment recording requires "
            "manual integration."
        )
        return

    for path in candidates:
        text = path.read_text(encoding="utf-8")

        if "record_installed_release(" in text:
            print(
                f"PASS  Deployment recording already present: {path}"
            )
            return

        # Safe integration point: immediately before a successful return
        # containing status=success or the final service restart.
        import_line = (
            "from agent.install_version import "
            "record_installed_release"
        )

        if import_line not in text:
            lines = text.splitlines()
            indexes = [
                i for i, line in enumerate(lines)
                if line.startswith("from ")
                or line.startswith("import ")
            ]
            lines.insert(
                max(indexes, default=-1) + 1,
                import_line,
            )
            text = "\n".join(lines) + "\n"

        marker = 'systemctl restart church-display-agent.service'
        index = text.find(marker)

        if index < 0:
            continue

        line_start = text.rfind("\n", 0, index) + 1
        indent = text[line_start:index]
        indent = indent[: len(indent) - len(indent.lstrip())]

        block = (
            indent
            + "record_installed_release(\n"
            + indent
            + "    Path(__file__).resolve().parents[2],\n"
            + indent
            + '    payload.get("target", ""),\n'
            + indent
            + '    sha256=payload.get("sha256", ""),\n'
            + indent
            + '    commit=payload.get("commit", ""),\n'
            + indent
            + '    package_url=payload.get("package_url", ""),\n'
            + indent
            + ")\n"
        )

        text = text[:line_start] + block + text[line_start:]

        if "from pathlib import Path" not in text:
            text = (
                "from pathlib import Path\n"
                + text
            )

        path.write_text(text, encoding="utf-8")
        print(
            f"PASS  Added installed-version recording to {path}"
        )
        return

    print(
        "WARN  Deployment handler found, but no safe automatic "
        "integration point was identified."
    )


def patch_css():
    if not CSS_APPEND.exists():
        return

    marker = "/* v5.6.0 deployment verification */"
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
    patch_display_template()
    patch_deployment_handler()
    patch_css()
    print("v5.6.0 self-verifying upgrades applied.")


if __name__ == "__main__":
    main()
