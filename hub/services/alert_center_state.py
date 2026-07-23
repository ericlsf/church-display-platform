"""Combine live alert state with acknowledgement metadata."""

from __future__ import annotations

from services.alert_acknowledgements import (
    clear_stale_acknowledgements,
    list_acknowledgements,
)
from services.alert_center import build_alert_center


def build_alert_center_state():
    center = build_alert_center()
    alerts = center.get("alerts", [])
    active_keys = {
        alert.get("key")
        for alert in alerts
        if alert.get("key")
    }

    clear_stale_acknowledgements(active_keys)
    acknowledgements = list_acknowledgements()

    active = []
    acknowledged = []

    for alert in alerts:
        record = acknowledgements.get(
            alert.get("key")
        )

        enriched = {
            **alert,
            "acknowledged": bool(record),
            "acknowledgement": record or {},
        }

        if record:
            acknowledged.append(enriched)
        else:
            active.append(enriched)

    severity_order = {
        "critical": 0,
        "warning": 1,
        "info": 2,
    }

    active.sort(
        key=lambda item: (
            severity_order.get(
                item.get("severity"),
                9,
            ),
            item.get("title", "").lower(),
        )
    )

    acknowledged.sort(
        key=lambda item: (
            item.get("acknowledgement", {}).get(
                "acknowledged_at",
                "",
            )
        ),
        reverse=True,
    )

    counts = {
        "active": len(active),
        "acknowledged": len(acknowledged),
        "critical": sum(
            item.get("severity") == "critical"
            for item in active
        ),
        "warning": sum(
            item.get("severity") == "warning"
            for item in active
        ),
        "info": sum(
            item.get("severity") == "info"
            for item in active
        ),
    }

    return {
        **center,
        "active_alerts": active,
        "acknowledged_alerts": acknowledged,
        "counts": counts,
    }
