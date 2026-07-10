#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_package(package_path, manifest_path=None):
    package_path = Path(package_path)

    if not package_path.exists():
        raise SystemExit(f"Package not found: {package_path}")

    if not zipfile.is_zipfile(package_path):
        raise SystemExit(f"Not a valid ZIP file: {package_path}")

    with zipfile.ZipFile(package_path) as zf:
        names = set(zf.namelist())
        required = {
            "church-display-platform/hub/app.py",
            "church-display-platform/display/agent/agent.py",
            "church-display-platform/release/build_release.py",
            "church-display-platform/manifest.json",
        }
        missing = sorted(required - names)
        if missing:
            raise SystemExit("Package missing required files: " + ", ".join(missing))

        embedded_manifest = json.loads(zf.read("church-display-platform/manifest.json").decode("utf-8"))

    digest = sha256_file(package_path)

    if manifest_path:
        manifest = json.loads(Path(manifest_path).read_text())
    else:
        manifest = embedded_manifest

    expected = manifest.get("package", {}).get("sha256")
    if expected and expected != digest:
        raise SystemExit(f"SHA256 mismatch: expected {expected}, got {digest}")
    if not expected:
        print("No external package checksum supplied; structural verification only.")

    print(f"OK: {package_path}")
    print(f"SHA256: {digest}")
    print(f"Version: {manifest.get('version')}")
    print(f"Commit: {manifest.get('commit_short')}")


def main():
    parser = argparse.ArgumentParser(description="Verify a Church Display release package.")
    parser.add_argument("package", help="Path to release ZIP")
    parser.add_argument("--manifest", help="Optional manifest path")
    args = parser.parse_args()
    verify_package(args.package, args.manifest)


if __name__ == "__main__":
    main()
