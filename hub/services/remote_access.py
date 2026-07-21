from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

CONFIG_PATH = Path('/etc/church-display/remote-access.json')


def _run(*args: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=8, check=False)
        return {
            'ok': completed.returncode == 0,
            'stdout': completed.stdout.strip(),
            'stderr': completed.stderr.strip(),
            'returncode': completed.returncode,
        }
    except Exception as exc:
        return {'ok': False, 'stdout': '', 'stderr': str(exc), 'returncode': -1}


def _config() -> dict[str, Any]:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def remote_access_status() -> dict[str, Any]:
    binary = shutil.which('cloudflared')
    service = _run('systemctl', 'is-active', 'cloudflared.service') if binary else {'ok': False, 'stdout': 'not-installed', 'stderr': '', 'returncode': 3}
    enabled = _run('systemctl', 'is-enabled', 'cloudflared.service') if binary else {'ok': False, 'stdout': 'not-installed', 'stderr': '', 'returncode': 3}
    version = _run(binary, '--version') if binary else {'ok': False, 'stdout': '', 'stderr': 'cloudflared is not installed', 'returncode': 127}
    cfg = _config()
    hostname = str(cfg.get('hostname') or '').strip()
    return {
        'installed': bool(binary),
        'binary': binary,
        'service_active': service.get('stdout') == 'active',
        'service_enabled': enabled.get('stdout') == 'enabled',
        'service_state': service.get('stdout') or service.get('stderr') or 'unknown',
        'version': version.get('stdout') or 'Not installed',
        'hostname': hostname,
        'public_url': f'https://{hostname}' if hostname else '',
        'origin': str(cfg.get('origin') or 'http://localhost:8090'),
        'configured': bool(hostname) and service.get('stdout') == 'active',
    }
