from flask import Blueprint, render_template

from services.releases import list_git_tags, latest_git_tag


releases_bp = Blueprint("releases", __name__, url_prefix="/releases")


@releases_bp.route("")
def releases_page():
    tags = list_git_tags(limit=50)
    latest = latest_git_tag()

    return render_template(
        "releases.html",
        active="releases",
        release_tags=tags,
        latest_tag=latest,
    )
