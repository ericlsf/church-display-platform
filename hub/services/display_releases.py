import hashlib
import io
import subprocess
import tarfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_EXCLUDES = {
    "venv",
    "__pycache__",
    "media",
    "status",
    "logs",
    "backups",
}
FILE_EXCLUDES = {
    "config.json",
    "config.json.bak",
    "church-display.log",
}


def validate_target(target):
    target = (target or "").strip()
    if not target:
        raise ValueError("A release target is required")

    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{target}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise ValueError(f"Release target not found: {target}")

    return target, result.stdout.strip()


def _git_files(target):
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", target, "--", "display"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def _include(path_string):
    path = PurePosixPath(path_string)
    relative = PurePosixPath(*path.parts[1:])

    if any(part in RUNTIME_EXCLUDES for part in relative.parts):
        return False
    if relative.name in FILE_EXCLUDES:
        return False
    if relative.suffix in {".pyc", ".pyo"}:
        return False

    allowed_roots = {"app", "agent", "scripts"}
    if relative.parts and relative.parts[0] in allowed_roots:
        return True

    return relative.as_posix() in {
        "requirements.txt",
        "install.sh",
    }


def _read_git_blob(target, path):
    result = subprocess.run(
        ["git", "show", f"{target}:{path}"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not read {path} from {target}: "
            f"{result.stderr.decode(errors='replace')[-300:]}"
        )
    return result.stdout


def build_release_package(target):
    target, commit = validate_target(target)
    buffer = io.BytesIO()

    files = [path for path in _git_files(target) if _include(path)]

    required = {
        "display/agent/agent.py",
        "display/app/main.py",
        "display/requirements.txt",
    }
    missing = sorted(required.difference(files))
    if missing:
        raise RuntimeError(
            "Release is missing required display files: "
            + ", ".join(missing)
        )

    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
        for path_string in sorted(files):
            data = _read_git_blob(target, path_string)
            relative = PurePosixPath(path_string).relative_to("display")
            archive_name = PurePosixPath("display-release") / relative

            info = tarfile.TarInfo(str(archive_name))
            info.size = len(data)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mode = 0o755 if relative.suffix == ".sh" else 0o644
            archive.addfile(info, io.BytesIO(data))

        metadata = (
            f"version={target}\n"
            f"commit={commit}\n"
        ).encode("utf-8")
        info = tarfile.TarInfo("display-release/RELEASE")
        info.size = len(metadata)
        info.mtime = 0
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(metadata))

        version = (target.lstrip("v") + "\n").encode("utf-8")
        info = tarfile.TarInfo("display-release/VERSION")
        info.size = len(version)
        info.mtime = 0
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(version))

    payload = buffer.getvalue()
    return {
        "target": target,
        "commit": commit,
        "bytes": payload,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }
