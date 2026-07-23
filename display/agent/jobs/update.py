import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from urllib import request

from agent.config import APP_DIR
from agent.utils import run_command
from agent.version import get_version_info
from agent.install_version import record_installed_release


INSTALL_ROOT = APP_DIR.parent
RELEASES_DIR = INSTALL_ROOT / "releases"
BACKUPS_DIR = INSTALL_ROOT / "backups"
CURRENT_BACKUP = BACKUPS_DIR / "last-good-display"
RUNTIME_NAMES = {"venv", "media", "status", "logs", "config", "backups"}
SOURCE_NAMES = {"app", "agent", "scripts", "requirements.txt", "install.sh", "VERSION", "RELEASE"}


def handle_update_check(job, report):
    info = get_version_info()
    report(
        "success",
        100,
        " ".join(
            f"{key}={info.get(key)}"
            for key in ("tag", "commit", "branch", "dirty")
        ),
    )


def _download(url, destination, report):
    report("running", 20, "Downloading display software package")
    req = request.Request(url, headers={"User-Agent": "ChurchDisplayAgent/1"})
    with request.urlopen(req, timeout=120) as response:
        total = int(response.headers.get("Content-Length", "0") or 0)
        written = 0
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                handle.write(chunk)
                written += len(chunk)
                if total:
                    progress = 20 + min(20, int(written / total * 20))
                    report("running", progress, f"Downloaded {written}/{total} bytes")


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(archive_path, destination):
    destination = destination.resolve()
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if destination not in target.parents and target != destination:
                raise RuntimeError("Unsafe path in display release package")
        archive.extractall(destination)


def _validate_stage(stage, report):
    release_root = stage / "display-release"
    required = [
        release_root / "app" / "main.py",
        release_root / "agent" / "agent.py",
        release_root / "requirements.txt",
        release_root / "VERSION",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Package missing required files: " + ", ".join(missing))

    report("running", 48, "Compiling staged Python source")
    py_files = [
        str(path)
        for root_name in ("app", "agent")
        for path in (release_root / root_name).rglob("*.py")
    ]
    code, stdout, stderr = run_command(
        [str(APP_DIR / "venv" / "bin" / "python"), "-m", "py_compile", *py_files],
        timeout=120,
    )
    if code != 0:
        raise RuntimeError((stderr or stdout or "Python validation failed")[-1000:])

    return release_root


def _backup_current(report):
    report("running", 55, "Creating rollback backup")
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    if CURRENT_BACKUP.exists():
        shutil.rmtree(CURRENT_BACKUP)
    CURRENT_BACKUP.mkdir(parents=True)

    for name in SOURCE_NAMES:
        source = APP_DIR / name
        if not source.exists():
            continue
        target = CURRENT_BACKUP / name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def _restore_backup(report, reason):
    report("running", 92, "Restoring previous display software")
    for name in SOURCE_NAMES:
        active = APP_DIR / name
        if active.is_dir():
            shutil.rmtree(active)
        elif active.exists():
            active.unlink()

        backup = CURRENT_BACKUP / name
        if not backup.exists():
            continue
        if backup.is_dir():
            shutil.copytree(backup, active)
        else:
            shutil.copy2(backup, active)

    run_command(
        [
            str(APP_DIR / "venv" / "bin" / "python"),
            "-m",
            "pip",
            "install",
            "-r",
            str(APP_DIR / "requirements.txt"),
        ],
        timeout=300,
    )
    run_command(["sudo", "systemctl", "restart", "church-display.service"], timeout=45)
    report("failed", 100, f"{reason}; previous display software restored")


def _install_release(release_root, report):
    report("running", 62, "Installing display software")

    for name in SOURCE_NAMES:
        source = release_root / name
        if not source.exists():
            continue

        target = APP_DIR / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)

    scripts = APP_DIR / "scripts"
    if scripts.exists():
        for path in scripts.glob("*.sh"):
            path.chmod(path.stat().st_mode | 0o111)


def _install_dependencies(report):
    report("running", 72, "Updating Python dependencies")
    code, stdout, stderr = run_command(
        [
            str(APP_DIR / "venv" / "bin" / "python"),
            "-m",
            "pip",
            "install",
            "-r",
            str(APP_DIR / "requirements.txt"),
        ],
        timeout=300,
    )
    if code != 0:
        raise RuntimeError((stderr or stdout or "Dependency update failed")[-1000:])


def _restart_and_verify(report):
    report("running", 84, "Restarting display application")
    code, stdout, stderr = run_command(
        ["sudo", "systemctl", "restart", "church-display.service"],
        timeout=45,
    )
    if code != 0:
        raise RuntimeError((stderr or stdout or "Could not restart display service")[-500:])

    time.sleep(6)
    code, stdout, stderr = run_command(
        ["systemctl", "is-active", "church-display.service"],
        timeout=15,
    )
    if code != 0 or stdout.strip() != "active":
        raise RuntimeError("Display service did not become active after update")


def handle_deploy_update(job, report):
    payload = job.get("payload", {})
    target = (
        payload.get("target")
        or payload.get("tag")
        or payload.get("version")
        or ""
    ).strip()
    package_url = (payload.get("package_url") or "").strip()
    expected_sha256 = (payload.get("sha256") or "").strip().lower()
    dry_run = str(payload.get("dry_run", "true")).lower() not in {
        "0", "false", "no"
    }

    if not target or not package_url:
        report("failed", 100, "Missing target version or package URL")
        return

    report("running", 10, f"Preparing display update to {target}")

    RELEASES_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="church-display-update-") as temp_name:
        temp = Path(temp_name)
        archive = temp / "release.tar.gz"
        stage = temp / "stage"
        stage.mkdir()

        try:
            _download(package_url, archive, report)

            actual_sha256 = _sha256(archive)
            if expected_sha256 and actual_sha256 != expected_sha256:
                raise RuntimeError(
                    f"Checksum mismatch: expected {expected_sha256}, "
                    f"received {actual_sha256}"
                )

            report("running", 43, "Extracting display software")
            _safe_extract(archive, stage)
            release_root = _validate_stage(stage, report)

            version = (release_root / "VERSION").read_text().strip()
            if version != target.lstrip("v"):
                raise RuntimeError(
                    f"Package version {version} does not match target {target}"
                )

            if dry_run:
                report(
                    "success",
                    100,
                    f"DRY RUN OK: {target} downloaded, checksum verified, "
                    "and staged source compiled successfully",
                )
                return

            _backup_current(report)
            _install_release(release_root, report)
            _install_dependencies(report)

            report(
                "running",
                80,
                f"Recording installed release {target}",
            )
            record_installed_release(
                APP_DIR,
                target,
                sha256=actual_sha256,
                commit=payload.get("commit", ""),
                package_url=package_url,
            )

            recorded = (
                (APP_DIR / "VERSION")
                .read_text(encoding="utf-8")
                .strip()
            )
            if recorded != target:
                raise RuntimeError(
                    f"Installed VERSION file reports {recorded}; "
                    f"expected {target}"
                )

            _restart_and_verify(report)

            report(
                "success",
                100,
                f"Display software updated to {target}; "
                "display service verified. Agent will restart.",
            )

            # Restart after the success report reaches the Hub.
            subprocess.Popen(
                [
                    "sudo",
                    "systemctl",
                    "restart",
                    "church-display-agent.service",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        except Exception as exc:
            if CURRENT_BACKUP.exists() and not dry_run:
                _restore_backup(report, str(exc))
            else:
                report("failed", 100, str(exc))
