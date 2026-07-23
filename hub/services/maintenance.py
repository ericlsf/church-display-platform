from datetime import datetime, timezone

from services.config import load_config, save_config


def set_maintenance(display_id, enabled, reason=""):
    cfg = load_config()
    display = next(
        (item for item in cfg.get("displays", []) if item.get("id") == display_id),
        None,
    )
    if not display:
        raise ValueError("Display not found")

    display["maintenance"] = {
        "enabled": bool(enabled),
        "reason": str(reason or "").strip()[:250],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_config(cfg)
    return display["maintenance"]


def in_maintenance(display):
    maintenance = display.get("maintenance", {})
    return bool(maintenance.get("enabled", False))
