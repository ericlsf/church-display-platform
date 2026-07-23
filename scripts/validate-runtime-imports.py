#!/usr/bin/env python3
"""Import every active Hub module without starting the HTTP server."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "hub"

sys.path.insert(0, str(HUB))


def package_modules(package_name: str) -> list[str]:
    package = importlib.import_module(package_name)
    names = [package_name]

    if hasattr(package, "__path__"):
        for module in pkgutil.walk_packages(
            package.__path__,
            prefix=f"{package_name}.",
        ):
            names.append(module.name)

    return names


def main() -> int:
    modules = []
    for package_name in ("routes", "services"):
        modules.extend(package_modules(package_name))

    failures: list[tuple[str, str]] = []

    for module_name in sorted(set(modules)):
        try:
            importlib.import_module(module_name)
            print(f"PASS  {module_name}")
        except Exception as exc:
            failures.append(
                (module_name, f"{type(exc).__name__}: {exc}")
            )
            print(
                f"FAIL  {module_name}: "
                f"{type(exc).__name__}: {exc}"
            )

    if failures:
        print()
        print(f"Runtime import validation failed: {len(failures)} module(s)")
        return 1

    print()
    print(f"Runtime import validation passed: {len(set(modules))} module(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
