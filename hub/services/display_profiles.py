import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from services.config import load_config
from services.display_groups import group_members
from services.jobs import create_job


ROOT = Path(__file__).resolve().parents[2]
PROFILES_FILE = ROOT / "hub" / "config" / "display_profiles.json"
MAX_HISTORY = 20


DEFAULT_SETTINGS = {
    "overlay": {
        "enabled": True,
        "text": "Welcome",
    },
    "clock": {
        "enabled": True,
    },
    "countdown": {
        "enabled": True,
        "text": "Service starts in",
        "takeover_text": "Find your seat",
        "start_minutes": 20,
        "takeover_seconds": 30,
        "services": [
            {"day": "Sunday", "time": "08:00"},
            {"day": "Sunday", "time": "09:30"},
            {"day": "Sunday", "time": "11:15"},
        ],
    },
    "timings": {
        "image_duration": 8,
    },
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _normalize_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _bounded_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def normalize_settings(settings):
    settings = settings if isinstance(settings, dict) else {}

    overlay = settings.get("overlay", {})
    clock = settings.get("clock", {})
    countdown = settings.get("countdown", {})
    timings = settings.get("timings", {})

    return {
        "overlay": {
            "enabled": _normalize_bool(
                overlay.get("enabled"),
                DEFAULT_SETTINGS["overlay"]["enabled"],
            ),
            "text": str(
                overlay.get(
                    "text",
                    DEFAULT_SETTINGS["overlay"]["text"],
                )
            ).strip()[:160],
        },
        "clock": {
            "enabled": _normalize_bool(
                clock.get("enabled"),
                DEFAULT_SETTINGS["clock"]["enabled"],
            ),
        },
        "countdown": {
            "enabled": _normalize_bool(
                countdown.get("enabled"),
                DEFAULT_SETTINGS["countdown"]["enabled"],
            ),
            "start_minutes": _bounded_int(
                countdown.get("start_minutes"),
                DEFAULT_SETTINGS["countdown"]["start_minutes"],
                0,
                180,
            ),
            "text": str(
                countdown.get(
                    "text",
                    DEFAULT_SETTINGS["countdown"]["text"],
                )
            ).strip()[:80],
            "takeover_text": str(
                countdown.get(
                    "takeover_text",
                    DEFAULT_SETTINGS["countdown"]["takeover_text"],
                )
            ).strip()[:80],
            "takeover_seconds": _bounded_int(
                countdown.get("takeover_seconds"),
                DEFAULT_SETTINGS["countdown"]["takeover_seconds"],
                0,
                300,
            ),
            "services": [
                {
                    "day": str(item.get("day", "Sunday")).strip(),
                    "time": str(item.get("time", "")).strip(),
                }
                for item in countdown.get(
                    "services",
                    DEFAULT_SETTINGS["countdown"]["services"],
                )
                if isinstance(item, dict) and item.get("time")
            ],
        },
        "timings": {
            "image_duration": _bounded_int(
                timings.get("image_duration"),
                DEFAULT_SETTINGS["timings"]["image_duration"],
                1,
                300,
            ),
        },
    }


def load_profiles():
    if not PROFILES_FILE.exists():
        return {
            "profiles": [],
            "default_profile_id": "",
        }

    try:
        data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {
            "profiles": [],
            "default_profile_id": "",
        }

    data.setdefault("profiles", [])
    data.setdefault("default_profile_id", "")

    for profile in data["profiles"]:
        profile["settings"] = normalize_settings(
            profile.get("settings", {})
        )
        profile.setdefault("history", [])
        profile.setdefault("description", "")
        profile.setdefault("created_at", _now())
        profile.setdefault("updated_at", profile["created_at"])

    return data


def save_profiles(data):
    PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = PROFILES_FILE.with_suffix(".json.tmp")
    temp.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )
    temp.replace(PROFILES_FILE)


def _slugify(value):
    value = str(value or "").strip().lower()
    result = []
    for char in value:
        if char.isalnum():
            result.append(char)
        elif char in {" ", "-", "_", "."}:
            result.append("-")

    slug = "".join(result).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")

    return slug or f"profile-{uuid.uuid4().hex[:8]}"


def _unique_id(data, proposed, current_id=""):
    existing = {
        profile.get("id")
        for profile in data.get("profiles", [])
        if profile.get("id") != current_id
    }

    base = _slugify(proposed)
    result = base
    counter = 2

    while result in existing:
        result = f"{base}-{counter}"
        counter += 1

    return result


def get_profile(profile_id):
    data = load_profiles()
    for profile in data["profiles"]:
        if profile.get("id") == profile_id:
            return profile
    return None


