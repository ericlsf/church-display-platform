from services.config import load_config, normalize_display_id, normalize_host, save_config


def refresh_approved_display_address(display_id, heartbeat):
    """Refresh network metadata for an already-approved display.

    Display IDs are stable across address changes, so a heartbeat can safely
    correct stale connection details without enrolling an unknown device.
    """
    canonical_id = normalize_display_id(display_id)
    reported_host = normalize_host(heartbeat.get("host"))
    reported_ip = str(heartbeat.get("ip") or "").strip()
    reported_hostname = str(heartbeat.get("hostname") or "").strip()

    if not canonical_id or not reported_host:
        return set()

    config = load_config()
    for display in config.get("displays", []):
        if normalize_display_id(display.get("id")) != canonical_id:
            continue

        updates = {
            "host": reported_host,
            "ip": reported_ip,
            "hostname": reported_hostname,
        }
        changed = {
            field
            for field, value in updates.items()
            if value and display.get(field) != value
        }
        if not changed:
            return set()

        for field in changed:
            display[field] = updates[field]
        save_config(config)
        return changed

    return set()
