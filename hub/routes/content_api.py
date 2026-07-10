from flask import Blueprint, jsonify, request, send_file

from services.content_cache import load_manifest, resolve_cached_file, sync_playlist_from_drive

content_api_bp = Blueprint("content_api", __name__, url_prefix="/api/v1/content")


@content_api_bp.route("/manifest")
def manifest():
    remote = request.args.get("remote", "gdrive").strip() or "gdrive"
    folder = request.args.get("folder", "").strip().strip("/")
    refresh = request.args.get("refresh") == "1"

    if refresh:
        data, error = sync_playlist_from_drive(remote, folder)
    else:
        data, error = load_manifest(remote, folder)
        if error:
            data, error = sync_playlist_from_drive(remote, folder)

    if error:
        return jsonify({"ok": False, "error": error}), 502
    return jsonify({"ok": True, "manifest": data})


@content_api_bp.route("/files/<playlist_id>/<path:relative_path>")
def content_file(playlist_id, relative_path):
    path = resolve_cached_file(playlist_id, relative_path)
    if not path:
        return jsonify({"ok": False, "error": "File not found"}), 404
    return send_file(path, conditional=True)
