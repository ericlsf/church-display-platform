from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor


def hide_cursor(app):
    """Hide the mouse pointer for kiosk playback."""
    app.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
