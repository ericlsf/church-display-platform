import requests
from services.config import normalize_host


def display_auth(display):
    username = display.get("username") or ""
    password = display.get("password") or ""
    if username and password:
        return (username, password)
    return None


def get_json(display, path, timeout=3):
    try:
        host = normalize_host(display.get("host", ""))
        r = requests.get(
            f"{host}{path}",
            timeout=timeout,
            auth=display_auth(display),
        )
        r.raise_for_status()
        return r.json(), True
    except Exception as e:
        return {"error": str(e)}, False


def post(display, path, data=None, timeout=8):
    try:
        host = normalize_host(display.get("host", ""))
        r = requests.post(
            f"{host}{path}",
            data=data or {},
            timeout=timeout,
            auth=display_auth(display),
            allow_redirects=False,
        )

        if r.status_code in [200, 204, 302, 303]:
            return {"status_code": r.status_code}, True

        return {
            "error": f"HTTP {r.status_code}: {r.text[:300]}"
        }, False

    except Exception as e:
        return {"error": str(e)}, False


#
# ----------------------------
# Versioned Display API (v1)
# ----------------------------
#

def get_status(display, timeout=3):
    """Read display status across both current and legacy player APIs."""
    status, online = get_json(display, "/api/v1/status", timeout=timeout)
    if online:
        return status, True
    legacy_status, legacy_online = get_json(display, "/api/status", timeout=timeout)
    if legacy_online:
        return legacy_status, True
    return status, False


def get_sync_status(display, timeout=3):
    return get_json(display, "/api/v1/sync", timeout=timeout)


def test_display(host, username="", password="", timeout=3):
    host = normalize_host(host)

    if not host:
        return False, "Missing host"

    display = {
        "host": host,
        "username": username,
        "password": password,
    }

    try:
        r = requests.get(
            f"{host}/api/v1/status",
            timeout=timeout,
            auth=display_auth(display),
        )
        r.raise_for_status()
        return True, r.json()

    except Exception as e:
        return False, str(e)


def set_sync_folder(display, remote, folder):
    return post(
        display,
        "/api/v1/sync/folder",
        {
            "sync_remote": remote or "gdrive",
            "sync_folder": folder or "Weekly",
        },
    )


def sync_now(display):
    return post(display, "/api/v1/sync/run")


def restart_display(display):
    return post(display, "/api/v1/system/restart")


def reboot_display(display):
    return post(display, "/api/v1/system/reboot")


