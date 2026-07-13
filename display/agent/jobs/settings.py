from agent.config import CONFIG_PATH
from agent.utils import read_json, write_json


def _clean_settings(raw):
    raw = raw if isinstance(raw, dict) else {}

    overlay = raw.get("overlay", {})
    clock = raw.get("clock", {})
    countdown = raw.get("countdown", {})
    timings = raw.get("timings", {})

    return {
        "overlay": {
            "enabled": bool(overlay.get("enabled", True)),
            "text": str(overlay.get("text", "")).strip()[:160],
        },
        "clock": {
            "enabled": bool(clock.get("enabled", True)),
        },
        "countdown": {
            "enabled": bool(countdown.get("enabled", True)),
            "start_minutes": max(
                0,
                min(180, int(countdown.get("start_minutes", 20))),
            ),
        },
        "timings": {
            "image_duration": max(
                1,
                min(300, int(timings.get("image_duration", 8))),
            ),
        },
    }


def handle_apply_display_settings(job, report):
    payload = job.get("payload", {})
    settings = _clean_settings(payload.get("settings"))

    report("running", 35, "Validating presentation settings")

    config = read_json(CONFIG_PATH, {})
    config.setdefault("overlay", {})
    config.setdefault("clock", {})
    config.setdefault("countdown", {})
    config.setdefault("timings", {})

    config["overlay"].update(settings["overlay"])
    config["clock"].update(settings["clock"])
    config["countdown"].update(settings["countdown"])
    config["timings"].update(settings["timings"])

    write_json(CONFIG_PATH, config)

    report(
        "success",
        100,
        "Presentation settings applied; player will reload them automatically",
    )
