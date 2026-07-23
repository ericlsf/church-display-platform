import io

from flask import Blueprint, jsonify, send_file

from services.display_artifacts import create_artifact, get_artifact
from services.display_releases import build_release_package


display_releases_bp = Blueprint(
    "display_releases",
    __name__,
    url_prefix="/api/v1/display-releases",
)


@display_releases_bp.route("/artifacts/<sha256>.tar.gz")
def artifact(sha256):
    metadata = get_artifact(sha256)
    if not metadata:
        return jsonify({"ok": False, "error": "Artifact not found"}), 404

    response = send_file(
        metadata["path"],
        mimetype="application/gzip",
        as_attachment=True,
        download_name=metadata["path"].name,
        conditional=False,
        max_age=0,
    )
    response.headers["Content-Encoding"] = "identity"
    response.headers["Cache-Control"] = "no-store, no-transform"
    response.headers["X-Checksum-SHA256"] = metadata["sha256"]
    if metadata.get("target"):
        response.headers["X-Display-Release"] = metadata["target"]
    if metadata.get("commit"):
        response.headers["X-Display-Commit"] = metadata["commit"]
    return response


@display_releases_bp.route("/<target>/package.tar.gz")
def package(target):
    """
    Compatibility endpoint.

    Creates or reuses a persisted immutable artifact, then serves those exact
    bytes. New deployment jobs use the checksum-addressed artifact endpoint.
    """
    try:
        metadata = create_artifact(target)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    return artifact(metadata["sha256"])


@display_releases_bp.route("/<target>/metadata")
def metadata(target):
    try:
        artifact_metadata = create_artifact(target)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    return jsonify({
        "ok": True,
        "target": artifact_metadata.get("target"),
        "commit": artifact_metadata.get("commit"),
        "sha256": artifact_metadata["sha256"],
        "size": artifact_metadata["size"],
        "artifact_url": (
            f"/api/v1/display-releases/artifacts/"
            f"{artifact_metadata['sha256']}.tar.gz"
        ),
    })
