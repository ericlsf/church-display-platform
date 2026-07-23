from flask import Blueprint, jsonify

from services.deployment_verification import (
    deployment_verification_state,
)


deployment_verification_bp = Blueprint(
    "deployment_verification",
    __name__,
    url_prefix="/display",
)


@deployment_verification_bp.route(
    "/<display_id>/deployment-verification"
)
def verification(display_id):
    return jsonify({
        "ok": True,
        **deployment_verification_state(display_id),
    })
