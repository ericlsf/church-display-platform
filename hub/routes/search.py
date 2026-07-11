from flask import Blueprint, jsonify, render_template, request

from services.search import global_search

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("")
def search_page():
    query = request.args.get("q", "").strip()
    return render_template(
        "search.html",
        active="search",
        query=query,
        results=global_search(query),
    )


@search_bp.route("/api")
def search_api():
    query = request.args.get("q", "").strip()
    return jsonify({"ok": True, "query": query, "results": global_search(query, limit=25)})
