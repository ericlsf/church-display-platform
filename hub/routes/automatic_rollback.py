from flask import Blueprint, jsonify, request

from services.automatic_rollback import (
    DEFAULT_TIMEOUT_SECONDS,
    automatic_rollback_state,
)


automatic_rollback_bp = Blueprint(
    "automatic_rollback",
    __name__,
    url_prefix="/display",
)


@automatic_rollback_bp.route(
    "/<display_id>/automatic-rollback"
)
def state(display_id):
    try:
        timeout = int(
            request.args.get(
                "timeout",
                DEFAULT_TIMEOUT_SECONDS,
            )
        )
    except ValueError:
        timeout = DEFAULT_TIMEOUT_SECONDS

    timeout = min(
        max(timeout, 60),
        1800,
    )

    return jsonify({
        "ok": True,
        **automatic_rollback_state(
            display_id,
            timeout_seconds=timeout,
        ),
    })
