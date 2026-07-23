from flask import (
    Blueprint,
    Response,
    g,
    request,
    session,
)

from services.audit import (
    append_audit,
    distinct_values,
    export_csv,
    read_audit,
)


audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


def _actor():
    user = getattr(g, "user", None)
    if isinstance(user, dict):
        return (
            user.get("username")
            or user.get("display_name")
            or "unknown"
        )
    if user:
        return (
            getattr(user, "username", None)
            or getattr(user, "display_name", None)
            or str(user)
        )

    return (
        session.get("username")
        or session.get("user")
        or session.get("display_name")
        or "unknown"
    )


def _category():
    endpoint = request.endpoint or ""
    if "." in endpoint:
        return endpoint.split(".", 1)[0]
    return endpoint or "unknown"


def _details():
    data = {}

    if request.form:
        for key in request.form:
            values = request.form.getlist(key)
            data[key] = values if len(values) > 1 else values[0]

    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        data.update(payload)

    return data


@audit_bp.before_app_request
def capture_mutating_request():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return

    # Avoid auditing the audit export page itself.
    if request.endpoint and request.endpoint.startswith("audit."):
        return

    g._audit_request = {
        "actor": _actor(),
        "category": _category(),
        "action": request.endpoint or request.path,
        "target": (
            request.view_args.get("display_id", "")
            if request.view_args
            else ""
        ),
        "details": _details(),
        "request_id": request.headers.get("X-Request-ID", ""),
        "remote_addr": request.remote_addr or "",
    }


@audit_bp.after_app_request
def record_mutating_request(response):
    captured = getattr(g, "_audit_request", None)
    if not captured:
        return response

    status = "success" if response.status_code < 400 else "failed"
    append_audit(status=status, **captured)
    return response


@audit_bp.route("")
def page():
    from flask import render_template

    rows = read_audit(
        limit=request.args.get("limit", 100),
        actor=request.args.get("actor", ""),
        category=request.args.get("category", ""),
        action=request.args.get("action", ""),
        status=request.args.get("status", ""),
        query=request.args.get("q", ""),
    )

    return render_template(
        "audit.html",
        active="audit",
        rows=rows,
        actors=distinct_values("actor"),
        categories=distinct_values("category"),
        current=request.args,
    )


@audit_bp.route("/export.csv")
def csv_export():
    rows = read_audit(
        limit=request.args.get("limit", 5000),
        actor=request.args.get("actor", ""),
        category=request.args.get("category", ""),
        action=request.args.get("action", ""),
        status=request.args.get("status", ""),
        query=request.args.get("q", ""),
    )

    return Response(
        export_csv(rows),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=audit-history.csv",
            "Cache-Control": "no-store",
        },
    )
