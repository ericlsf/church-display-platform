import json
import subprocess
from datetime import datetime
from pathlib import Path


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def read_json(path, default=None):
    path = Path(path)

    try:
        return json.loads(path.read_text())
    except Exception:
        return default if default is not None else {}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def run_command(command, cwd=None, timeout=None):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
    )

    return result.returncode, result.stdout, result.stderr


def cpu_temp():
    try:
        raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return f"{int(raw) / 1000:.1f}°C"
    except Exception:
        return "Unknown"


def disk_usage():
    try:
        output = subprocess.check_output(["df", "-h", "/"], text=True)
        return output.splitlines()[1].split()[4]
    except Exception:
        return "Unknown"


def memory_usage():
    try:
        data = {}

        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            data[key] = int(value.strip().split()[0])

        used = data["MemTotal"] - data["MemAvailable"]
        return f"{int((used / data['MemTotal']) * 100)}%"
    except Exception:
        return "Unknown"


def uptime():
    try:
        return subprocess.check_output(["uptime", "-p"], text=True).strip()
    except Exception:
        return "Unknown"