def save_profile(
    profile_id,
    name,
    description,
    settings,
    actor="unknown",
):
    data = load_profiles()
    profile_id = str(profile_id or "").strip()
    name = str(name or "").strip()
    description = str(description or "").strip()[:500]

    if not name:
        raise ValueError("Profile name is required")

    profile = next(
        (
            item
            for item in data["profiles"]
            if item.get("id") == profile_id
        ),
        None,
    )

    normalized = normalize_settings(settings)
    now = _now()

    if profile:
        previous = {
            "saved_at": now,
            "saved_by": actor or "unknown",
            "name": profile.get("name", ""),
            "description": profile.get("description", ""),
            "settings": deepcopy(profile.get("settings", {})),
        }
        history = profile.setdefault("history", [])
        history.insert(0, previous)
        del history[MAX_HISTORY:]

        profile["name"] = name
        profile["description"] = description
        profile["settings"] = normalized
        profile["updated_at"] = now
        profile["updated_by"] = actor or "unknown"
    else:
        profile_id = _unique_id(data, profile_id or name)
        profile = {
            "id": profile_id,
            "name": name,
            "description": description,
            "settings": normalized,
            "history": [],
            "created_at": now,
            "created_by": actor or "unknown",
            "updated_at": now,
            "updated_by": actor or "unknown",
        }
        data["profiles"].append(profile)

    save_profiles(data)
    return profile


def clone_profile(profile_id, name, actor="unknown"):
    source = get_profile(profile_id)
    if not source:
        raise ValueError("Profile not found")

    return save_profile(
        "",
        name or f"{source.get('name', 'Profile')} Copy",
        source.get("description", ""),
        deepcopy(source.get("settings", {})),
        actor=actor,
    )


def delete_profile(profile_id):
    data = load_profiles()
    data["profiles"] = [
        profile
        for profile in data["profiles"]
        if profile.get("id") != profile_id
    ]

    if data.get("default_profile_id") == profile_id:
        data["default_profile_id"] = ""

    save_profiles(data)


def set_default_profile(profile_id):
    data = load_profiles()

    if profile_id and not any(
        profile.get("id") == profile_id
        for profile in data["profiles"]
    ):
        raise ValueError("Profile not found")

    data["default_profile_id"] = profile_id
    save_profiles(data)


def restore_revision(profile_id, revision_index, actor="unknown"):
    data = load_profiles()
    profile = next(
        (
            item
            for item in data["profiles"]
            if item.get("id") == profile_id
        ),
        None,
    )

    if not profile:
        raise ValueError("Profile not found")

    history = profile.get("history", [])

    try:
        revision = history[int(revision_index)]
    except (ValueError, IndexError):
        raise ValueError("Profile revision not found")

    return save_profile(
        profile_id,
        revision.get("name", profile.get("name", "")),
        revision.get(
            "description",
            profile.get("description", ""),
        ),
        revision.get("settings", {}),
        actor=actor,
    )


def export_profile(profile_id):
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("Profile not found")

    return {
        "schema": "church-display-profile/v1",
        "profile": {
            "id": profile.get("id"),
            "name": profile.get("name"),
            "description": profile.get("description", ""),
            "settings": normalize_settings(
                profile.get("settings", {})
            ),
        },
    }


def import_profile(payload, actor="unknown"):
    if not isinstance(payload, dict):
        raise ValueError("Invalid profile document")

    if payload.get("schema") != "church-display-profile/v1":
        raise ValueError("Unsupported profile schema")

    profile = payload.get("profile")
    if not isinstance(profile, dict):
        raise ValueError("Profile data is missing")

    return save_profile(
        "",
        profile.get("name", "Imported Profile"),
        profile.get("description", ""),
        profile.get("settings", {}),
        actor=actor,
    )


def _resolve_targets(display_ids=None, group_ids=None):
    combined = list(display_ids or [])
    combined.extend(group_members(group_ids or []))

    valid_ids = {
        display.get("id")
        for display in load_config().get("displays", [])
    }

    result = []
    seen = set()

    for display_id in combined:
        display_id = str(display_id or "").strip()
        if (
            not display_id
            or display_id in seen
            or display_id not in valid_ids
        ):
            continue
        seen.add(display_id)
        result.append(display_id)

    return result


def apply_profile(
    profile_id,
    display_ids=None,
    group_ids=None,
):
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("Profile not found")

    targets = _resolve_targets(display_ids, group_ids)
    if not targets:
        raise ValueError("Select at least one display or group")

    jobs = []
    for display_id in targets:
        jobs.append(
            create_job(
                display_id,
                "apply_display_settings",
                {
                    "settings": deepcopy(profile["settings"]),
                    "profile_id": profile["id"],
                    "profile_name": profile["name"],
                },
            )
        )

    return {
        "profile": profile,
        "display_ids": targets,
        "jobs": jobs,
    }
