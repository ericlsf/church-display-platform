"""Classify managed machines without requiring a display-agent update."""
import socket


VALID_DEVICE_ROLES = {"display", "controller"}


def _identity(value):
    return str(value or "").strip().lower().split(".", 1)[0].replace("_", "-")


def device_role_for(display, local_hostname=None):
    explicit = str(
        display.get("device_role") or display.get("role") or ""
    ).strip().lower()
    if explicit in VALID_DEVICE_ROLES:
        return explicit

    local = _identity(local_hostname or socket.gethostname())
    identities = {
        _identity(display.get("id")),
        _identity(display.get("hostname")),
        _identity(display.get("name")),
    }
    return "controller" if local and local in identities else "display"


def is_controller(display):
    return device_role_for(display) == "controller"
