import logging
import uuid

from flask import g, request


logger = logging.getLogger("church_display.requests")


def assign_request_id():
    incoming = (request.headers.get("X-Request-ID") or "").strip()
    g.request_id = incoming[:128] if incoming else str(uuid.uuid4())


def request_id():
    return getattr(g, "request_id", "unknown")


def log_exception(exc):
    logger.exception(
        "Unhandled request error id=%s method=%s path=%s remote=%s",
        request_id(),
        request.method,
        request.path,
        request.remote_addr,
        exc_info=exc,
    )
