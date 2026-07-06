import subprocess


def list_drive_folders(remote="gdrive", timeout=8):
    remote = remote or "gdrive"
    try:
        result = subprocess.run(["rclone", "lsd", f"{remote}:"], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return [], "rclone is not installed or not in PATH."
    except Exception as e:
        return [], str(e)
    if result.returncode != 0:
        return [], result.stderr.strip() or result.stdout.strip() or f"rclone exited with {result.returncode}"
    folders = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if parts:
            folders.append(parts[-1])
    return sorted(set(folders), key=lambda s: s.lower()), ""
