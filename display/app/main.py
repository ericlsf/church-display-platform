import sys
import os
import json
import threading
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
from datetime import datetime

from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QPixmap, QColor

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from app.logging_setup import setup_logging
from app.media import scan_media
from app.admin_server import start_admin_server
from app.cursor import hide_cursor


IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".mkv"}

CONFIG_PATH = str(APP_ROOT / "config" / "config.json")
MEDIA_RESCAN_SECONDS = 10

STATUS_DIR = str(APP_ROOT / "status")
PLAYER_STATUS_PATH = str(APP_ROOT / "status" / "player.json")
MEDIA_STATUS_PATH = str(APP_ROOT / "status" / "media.json")


class OutlineLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._align = Qt.AlignCenter
        self._color = QColor(255, 255, 255)

    def setText(self, text):
        self._text = text
        super().setText(text)
        self.update()

    def setTextColor(self, color: QColor):
        self._color = color
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        painter.setPen(QColor(0, 0, 0))

        offsets = [
            (-2, -2), (0, -2), (2, -2),
            (-2,  0),          (2,  0),
            (-2,  2), (0,  2), (2,  2)
        ]

        for dx, dy in offsets:
            painter.drawText(rect.translated(dx, dy), int(self._align), self._text)

        painter.setPen(self._color)
        painter.drawText(rect, self._align, self._text)


