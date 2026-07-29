import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from urllib import parse, request

from agent.config import APP_DIR
from agent.hub_connection import open_hub
from agent.utils import run_command
from agent.version import get_version_info
from agent.install_version import record_installed_release
from agent import update_state


INSTALL_ROOT = APP_DIR.parent
RELEASES_DIR = INSTALL_ROOT / "releases"
BACKUPS_DIR = INSTALL_ROOT / "backups"
CURRENT_BACKUP = BACKUPS_DIR / "last-good-display"
RUNTIME_NAMES = {"venv", "media", "status", "logs", "config", "backups"}
SOURCE_NAMES = {"app", "agent", "scripts", "recovery", "systemd", "requirements.txt", "install.sh", "VERSION", "RELEASE"}


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


def _download(url, destination, report, expected_sha256=""):
    report("running", 20, "Downloading display software package")
    parsed = parse.urlsplit(url)
    release_path = parsed.path
    if parsed.query:
        release_path += f"?{parsed.query}"

    expected_sha256 = (expected_sha256 or "").strip().lower()

    def valid_release_response(response):
        content_type = (
            response.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )
        if content_type not in {
            "application/gzip",
            "application/x-gzip",
            "application/octet-stream",
        }:
            return False
        reported_checksum = (
            response.headers.get("X-Checksum-SHA256", "")
            .strip()
            .lower()
        )
        return not (
            expected_sha256
            and reported_checksum
            and reported_checksum != expected_sha256
        )

    headers = {
        "User-Agent": "ChurchDisplayAgent/1",
        "Accept": "application/octet-stream, application/gzip",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
    }
    if release_path.startswith("/api/v1/display-releases/"):
        response_context = open_hub(
            release_path,
            headers=headers,
            timeout=120,
            validate_response=valid_release_response,
        )
    else:
        req = request.Request(url, headers=headers)
        response_context = request.urlopen(req, timeout=120)
    with response_context as response:
        if not valid_release_response(response):
            raise RuntimeError(
                "Display update URL did not return a software package "
                f"(received {response.headers.get('Content-Type', 'unknown')})"
            )
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
    if destination.stat().st_size < 2:
        raise RuntimeError("Display software package download was empty")
    with destination.open("rb") as handle:
        if handle.read(2) != b"\x1f\x8b":
            raise RuntimeError(
                "Display update URL returned data that is not a gzip package"
            )

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

    report("running", 51, "Validating staged agent imports")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(release_root)
    result = subprocess.run(
        [str(APP_DIR / "venv" / "bin" / "python"), "-c", "import agent.config, agent.hub_connection, agent.dispatcher; from agent.jobs import update"],
        cwd=release_root, env=environment, capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "Agent import validation failed")[-1000:])

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
            _download(
                package_url,
                archive,
                report,
                expected_sha256=expected_sha256,
            )

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

            previous_version = (APP_DIR / "VERSION").read_text(encoding="utf-8").strip() if (APP_DIR / "VERSION").exists() else "unknown"
            update_state.begin(job, target, previous_version)
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
            update_state.awaiting_checkin()
            report(
                "running",
                95,
                f"Installed {target}; waiting for restarted agent check-in verification",
            )

            # A detached watchdog restores the backup if this agent never checks in.
            subprocess.Popen(
                [
                    str(APP_DIR / "venv" / "bin" / "python"),
                    str(APP_DIR / "recovery" / "recover.py"),
                    "--watch",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            # The restarted agent reports final success only after a heartbeat.
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
            update_state.failed(exc)
            if CURRENT_BACKUP.exists() and not dry_run:
                _restore_backup(report, str(exc))
            else:
                report("failed", 100, str(exc))
