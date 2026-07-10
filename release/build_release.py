#!/usr/bin/env python3
import argparse
from pathlib import Path

from changelog import render_release_notes
from manifest import build_manifest, sha256_file, write_manifest
from package import build_source_zip


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "release" / "dist"


def normalize_version(version):
    version = (version or "").strip()
    if not version:
        raise SystemExit("Version is required. Example: ./release/build_release.py v1.8.0")
    if not version.startswith("v"):
        version = "v" + version
    return version


def write_sha256s(path, entries):
    lines = [f"{digest}  {name}" for name, digest in entries]
    path.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build a Church Display Platform release package.")
    parser.add_argument("version", nargs="?", help="Release version, for example v1.8.0")
    args = parser.parse_args()

    version = normalize_version(args.version)
    DIST.mkdir(parents=True, exist_ok=True)

    package_name = f"church-display-platform-{version}.zip"
    package_path = DIST / package_name
    manifest_path = DIST / "manifest.json"
    notes_path = DIST / "release_notes.md"
    sums_path = DIST / "SHA256SUMS"

    # First pass manifest goes inside the package before the final package hash exists.
    embedded_manifest = build_manifest(version)
    extra_files = {
        "manifest.json": __import__("json").dumps(embedded_manifest, indent=2) + "\n",
    }

    build_source_zip(package_path, extra_files=extra_files)

    package_sha = sha256_file(package_path)
    package_size = package_path.stat().st_size

    final_manifest = build_manifest(
        version,
        package_name=package_name,
        package_sha256=package_sha,
        package_size=package_size,
    )

    notes = render_release_notes(version, final_manifest)
    write_manifest(manifest_path, final_manifest)
    notes_path.write_text(notes)
    write_sha256s(sums_path, [
        (package_name, package_sha),
        ("manifest.json", sha256_file(manifest_path)),
        ("release_notes.md", sha256_file(notes_path)),
    ])

    # Embed a package-local manifest and notes. The embedded manifest intentionally
    # leaves the package checksum blank because a ZIP cannot contain its own final
    # checksum without changing that checksum. The external manifest is authoritative
    # for package SHA256 verification.
    embedded_final_manifest = dict(final_manifest)
    embedded_final_manifest["package"] = dict(final_manifest["package"])
    embedded_final_manifest["package"]["sha256"] = ""

    extra_files = {
        "manifest.json": __import__("json").dumps(embedded_final_manifest, indent=2) + "\n",
        "release_notes.md": notes_path.read_text(),
    }
    build_source_zip(package_path, extra_files=extra_files)

    # Final package hash after embedding manifest/notes.
    package_sha = sha256_file(package_path)
    final_manifest["package"]["sha256"] = package_sha
    final_manifest["package"]["size_bytes"] = package_path.stat().st_size
    write_manifest(manifest_path, final_manifest)
    write_sha256s(sums_path, [
        (package_name, package_sha),
        ("manifest.json", sha256_file(manifest_path)),
        ("release_notes.md", sha256_file(notes_path)),
    ])

    print("Release built:")
    print(f"  {package_path}")
    print(f"  {manifest_path}")
    print(f"  {notes_path}")
    print(f"  {sums_path}")


if __name__ == "__main__":
    main()
