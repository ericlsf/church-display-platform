from pathlib import Path

from flask import Blueprint, Response, request, send_file

from services.display_package import build_display_package, current_version


display_installer_bp = Blueprint(
    "display_installer",
    __name__,
    url_prefix="/install/display",
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
BOOTSTRAP_FILE = STATIC_DIR / "install-display-bootstrap.sh"


@display_installer_bp.route("")
def download_installer():
    hub_url = request.host_url.rstrip("/")
    script = BOOTSTRAP_FILE.read_text(encoding="utf-8")
    script = script.replace("__HUB_URL__", hub_url)

    return Response(
        script,
        mimetype="text/x-shellscript",
        headers={
            "Content-Disposition": "inline; filename=install-display.sh",
            "Cache-Control": "no-store",
        },
    )


@display_installer_bp.route("/package.tar.gz")
def download_package():
    return send_file(
        build_display_package(),
        mimetype="application/gzip",
        as_attachment=True,
        download_name=f"church-display-{current_version()}.tar.gz",
        max_age=0,
    )


@display_installer_bp.route("/command")
def command():
    hub_url = request.host_url.rstrip("/")
    return Response(
        f"bash <(curl -fsSL {hub_url}/install/display)\n",
        mimetype="text/plain",
    )


@display_installer_bp.route("/health")
def health():
    package = build_display_package()
    size = len(package.getbuffer())
    return {
        "ok": True,
        "version": current_version(),
        "package_bytes": size,
        "command": (
            f"bash <(curl -fsSL "
            f"{request.host_url.rstrip('/')}/install/display)"
        ),
    }
