"""Apply Alert Center rules to generated alerts."""

from __future__ import annotations

from datetime import datetime, time, timezone

from services.alert_rules import load_alert_rules


def _parse_time(value):
    try:
        hour, minute = str(value).split(":", 1)
        return time(
            hour=int(hour),
            minute=int(minute),
        )
    except Exception:
        return time(0, 0)


def quiet_hours_active(rules, now=None):
    if not rules.get("quiet_hours_enabled"):
        return False

    now = now or datetime.now(timezone.utc)
    current = now.time().replace(
        tzinfo=None,
        second=0,
        microsecond=0,
    )

    start = _parse_time(
        rules.get("quiet_hours_start")
    )
    end = _parse_time(
        rules.get("quiet_hours_end")
    )

    if start == end:
        return True

    if start < end:
        return start <= current < end

    return current >= start or current < end


def apply_alert_policy(center, now=None):
    rules = load_alert_rules()
    quiet = quiet_hours_active(
        rules,
        now=now,
    )

    active = []
    suppressed = []

    for alert in center.get("alerts", []):
        category = alert.get(
            "category",
            "system",
        )

        enabled = rules.get(
            "categories",
            {},
        ).get(
            category,
            True,
        )

        reason = ""

        if not enabled:
            reason = "category disabled"
        elif (
            quiet
            and alert.get("severity") != "critical"
        ):
            reason = "quiet hours"

        enriched = {
            **alert,
            "suppressed": bool(reason),
            "suppression_reason": reason,
        }

        if reason:
            suppressed.append(enriched)
        else:
            active.append(enriched)

    counts = {
        "critical": sum(
            alert.get("severity") == "critical"
            for alert in active
        ),
        "warning": sum(
            alert.get("severity") == "warning"
            for alert in active
        ),
        "info": sum(
            alert.get("severity") == "info"
            for alert in active
        ),
        "active": len(active),
        "suppressed": len(suppressed),
    }

    return {
        **center,
        "alerts": active,
        "suppressed_alerts": suppressed,
        "rules": rules,
        "quiet_hours_active": quiet,
        "counts": counts,
    }