class Player(QWidget):
    def __init__(self):
        super().__init__()

        print("APP STARTED")

        os.makedirs(STATUS_DIR, exist_ok=True)

        self.files = scan_media() or []
        self.index = 0

        self.current_media = ""
        self.current_media_type = "none"
        self.last_media_rescan = datetime.now().isoformat(timespec="seconds")
        self.last_config_load = ""

        self.config = {}
        self.load_config()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: black;")

        # ---------------- BASE ----------------
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: black;")

        self.video = QVideoWidget(self)
        self.video.hide()

        self.audio = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.mediaStatusChanged.connect(self.on_video_status)

        # ---------------- CRITICAL FIX: video must never cover overlays ----------------
        self.video.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # ---------------- OVERLAY ----------------
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay.setStyleSheet("background: transparent;")

        self.top_center = self.make_label(48, Qt.AlignTop | Qt.AlignHCenter)
        self.top_right = self.make_label(34, Qt.AlignTop | Qt.AlignRight)
        self.bottom_left = self.make_label(40, Qt.AlignBottom | Qt.AlignLeft)
        self.bottom_right = self.make_label(30, Qt.AlignBottom | Qt.AlignRight)

        # ---------------- TAKEOVER ----------------
        self.takeover = QLabel(self)
        self.takeover.setAlignment(Qt.AlignCenter)
        self.takeover.setVisible(False)
        self.takeover.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 245);
                color: yellow;
                font-size: 140px;
                font-weight: 900;
            }
        """)

        # ---------------- VIDEO FIX TIMER ----------------
        self.video_fix_timer = QTimer()
        self.video_fix_timer.setInterval(100)
        self.video_fix_timer.timeout.connect(self.force_stack_order)

        # ---------------- MEDIA TIMER ----------------
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.next)

        self.overlay_timer = QTimer()
        self.overlay_timer.timeout.connect(self.update_overlays)
        self.overlay_timer.start(1000)

        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self.load_config)
        self.config_timer.start(2000)

        # ---------------- STATUS TIMER ----------------
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.write_player_status)
        self.status_timer.start(1000)

        # ---------------- MEDIA RESCAN TIMER ----------------
        self.media_timer = QTimer()
        self.media_timer.timeout.connect(self.rescan_media)
        self.media_timer.start(MEDIA_RESCAN_SECONDS * 1000)

        # ---------------- WEB ADMIN SERVER ----------------
        threading.Thread(
            target=start_admin_server,
            args=(CONFIG_PATH,),
            daemon=True
        ).start()

        QTimer.singleShot(0, self.start)

    # ---------------- FINAL STACK CONTROL ----------------
    def force_stack_order(self):
        self.label.lower()
        self.video.lower()
        self.overlay.raise_()
        self.takeover.raise_()

    # ---------------- LABEL FACTORY ----------------
    def make_label(self, size, align):
        lbl = OutlineLabel(self.overlay)
        lbl._align = align
        lbl.setAlignment(Qt.AlignCenter)

        lbl.setStyleSheet(f"""
            QLabel {{
                font-size: {size}px;
                font-weight: 900;
                color: white;
                background: transparent;
                padding: 10px;
            }}
        """)

        lbl.show()
        return lbl

    # ---------------- CONFIG ----------------
    def load_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    self.config = json.load(f)
                self.last_config_load = datetime.now().isoformat(timespec="seconds")
        except Exception as e:
            print("CONFIG ERROR:", e)

    # ---------------- MEDIA RESCAN ----------------
    def rescan_media(self):
        new_files = scan_media() or []

        if new_files == self.files:
            self.last_media_rescan = datetime.now().isoformat(timespec="seconds")
            self.write_media_status()
            return

        was_empty = not self.files
        current_file = self.files[self.index] if self.files and self.index < len(self.files) else None

        self.files = new_files
        self.last_media_rescan = datetime.now().isoformat(timespec="seconds")

        if not self.files:
            self.index = 0
            self.current_media = ""
            self.current_media_type = "none"
            self.label.clear()
            self.video.hide()
            print("MEDIA RESCANNED: no files found")
            self.write_all_status()
            return

        if current_file in self.files:
            self.index = self.files.index(current_file)
        else:
            self.index = 0

        print("MEDIA RESCANNED")

        if was_empty or current_file not in self.files:
            self.show_current()
        else:
            self.write_all_status()

    # ---------------- START ----------------
    def start(self):
        self.showFullScreen()
        self.overlay.raise_()
        QTimer.singleShot(200, self.show_current)

    # ---------------- RESIZE ----------------
    def resizeEvent(self, event):
        r = self.rect()

        self.label.setGeometry(r)
        self.video.setGeometry(r)
        self.overlay.setGeometry(r)
        self.takeover.setGeometry(r)

        w, h = r.width(), r.height()

        self.top_center.setGeometry(0, 0, w, 150)
        self.top_right.setGeometry(w - 500, 0, 500, 150)
        self.bottom_left.setGeometry(20, h - 150, 800, 150)
        self.bottom_right.setGeometry(w - 500, h - 150, 500, 150)

        super().resizeEvent(event)

    # ---------------- OVERLAYS ----------------
    def update_overlays(self):
        cfg = self.config
        text, color, seconds = self.get_countdown_text()

        # ---------------- TAKEOVER ----------------
        takeover_seconds = max(
            0,
            int(cfg.get("countdown", {}).get("takeover_seconds", 30)),
        )
        if seconds is not None and seconds <= takeover_seconds:
            mins = seconds // 60
            secs = seconds % 60

            takeover_text = cfg.get("countdown", {}).get(
                "takeover_text",
                "Find your seat",
            )
            self.takeover.setText(f"{takeover_text}\n{mins:02}:{secs:02}")
            self.takeover.setVisible(True)

            self.top_center.setText("")
            self.top_right.setText("")
            self.bottom_left.setText("")
            self.bottom_right.setText("")

            self.force_stack_order()
            self.write_all_status()
            return

        self.takeover.setVisible(False)

        # ---------------- NORMAL MODE ----------------
        self.top_center.setText(self.get_active_overlay_text())

        if cfg.get("clock", {}).get("enabled"):
            self.top_right.setText(datetime.now().strftime("%I:%M %p"))
        else:
            self.top_right.setText("")

        self.bottom_left.setText(text)

        if color == "yellow":
            self.bottom_left.setTextColor(QColor(255, 255, 0))
        else:
            self.bottom_left.setTextColor(QColor(255, 255, 255))

        self.bottom_right.setText("")

        self.force_stack_order()
        self.write_player_status()

    # ---------------- SCHEDULED OVERLAYS ----------------
    def get_active_overlay_text(self):
        cfg = self.config
        fallback = cfg.get("overlay", {}).get("text", "")
        now = datetime.now()
        active = []

        for item in cfg.get("scheduled_overlays", []):
            try:
                if not item.get("enabled", True):
                    continue
                if not item.get("message", "").strip():
                    continue
                if self.scheduled_overlay_is_active(item, now):
                    active.append(item)
            except Exception:
                pass

        if not active:
            return fallback

        active.sort(key=lambda x: int(x.get("priority", 100)), reverse=True)
        return active[0].get("message", fallback)

    def scheduled_overlay_is_active(self, item, now):
        start_date = item.get("start_date", "").strip()
        end_date = item.get("end_date", "").strip()

        if start_date:
            try:
                if now.date() < datetime.strptime(start_date, "%Y-%m-%d").date():
                    return False
            except Exception:
                pass

        if end_date:
            try:
                if now.date() > datetime.strptime(end_date, "%Y-%m-%d").date():
                    return False
            except Exception:
                pass

        days = item.get("days", [])
        if days and now.strftime("%A") not in days:
            return False

        start_time = item.get("start_time", "").strip()
        end_time = item.get("end_time", "").strip()

        if start_time and end_time:
            try:
                st = datetime.strptime(start_time, "%H:%M").time()
                et = datetime.strptime(end_time, "%H:%M").time()
                current = now.time()
                if st <= et:
                    return st <= current <= et
                return current >= st or current <= et
            except Exception:
                return True

        return True

    def format_countdown_duration(self, seconds):
        seconds = int(max(0, seconds))
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if days >= 1:
            return f"{days}d {hours}h" if hours else f"{days}d"
        if hours >= 1:
            return f"{hours}h {minutes}m" if minutes else f"{hours}h"
        if minutes >= 10:
            return f"{minutes}m"
        return f"{minutes:02}:{secs:02}"

    # ---------------- COUNTDOWN ----------------
    def get_countdown_text(self):
        cfg = self.config
        now = datetime.now()

        # Sunday service countdowns ALWAYS take priority.
        c = cfg.get("countdown", {})

        if c.get("enabled"):
            best = None
            best_delta = None

            for svc in c.get("services", []):
                try:
                    if svc.get("day", "Sunday") != now.strftime("%A"):
                        continue
                    t = datetime.strptime(svc["time"], "%H:%M").time()
                    dt = datetime.combine(now.date(), t)
                    delta = (dt - now).total_seconds()

                    if delta < 0:
                        continue

                    start_window = c.get("start_minutes", 20) * 60
                    if delta > start_window:
                        continue

                    if best_delta is None or delta < best_delta:
                        best_delta = delta
                        label = c.get("text", "Service starts in").rstrip(":")
                        color = "yellow" if delta <= 300 else "white"
                        best = (f"{label}: {self.format_countdown_duration(delta)}", color, int(delta))
                except Exception:
                    pass

            if best:
                return best

        # Dynamic timers only show if no Sunday service countdown is active.
        best_dynamic = None
        best_dynamic_delta = None

        for item in cfg.get("dynamic_countdowns", []):
            try:
                target = datetime.fromisoformat(item["target"])
                delta = (target - now).total_seconds()

                if delta < 0:
                    continue

                show_before_minutes = item.get("show_before_minutes", 20)
                if delta > show_before_minutes * 60:
                    continue

                if best_dynamic_delta is None or delta < best_dynamic_delta:
                    best_dynamic_delta = delta
                    color = "yellow" if delta <= 300 else "white"
                    best_dynamic = (
                        f"{item.get('label','Event')}: {self.format_countdown_duration(delta)}",
                        color,
                        int(delta)
                    )
            except Exception:
                pass

        return best_dynamic if best_dynamic else ("", "white", None)

    # ---------------- STATUS ----------------
    def write_all_status(self):
        self.write_player_status()
        self.write_media_status()

    def write_json_atomic(self, path, payload):
        try:
            tmp = path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            print("STATUS WRITE ERROR:", e)

    def write_media_status(self):
        images = [f for f in self.files if Path(f).suffix.lower() in IMAGE_EXT]
        videos = [f for f in self.files if Path(f).suffix.lower() in VIDEO_EXT]

        status = {
            "total": len(self.files),
            "images": len(images),
            "videos": len(videos),
            "last_rescan": self.last_media_rescan,
            "current_media": os.path.basename(str(self.current_media)) if self.current_media else "",
            "current_index": self.index,
            "next_rescan_seconds": MEDIA_RESCAN_SECONDS,
            "last_update": datetime.now().isoformat(timespec="seconds")
        }

        self.write_json_atomic(MEDIA_STATUS_PATH, status)

    def write_player_status(self):
        text, color, seconds = self.get_countdown_text()

        status = {
            "state": "running",
            "current_media": os.path.basename(str(self.current_media)) if self.current_media else "",
            "current_media_path": str(self.current_media) if self.current_media else "",
            "media_type": self.current_media_type,
            "overlay": self.get_active_overlay_text(),
            "clock_enabled": self.config.get("clock", {}).get("enabled", False),
            "countdown": text,
            "countdown_color": color,
            "countdown_seconds": seconds,
            "media_count": len(self.files),
            "current_index": self.index,
            "last_config_load": self.last_config_load,
            "last_media_rescan": self.last_media_rescan,
            "last_update": datetime.now().isoformat(timespec="seconds")
        }

        self.write_json_atomic(PLAYER_STATUS_PATH, status)

    # ---------------- MEDIA ----------------
    def next(self):
        if not self.files:
            return

        self.index = (self.index + 1) % len(self.files)
        self.show_current()

    def show_current(self):
        if not self.files:
            print("NO MEDIA FILES FOUND")
            self.current_media = ""
            self.current_media_type = "none"
            self.write_all_status()
            return

        file = self.files[self.index]
        ext = Path(file).suffix.lower()

        print("SHOW:", file)

        self.current_media = file
        self.current_media_type = "image" if ext in IMAGE_EXT else "video"

        self.timer.stop()
        self.player.stop()
        self.video.hide()
        self.video_fix_timer.stop()

        if ext in IMAGE_EXT:
            self.show_image(file)
        else:
            self.show_video(file)

        self.write_all_status()

    def show_image(self, file):
        pix = QPixmap(str(file)).scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.label.setPixmap(pix)
        self.label.show()

        self.force_stack_order()

        self.timer.start(self.config.get("timings", {}).get("image_duration", 8) * 1000)

    def show_video(self, file):
        self.video.show()
        self.player.setSource(QUrl.fromLocalFile(str(file)))
        self.player.play()

        self.video_fix_timer.start()

        self.force_stack_order()

    def on_video_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.video_fix_timer.stop()
            self.next()


def main():
    setup_logging()
    app = QApplication(sys.argv)
    hide_cursor(app)

    player = Player()
    app._player = player

    sys.exit(app.exec())


if __name__ == "__main__":
    main()



