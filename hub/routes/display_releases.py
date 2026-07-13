import io

from flask import Blueprint, jsonify, send_file

from services.display_releases import build_release_package


display_releases_bp = Blueprint(
    "display_releases",
    __name__,
    url_prefix="/api/v1/display-releases",
)


@display_releases_bp.route("/<target>/package.tar.gz")
def package(target):
    try:
        release = build_release_package(target)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    response = send_file(
        io.BytesIO(release["bytes"]),
        mimetype="application/gzip",
        as_attachment=True,
        download_name=f"church-display-{target}.tar.gz",
        max_age=0,
    )
    response.headers["X-Display-Release"] = release["target"]
    response.headers["X-Display-Commit"] = release["commit"]
    response.headers["X-Checksum-SHA256"] = release["sha256"]
    return response


@display_releases_bp.route("/<target>/metadata")
def metadata(target):
    try:
        release = build_release_package(target)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    return jsonify({
        "ok": True,
        "target": release["target"],
        "commit": release["commit"],
        "sha256": release["sha256"],
        "size": release["size"],
    })
