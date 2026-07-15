#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
UPDATE = ROOT / "display/agent/jobs/update.py"
VERIFY = ROOT / "hub/services/deployment_verification.py"


def patch_update_handler():
    text = UPDATE.read_text(encoding="utf-8")

    import_line = (
        "from agent.install_version import "
        "record_installed_release"
    )

    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if line.startswith("from ")
            or line.startswith("import ")
        ]
        lines.insert(
            max(indexes, default=-1) + 1,
            import_line,
        )
        text = "\n".join(lines) + "\n"

    if "record_installed_release(" not in text:
        marker = (
            "            _install_dependencies(report)\n"
            "            _restart_and_verify(report)"
        )

        replacement = (
            "            _install_dependencies(report)\n"
            "\n"
            "            report(\n"
            '                "running",\n'
            "                80,\n"
            '                f"Recording installed release {target}",\n'
            "            )\n"
            "            record_installed_release(\n"
            "                APP_DIR,\n"
            "                target,\n"
            "                sha256=actual_sha256,\n"
            '                commit=payload.get("commit", ""),\n'
            "                package_url=package_url,\n"
            "            )\n"
            "\n"
            "            recorded = (\n"
            '                (APP_DIR / "VERSION")\n'
            "                .read_text(encoding=\"utf-8\")\n"
            "                .strip()\n"
            "            )\n"
            "            if recorded != target:\n"
            "                raise RuntimeError(\n"
            '                    f"Installed VERSION file reports {recorded}; "\n'
            '                    f"expected {target}"\n'
            "                )\n"
            "\n"
            "            _restart_and_verify(report)"
        )

        if marker not in text:
            raise SystemExit(
                "Could not find the verified deployment insertion point"
            )

        text = text.replace(
            marker,
            replacement,
            1,
        )

    UPDATE.write_text(text, encoding="utf-8")


def patch_verification():
    text = VERIFY.read_text(encoding="utf-8")

    import_line = (
        "from services.version_compare import versions_match"
    )

    if import_line not in text:
        lines = text.splitlines()
        indexes = [
            index
            for index, line in enumerate(lines)
            if line.startswith("from services.")
        ]
        lines.insert(
            max(indexes, default=0) + 1,
            import_line,
        )
        text = "\n".join(lines) + "\n"

    text = text.replace(
        "        if target and reported_version == target:",
        "        if target and versions_match(reported_version, target):",
    )

    if "versions_match(reported_version, target)" not in text:
        raise SystemExit(
            "Could not patch deployment version comparison"
        )

    VERIFY.write_text(text, encoding="utf-8")


def main():
    patch_update_handler()
    patch_verification()
    print(
        "v5.6.2 authoritative version integration applied."
    )


if __name__ == "__main__":
    main()
