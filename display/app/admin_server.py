import base64
import html
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse, unquote

from app.media import scan_media


IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
VIDEO_EXT = (".mp4", ".mov", ".mkv")

APP_ROOT = Path(__file__).resolve().parent.parent

SYNC_SCRIPT_PATH = str(APP_ROOT / "scripts" / "sync_media.sh")
# Legacy fallback only; sync folders are no longer restricted to this list.
SYNC_FOLDER_OPTIONS = ["Weekly", "Missions"]


class ConfigAdminHandler(BaseHTTPRequestHandler):
    config_path = None

    # ---------------- BASIC HELPERS ----------------
    def log_message(self, fmt, *args):
        print(f"[admin] {self.address_string()} - {fmt % args}")

    def auth_enabled(self):
        return bool(os.environ.get("CHURCH_DISPLAY_ADMIN_PASSWORD"))

    def check_auth(self):
        if not self.auth_enabled():
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
            user, password = decoded.split(":", 1)
        except Exception:
            return False
        return user == os.environ.get("CHURCH_DISPLAY_ADMIN_USER", "admin") and password == os.environ.get("CHURCH_DISPLAY_ADMIN_PASSWORD", "")

    def require_auth(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Church Display Admin"')
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Authentication required")

    def safe(self, value):
        return html.escape(str(value or ""))

    def checked(self, value):
        return "checked" if value else ""

    def selected(self, a, b):
        return "selected" if str(a) == str(b) else ""

    def base_dir(self):
        return os.path.dirname(os.path.dirname(self.config_path))

    def status_path(self, name):
        return os.path.join(self.base_dir(), "status", name)

    def read_json_file(self, path, default=None):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default if default is not None else {}

    def read_config(self):
        return self.read_json_file(self.config_path, {})

    def read_status(self, name):
        return self.read_json_file(self.status_path(name), {})

    def get_sync_config(self):
        cfg = self.read_config()
        sync = cfg.get("sync", {})

        remote = (sync.get("remote") or "gdrive").strip()
        folder = (sync.get("folder") or "Weekly").strip()

        return remote, folder

    def write_sync_config(self, remote, folder):
        remote = (remote or "gdrive").strip()
        folder = (folder or "Weekly").strip()

        cfg = self.read_config()
        cfg.setdefault("sync", {})
        cfg["sync"]["remote"] = remote
        cfg["sync"]["folder"] = folder
        self.write_config(cfg)

    def read_sync_status(self):
        return self.read_status("sync.json")


    def normalize_json_text(self, data):
        try:
            return json.dumps(data, sort_keys=True, separators=(",", ":"))
        except Exception:
            return ""

    def get_backup_dir(self):
        return os.path.join(os.path.dirname(self.config_path), "backups")

    def create_config_backup_if_changed(self, new_cfg):
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, "r") as f:
                old_cfg = json.load(f)
        except Exception:
            return
        if self.normalize_json_text(old_cfg) == self.normalize_json_text(new_cfg):
            return
        os.makedirs(self.get_backup_dir(), exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = os.path.join(self.get_backup_dir(), f"{stamp}.json")
        try:
            shutil.copy2(self.config_path, backup_path)
        except Exception as e:
            print("BACKUP ERROR:", e)

    def prune_config_backups(self, keep=10):
        backup_dir = self.get_backup_dir()
        if not os.path.exists(backup_dir):
            return
        backups = [os.path.join(backup_dir, n) for n in os.listdir(backup_dir) if n.endswith(".json")]
        backups.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        for path in backups[keep:]:
            try:
                os.remove(path)
            except Exception:
                pass

    def list_config_backups(self):
        backup_dir = self.get_backup_dir()
        if not os.path.exists(backup_dir):
            return []
        backups = []
        for name in os.listdir(backup_dir):
            if not name.endswith(".json"):
                continue
            path = os.path.join(backup_dir, name)
            try:
                backups.append({"name": name, "path": path, "mtime": datetime.fromtimestamp(os.path.getmtime(path)), "size": os.path.getsize(path)})
            except Exception:
                pass
        backups.sort(key=lambda x: x["mtime"], reverse=True)
        return backups[:10]

    def safe_backup_name(self, name):
        name = os.path.basename(unquote(name or ""))
        return name if name.endswith(".json") else ""

    def write_config(self, cfg):
        self.create_config_backup_if_changed(cfg)
        tmp = self.config_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, self.config_path)
        self.prune_config_backups()

    def minutes_to_amount_unit(self, minutes):
        try:
            minutes = int(minutes)
        except Exception:
            return 20, "minutes"
        if minutes % 10080 == 0:
            return minutes // 10080, "weeks"
        if minutes % 1440 == 0:
            return minutes // 1440, "days"
        if minutes % 60 == 0:
            return minutes // 60, "hours"
        return minutes, "minutes"

    def amount_unit_to_minutes(self, amount, unit):
        try:
            amount = max(1, int(amount))
        except Exception:
            amount = 20
        if unit == "weeks":
            return amount * 10080
        if unit == "days":
            return amount * 1440
        if unit == "hours":
            return amount * 60
        return amount

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Unknown"

    def get_uptime(self):
        try:
            seconds = int(float(open("/proc/uptime").read().split()[0]))
            d, r = divmod(seconds, 86400)
            h, r = divmod(r, 3600)
            m = r // 60
            if d:
                return f"{d}d {h}h"
            if h:
                return f"{h}h {m}m"
            return f"{m}m"
        except Exception:
            return "Unknown"

    def get_cpu_temp(self):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return f"{int(f.read().strip()) / 1000:.1f}°C"
        except Exception:
            return "Unknown"

    def get_disk_usage(self):
        try:
            out = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2).stdout.splitlines()
            return out[1].split()[4] if len(out) > 1 else "Unknown"
        except Exception:
            return "Unknown"

    def get_memory_usage(self):
        try:
            data = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    data[k] = int(v.strip().split()[0])
            return f"{int(((data['MemTotal'] - data['MemAvailable']) / data['MemTotal']) * 100)}%"
        except Exception:
            return "Unknown"

    def human_age(self, iso_value):
        try:
            updated = datetime.fromisoformat(iso_value)
            age = int((datetime.now() - updated).total_seconds())
            if age < 5:
                return "Just now"
            if age < 60:
                return f"{age}s ago"
            if age < 3600:
                return f"{age // 60}m ago"
            return updated.strftime("%Y-%m-%d %I:%M:%S %p")
        except Exception:
            return "Unknown"

    def is_status_fresh(self, status, max_age=30):
        try:
            updated = datetime.fromisoformat(status.get("last_update", ""))
            return (datetime.now() - updated).total_seconds() <= max_age
        except Exception:
            return False

    def get_media_summary(self):
        files = scan_media() or []
        images = [f for f in files if str(f).lower().endswith(IMAGE_EXT)]
        videos = [f for f in files if str(f).lower().endswith(VIDEO_EXT)]
        return files, images, videos

    # ---------------- ROUTING ----------------
    def do_GET(self):
        if not self.check_auth():
            return self.require_auth()
        path = urlparse(self.path).path
        if path == "/": return self.render_dashboard()
        if path == "/display": return self.render_display()
        if path == "/services": return self.render_services()
        if path == "/events": return self.render_events()
        if path == "/schedule": return self.render_schedule()
        if path == "/diagnostics": return self.render_diagnostics()
        if path == "/sync": return self.render_sync()
        if path == "/media": return self.render_media()
        if path == "/system": return self.render_system()
        if path == "/advanced": return self.render_advanced()
        if path == "/api/status": return self.handle_api_status()
        if path == "/api/sync-status": return self.handle_api_sync_status()

        # Versioned API v1 aliases.
        # These preserve the old endpoints while giving the Hub a stable API contract.
        if path == "/api/v1/status": return self.handle_api_status()
        if path == "/api/v1/sync": return self.handle_api_sync_status()

        if path == "/download-backup": return self.handle_download_backup()
        self.send_error(404)

    def do_POST(self):
        if not self.check_auth():
            return self.require_auth()
        path = urlparse(self.path).path
        data = self.read_post_data()
        if path == "/save-display": return self.handle_save_display(data)
        if path == "/save-services": return self.handle_save_services(data)
        if path == "/save-events": return self.handle_save_events(data)
        if path == "/save-schedule": return self.handle_save_schedule(data)
        if path == "/save-sync": return self.handle_save_sync(data)

        # Versioned API v1 aliases.
        # These preserve the old endpoints while giving the Hub a stable API contract.
        if path == "/api/v1/sync/folder": return self.handle_save_sync(data)
        if path == "/api/v1/sync/run": return self.handle_sync_now()
        if path == "/api/v1/system/restart": return self.handle_restart()
        if path == "/api/v1/system/reboot": return self.handle_reboot()

        if path == "/raw": return self.handle_raw(data)
        if path == "/restore-backup": return self.handle_restore_backup(data)
        if path == "/sync-now": return self.handle_sync_now()
        if path == "/restart": return self.handle_restart()
        if path == "/reboot": return self.handle_reboot()
        self.send_error(404)

    def read_post_data(self):
        length = int(self.headers.get("Content-Length", 0))
        return parse_qs(self.rfile.read(length).decode("utf-8"))

    # ---------------- LAYOUT ----------------
    def page(self, title, active, body):
        nav_items = [
            ("/", "Dashboard", "dashboard"),
            ("/display", "Display", "display"),
            ("/services", "Sunday Services", "services"),
            ("/events", "Events", "events"),
            ("/schedule", "Scheduled Messages", "schedule"),
            ("/diagnostics", "Diagnostics", "diagnostics"),
            ("/sync", "Media Sync", "sync"),
            ("/media", "Media", "media"),
            ("/system", "System", "system"),
            ("/advanced", "Advanced", "advanced"),
        ]
        nav = "".join([f'<a class="{"active" if active == key else ""}" href="{href}">{label}</a>' for href, label, key in nav_items])
        page = f"""<!doctype html><html><head><title>{self.safe(title)} - Church Display Admin</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{--bg:#101010;--panel:#1d1d1d;--panel2:#151515;--border:#333;--text:#f2f2f2;--muted:#aaa;--blue:#2d7dff;--red:#b3261e;--green:#1f8f4d;--yellow:#ffd700}}
*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;background:var(--bg);color:var(--text);margin:0}}header{{background:#050505;border-bottom:1px solid var(--border);padding:16px 20px;position:sticky;top:0;z-index:10}}header h1{{margin:0 0 12px 0;font-size:24px}}nav{{display:flex;gap:8px;overflow-x:auto;padding-bottom:2px}}nav a{{color:#ddd;text-decoration:none;padding:9px 12px;border-radius:8px;background:#181818;white-space:nowrap;border:1px solid #292929}}nav a.active{{background:var(--blue);color:white;border-color:var(--blue)}}main{{padding:20px;max-width:1200px;margin:0 auto}}.section{{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:18px;margin-bottom:18px}}.card{{background:var(--panel2);border:1px solid var(--border);padding:14px;border-radius:10px;margin-top:12px}}.muted{{color:var(--muted)}}label{{display:block;margin-top:12px;margin-bottom:5px;font-weight:bold}}input,textarea,select{{width:100%;padding:11px;font-size:16px;border-radius:7px;border:1px solid #555;background:#090909;color:white}}input[type=checkbox]{{width:auto;margin-right:8px}}textarea{{height:360px;font-family:monospace;white-space:pre}}button{{padding:12px 18px;font-size:16px;border-radius:7px;border:0;cursor:pointer;margin-top:14px;margin-right:8px}}.primary{{background:var(--blue);color:white}}.danger{{background:var(--red);color:white}}.safe{{background:var(--green);color:white}}.grid{{display:grid;gap:10px}}.two{{grid-template-columns:1fr 1fr}}.three{{grid-template-columns:repeat(3,1fr)}}.four{{grid-template-columns:repeat(4,1fr)}}.stat{{background:var(--panel2);border-radius:10px;padding:14px;text-align:center;border:1px solid var(--border)}}.stat strong{{display:block;font-size:30px}}.status-good{{color:#54d17a;font-weight:bold}}.status-warn{{color:#ffcf33;font-weight:bold}}.preview{{background:black;border:1px solid #444;border-radius:12px;height:260px;position:relative;overflow:hidden;text-align:center}}.preview .top{{position:absolute;top:24px;width:100%;font-size:28px;font-weight:900;text-shadow:2px 2px 0 black}}.preview .clock{{position:absolute;top:26px;right:26px;font-size:22px;font-weight:800;text-shadow:2px 2px 0 black}}.preview .bottom{{position:absolute;bottom:26px;left:28px;font-size:26px;font-weight:900;color:var(--yellow);text-shadow:2px 2px 0 black}}.pill{{display:inline-block;padding:6px 10px;border-radius:999px;background:#242424;border:1px solid #444;color:#ddd;font-size:14px;text-decoration:none}}@media(max-width:760px){{main{{padding:14px}}.two,.three,.four{{grid-template-columns:1fr}}header{{padding:14px}}}}
</style></head><body><header><h1>Church Display Admin</h1><nav>{nav}</nav></header><main>{body}</main></body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    # ---------------- API ----------------
    def handle_api_status(self):
        cfg = self.read_config()
        player = self.read_status("player.json")
        media = self.read_status("media.json")
        files, images, videos = self.get_media_summary()
        fresh = self.is_status_fresh(player, 10)
        payload = {
            "fresh": fresh,
            "state_label": "Running" if fresh else "No recent status",
            "state_dot": "●" if fresh else "○",
            "current_media": player.get("current_media") or "No media reported",
            "media_type": player.get("media_type") or "Unknown",
            "overlay": player.get("overlay") or cfg.get("overlay", {}).get("text", ""),
            "countdown": player.get("countdown") or "No active countdown",
            "last_update": self.human_age(player.get("last_update", "")),
            "clock": datetime.now().strftime("%I:%M %p") if player.get("clock_enabled", cfg.get("clock", {}).get("enabled")) else "",
            "current_index": player.get("current_index", ""),
            "player_media_count": player.get("media_count", len(files)),
            "images": media.get("images", len(images)),
            "videos": media.get("videos", len(videos)),
            "total_media": media.get("total", len(files)),
            "ip": self.get_local_ip(),
            "uptime": self.get_uptime(),
            "memory": self.get_memory_usage(),
            "disk": self.get_disk_usage(),
            "now": datetime.now().strftime("%I:%M:%S %p")
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


    def handle_api_sync_status(self):
        remote, folder = self.get_sync_config()
        status = self.read_sync_status()

        payload = {
            "remote": remote,
            "folder": folder,
            "source": f"{remote}:{folder}",
            "state": status.get("state", "unknown"),
            "last_success": self.human_age(status.get("last_success", "")),
            "last_update": self.human_age(status.get("last_update", "")),
            "duration_seconds": status.get("duration_seconds", ""),
            "files_synced": status.get("files_synced", ""),
            "error": status.get("error", ""),
            "fresh": self.is_status_fresh(status, 900),
        }

        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---------------- PAGES ----------------
    def render_dashboard(self):
        cfg = self.read_config(); player = self.read_status("player.json"); media = self.read_status("media.json")
        files, images, videos = self.get_media_summary(); fresh = self.is_status_fresh(player, 10)
        state_label = "Running" if fresh else "No recent status"; state_class = "status-good" if fresh else "status-warn"; state_dot = "●" if fresh else "○"
        overlay = self.safe(player.get("overlay") or cfg.get("overlay", {}).get("text", "")); countdown = self.safe(player.get("countdown") or "No active countdown")
        clock = datetime.now().strftime("%I:%M %p") if player.get("clock_enabled", cfg.get("clock", {}).get("enabled")) else ""
        body = f'''
        <div class="section"><h2>Live Dashboard</h2><div class="grid four"><div class="stat"><strong id="status-dot" class="{state_class}">{state_dot}</strong><span id="status-label">{state_label}</span></div><div class="stat"><strong id="image-count">{media.get('images', len(images))}</strong>Images</div><div class="stat"><strong id="video-count">{media.get('videos', len(videos))}</strong>Videos</div><div class="stat"><strong id="total-media">{media.get('total', len(files))}</strong>Total Media</div></div><p class="muted">Player status last updated: <span id="last-update">{self.safe(self.human_age(player.get('last_update','')))}</span></p><p class="muted">Dashboard refreshed: <span id="dashboard-refreshed">loading...</span></p></div>
        <div class="section"><h2>Display Preview</h2><div class="preview"><div id="preview-overlay" class="top">{overlay}</div><div id="preview-clock" class="clock">{self.safe(clock)}</div><div id="preview-countdown" class="bottom">{countdown}</div></div><p class="muted">This preview updates every 3 seconds from status/player.json.</p></div>
        <div class="section"><h2>Current Playback</h2><div class="grid two"><div class="card"><h3>Currently Playing</h3><p><strong id="current-media">{self.safe(player.get('current_media','No media reported'))}</strong></p><p>Type: <strong id="media-type">{self.safe(player.get('media_type','Unknown'))}</strong></p><p>Index: <strong id="current-index">{self.safe(player.get('current_index',''))}</strong> of <strong id="player-media-count">{self.safe(player.get('media_count',len(files)))}</strong></p></div><div class="card"><h3>Current Display State</h3><p>Overlay: <strong id="current-overlay">{overlay or 'None'}</strong></p><p>Countdown: <strong id="current-countdown">{countdown}</strong></p></div></div></div>
        <div class="section"><h2>System</h2><div class="grid four"><div class="stat"><strong id="system-ip">{self.safe(self.get_local_ip())}</strong>IP</div><div class="stat"><strong id="system-uptime">{self.safe(self.get_uptime())}</strong>Uptime</div><div class="stat"><strong id="system-memory">{self.safe(self.get_memory_usage())}</strong>Memory</div><div class="stat"><strong id="system-disk">{self.safe(self.get_disk_usage())}</strong>Disk</div></div></div>
        <script>
        function setText(id,v){{const e=document.getElementById(id);if(e) e.textContent=(v===null||v===undefined||v==='')?'—':String(v);}}
        async function refreshDashboard(){{try{{const r=await fetch('/api/status',{{cache:'no-store'}});if(!r.ok)return;const d=await r.json();const dot=document.getElementById('status-dot');if(dot){{dot.textContent=d.state_dot||'○';dot.className=d.fresh?'status-good':'status-warn';}}setText('status-label',d.state_label);setText('image-count',d.images);setText('video-count',d.videos);setText('total-media',d.total_media);setText('last-update',d.last_update);setText('dashboard-refreshed',d.now);setText('preview-overlay',d.overlay);setText('preview-clock',d.clock);setText('preview-countdown',d.countdown);setText('current-media',d.current_media);setText('media-type',d.media_type);setText('current-index',d.current_index);setText('player-media-count',d.player_media_count);setText('current-overlay',d.overlay||'None');setText('current-countdown',d.countdown);setText('system-ip',d.ip);setText('system-uptime',d.uptime);setText('system-memory',d.memory);setText('system-disk',d.disk);}}catch(e){{console.log(e);}}}}
        refreshDashboard();setInterval(refreshDashboard,3000);
        </script>'''
        return self.page("Dashboard", "dashboard", body)

    def render_display(self):
        cfg = self.read_config(); overlay_text = self.safe(cfg.get("overlay", {}).get("text", "")); clock_checked = self.checked(cfg.get("clock", {}).get("enabled")); image_duration = cfg.get("timings", {}).get("image_duration", 8)
        body = f'''<form method="POST" action="/save-display"><div class="section"><h2>Display Settings</h2><label>Welcome / Top Center Text</label><input name="overlay_text" value="{overlay_text}"><label><input type="checkbox" name="clock_enabled" {clock_checked}>Show Clock</label><label>Image Duration, in Seconds</label><input name="image_duration" type="number" min="1" value="{image_duration}"><button class="primary" type="submit">Save Display Settings</button></div></form>'''
        return self.page("Display", "display", body)

    def render_services(self):
        cfg = self.read_config(); c = cfg.get("countdown", {}); checked = self.checked(c.get("enabled")); start = c.get("start_minutes", 20); services = c.get("services") or [{"day":"Sunday","time":"08:00"},{"day":"Sunday","time":"09:30"},{"day":"Sunday","time":"11:15"}]
        rows = "".join([f'<div class="card"><div class="grid three"><div><label>Day</label><input name="service_day" value="{self.safe(s.get("day","Sunday"))}"></div><div><label>Time</label><input name="service_time" value="{self.safe(s.get("time",""))}" placeholder="09:30"></div><div><label>Status</label><p><span class="pill">{"Default" if i < 3 else "Additional"}</span></p></div></div></div>' for i,s in enumerate(services)])
        body = f'''<form method="POST" action="/save-services"><div class="section"><h2>Sunday Services</h2><p class="muted">Sunday timers always take priority. Default rows are editable but not deleted.</p><label><input type="checkbox" name="countdown_enabled" {checked}>Enable Sunday Countdown</label><label>Countdown Starts This Many Minutes Before Service</label><input name="countdown_start_minutes" type="number" min="1" value="{start}">{rows}<div class="card"><h3>Add Additional Service</h3><div class="grid two"><input name="service_day" value="Sunday"><input name="service_time" placeholder="18:00"></div></div><button class="primary" type="submit">Save Sunday Services</button></div></form>'''
        return self.page("Sunday Services", "services", body)

    def render_events(self):
        cfg = self.read_config(); cards = ""
        for item in cfg.get("dynamic_countdowns", []):
            dt_date = dt_time = ""
            try:
                dt = datetime.fromisoformat(item.get("target", "")); dt_date = dt.strftime("%Y-%m-%d"); dt_time = dt.strftime("%H:%M")
            except Exception: pass
            amount, unit = self.minutes_to_amount_unit(item.get("show_before_minutes", 20))
            cards += f'''<div class="card"><label>Event Label</label><input name="dynamic_label" value="{self.safe(item.get('label',''))}"><div class="grid two"><div><label>Date</label><input name="dynamic_date" type="date" value="{dt_date}"></div><div><label>Time</label><input name="dynamic_time" type="time" value="{dt_time}"></div></div><label>Show Countdown Before Event</label><div class="grid two"><input name="dynamic_show_amount" type="number" min="1" value="{amount}"><select name="dynamic_show_unit"><option value="minutes" {self.selected(unit,'minutes')}>Minutes</option><option value="hours" {self.selected(unit,'hours')}>Hours</option><option value="days" {self.selected(unit,'days')}>Days</option><option value="weeks" {self.selected(unit,'weeks')}>Weeks</option></select></div></div>'''
        body = f'''<form method="POST" action="/save-events"><div class="section"><h2>Events</h2><p class="muted">Dynamic event countdowns show only when no Sunday service countdown is active.</p>{cards}<div class="card"><h3>Add Event</h3><label>Event Label</label><input name="dynamic_label" placeholder="Youth Night"><div class="grid two"><div><label>Date</label><input name="dynamic_date" type="date"></div><div><label>Time</label><input name="dynamic_time" type="time"></div></div><label>Show Countdown Before Event</label><div class="grid two"><input name="dynamic_show_amount" type="number" min="1" value="20"><select name="dynamic_show_unit"><option value="minutes">Minutes</option><option value="hours">Hours</option><option value="days">Days</option><option value="weeks">Weeks</option></select></div></div><button class="primary" type="submit">Save Events</button></div></form>'''
        return self.page("Events", "events", body)

    def render_schedule(self):
        cfg = self.read_config(); cards = ""
        for item in cfg.get("scheduled_overlays", []):
            cards += f'''<div class="card"><label><input type="checkbox" name="sched_enabled" {self.checked(item.get('enabled', True))}>Enabled</label><label>Message</label><input name="sched_message" value="{self.safe(item.get('message',''))}"><label>Priority</label><input name="sched_priority" type="number" value="{self.safe(item.get('priority',100))}"><div class="grid two"><div><label>Start Date</label><input name="sched_start_date" type="date" value="{self.safe(item.get('start_date',''))}"></div><div><label>End Date</label><input name="sched_end_date" type="date" value="{self.safe(item.get('end_date',''))}"></div></div><div class="grid two"><div><label>Start Time</label><input name="sched_start_time" type="time" value="{self.safe(item.get('start_time',''))}"></div><div><label>End Time</label><input name="sched_end_time" type="time" value="{self.safe(item.get('end_time',''))}"></div></div></div>'''
        body = f'''<form method="POST" action="/save-schedule"><div class="section"><h2>Scheduled Messages</h2><p class="muted">Highest-priority active message wins. If none are active, normal welcome text is used.</p>{cards}<div class="card"><h3>Add Scheduled Message</h3><label><input type="checkbox" name="sched_enabled" checked>Enabled</label><label>Message</label><input name="sched_message" placeholder="Merry Christmas"><label>Priority</label><input name="sched_priority" type="number" value="100"><div class="grid two"><div><label>Start Date</label><input name="sched_start_date" type="date"></div><div><label>End Date</label><input name="sched_end_date" type="date"></div></div><div class="grid two"><div><label>Start Time</label><input name="sched_start_time" type="time"></div><div><label>End Time</label><input name="sched_end_time" type="time"></div></div></div><button class="primary" type="submit">Save Scheduled Messages</button></div></form>'''
        return self.page("Scheduled Messages", "schedule", body)

    def render_diagnostics(self):
        player = self.read_status("player.json"); media = self.read_status("media.json"); sync = self.read_status("sync.json"); files, images, videos = self.get_media_summary()
        body = f'''<div class="section"><h2>Diagnostics</h2><div class="grid four"><div class="stat"><strong class="{'status-good' if self.is_status_fresh(player,10) else 'status-warn'}">{'●' if self.is_status_fresh(player,10) else '○'}</strong>Player</div><div class="stat"><strong class="{'status-good' if self.is_status_fresh(media,60) else 'status-warn'}">{'●' if self.is_status_fresh(media,60) else '○'}</strong>Media</div><div class="stat"><strong class="{'status-good' if self.is_status_fresh(sync,300) else 'status-warn'}">{'●' if self.is_status_fresh(sync,300) else '○'}</strong>Google Drive</div><div class="stat"><strong>{self.safe(self.get_cpu_temp())}</strong>CPU Temp</div></div></div><div class="section"><h2>Player</h2><p>Last heartbeat: <strong>{self.safe(self.human_age(player.get('last_update','')))}</strong></p><p>Current media: <strong>{self.safe(player.get('current_media',''))}</strong></p><p>Overlay: <strong>{self.safe(player.get('overlay',''))}</strong></p><p>Countdown: <strong>{self.safe(player.get('countdown','No active countdown'))}</strong></p><p>Last config load: <strong>{self.safe(self.human_age(player.get('last_config_load','')))}</strong></p></div><div class="section"><h2>Media</h2><p>Files: <strong>{self.safe(media.get('total',len(files)))}</strong></p><p>Images: <strong>{self.safe(media.get('images',len(images)))}</strong></p><p>Videos: <strong>{self.safe(media.get('videos',len(videos)))}</strong></p><p>Last rescan: <strong>{self.safe(self.human_age(media.get('last_rescan','')))}</strong></p></div><div class="section"><h2>Google Drive Sync</h2><p>Status: <strong>{self.safe(sync.get('state','No sync status file'))}</strong></p><p>Last update: <strong>{self.safe(self.human_age(sync.get('last_update','')))}</strong></p><p class="muted">Drive sync status will show here when a sync process writes status/sync.json.</p></div><div class="section"><h2>System</h2><div class="grid four"><div class="stat"><strong>{self.safe(self.get_local_ip())}</strong>IP</div><div class="stat"><strong>{self.safe(self.get_uptime())}</strong>Uptime</div><div class="stat"><strong>{self.safe(self.get_memory_usage())}</strong>Memory</div><div class="stat"><strong>{self.safe(self.get_disk_usage())}</strong>Disk</div></div></div>'''
        return self.page("Diagnostics", "diagnostics", body)


    def render_sync(self):
        remote, folder = self.get_sync_config()
        status = self.read_sync_status()

        state = self.safe(status.get("state", "unknown"))
        last_success = self.safe(self.human_age(status.get("last_success", "")))
        last_update = self.safe(self.human_age(status.get("last_update", "")))
        duration = self.safe(status.get("duration_seconds", ""))
        files_synced = self.safe(status.get("files_synced", ""))
        error = self.safe(status.get("error", ""))

        # Folder names are intentionally unrestricted.
        # The Hub can send any folder returned by rclone/Google Drive.

        body = f"""
        <div class="section">
            <h2>Media Sync</h2>
            <p class="muted">
                This controls which Google Drive folder this display board syncs from.
                Each board has its own local setting.
            </p>

            <form method="POST" action="/save-sync">
                <label>Rclone Remote</label>
                <input name="sync_remote" value="{self.safe(remote)}">

                <label>Google Drive Folder</label>
                <input name="sync_folder" value="{self.safe(folder)}" placeholder="Weekly">

                <button class="primary" type="submit">Save Sync Settings</button>
            </form>
        </div>

        <div class="section">
            <h2>Current Sync Status</h2>
            <div class="grid three">
                <div class="stat"><strong id="sync-folder">{self.safe(folder)}</strong>Folder</div>
                <div class="stat"><strong id="sync-state">{state}</strong>Status</div>
                <div class="stat"><strong id="sync-last-success">{last_success}</strong>Last Success</div>
            </div>

            <p>Source: <strong id="sync-source">{self.safe(remote)}:{self.safe(folder)}</strong></p>
            <p>Last Update: <strong id="sync-last-update">{last_update}</strong></p>
            <p>Duration: <strong id="sync-duration">{duration}</strong> seconds</p>
            <p>Files Synced: <strong id="sync-files">{files_synced}</strong></p>
            <p>Error: <strong id="sync-error">{error or "None"}</strong></p>

            <form method="POST" action="/sync-now" onsubmit="return confirm('Run media sync now?');">
                <button class="safe" type="submit">Sync Now</button>
            </form>
        </div>

        <script>
        function setText(id, value) {{
            const el = document.getElementById(id);
            if (!el) return;
            el.textContent = value === null || value === undefined || value === "" ? "—" : String(value);
        }}

        async function refreshSyncStatus() {{
            try {{
                const response = await fetch("/api/sync-status", {{ cache: "no-store" }});
                if (!response.ok) return;
                const data = await response.json();

                setText("sync-folder", data.folder);
                setText("sync-state", data.state);
                setText("sync-source", data.source);
                setText("sync-last-success", data.last_success);
                setText("sync-last-update", data.last_update);
                setText("sync-duration", data.duration_seconds);
                setText("sync-files", data.files_synced);
                setText("sync-error", data.error || "None");
            }} catch (err) {{
                console.log("Sync status refresh failed", err);
            }}
        }}

        refreshSyncStatus();
        setInterval(refreshSyncStatus, 5000);
        </script>
        """

        return self.page("Media Sync", "sync", body)

    def render_media(self):
        files, images, videos = self.get_media_summary(); sample = "".join([f"<li>{self.safe(os.path.basename(str(f)))}</li>" for f in files[:25]])
        body = f'''<div class="section"><h2>Media Status</h2><p class="muted">Media files are managed through Google Drive.</p><div class="grid three"><div class="stat"><strong>{len(files)}</strong>Total Files</div><div class="stat"><strong>{len(images)}</strong>Images</div><div class="stat"><strong>{len(videos)}</strong>Videos</div></div><form method="GET" action="/media"><button class="safe" type="submit">Refresh Media Status</button></form></div><div class="section"><h2>Recent Media Files</h2><ul>{sample}</ul></div>'''
        return self.page("Media", "media", body)

    def render_system(self):
        auth_status = "Enabled" if self.auth_enabled() else "Disabled"
        body = f'''<div class="section"><h2>System Status</h2><div class="grid four"><div class="stat"><strong>{self.safe(self.get_local_ip())}</strong>IP</div><div class="stat"><strong>{self.safe(self.get_uptime())}</strong>Uptime</div><div class="stat"><strong>{self.safe(self.get_memory_usage())}</strong>Memory</div><div class="stat"><strong>{self.safe(self.get_disk_usage())}</strong>Disk</div></div><p>CPU Temp: <strong>{self.safe(self.get_cpu_temp())}</strong></p><p>Admin Authentication: <strong>{auth_status}</strong></p></div><div class="section"><h2>System Actions</h2><form method="POST" action="/restart" onsubmit="return confirm('Restart display service?');"><button class="danger" type="submit">Restart Display</button></form><form method="POST" action="/reboot" onsubmit="return confirm('Reboot Raspberry Pi?');"><button class="danger" type="submit">Reboot Pi</button></form><p class="muted">Restart/reboot require sudo permissions.</p></div>'''
        return self.page("System", "system", body)

    def render_advanced(self):
        cfg = self.read_config(); raw_json = self.safe(json.dumps(cfg, indent=2)); q = parse_qs(urlparse(self.path).query); dev = q.get("dev", ["0"])[0] == "1"
        backups = self.list_config_backups(); rows = ""
        for b in backups:
            name = self.safe(b["name"]); label = b["mtime"].strftime("%Y-%m-%d %I:%M:%S %p"); size_kb = max(1, round(b["size"] / 1024))
            rows += f'''<div class="card"><h3>{self.safe(label)}</h3><p class="muted">{name} • {size_kb} KB</p><form method="GET" action="/download-backup"><input type="hidden" name="name" value="{name}"><button class="safe" type="submit">Download Backup</button></form><form method="POST" action="/restore-backup" onsubmit="return confirm('Restore this backup?');"><input type="hidden" name="name" value="{name}"><button class="danger" type="submit">Restore This Backup</button></form></div>'''
        if not rows: rows = "<p class='muted'>No backups found yet.</p>"
        raw = f'''<div class="section"><h2>Raw JSON Editor</h2><form method="POST" action="/raw"><textarea name="raw_json">{raw_json}</textarea><button class="primary" type="submit">Save Raw JSON</button></form><p><a class="pill" href="/advanced">Hide Developer Mode</a></p></div>''' if dev else '''<div class="section"><h2>Developer Mode</h2><p class="muted">Raw JSON editing is hidden to prevent accidental changes.</p><p><a class="pill" href="/advanced?dev=1">Enable Developer Mode</a></p></div>'''
        return self.page("Advanced", "advanced", f'''<div class="section"><h2>Configuration Backups</h2><p class="muted">The admin keeps the 10 newest backups automatically.</p>{rows}</div>{raw}''')

    # ---------------- SAVE HANDLERS ----------------
    def handle_save_display(self, data):
        cfg = self.read_config(); cfg.setdefault("overlay", {}); cfg.setdefault("clock", {}); cfg.setdefault("timings", {})
        cfg["overlay"]["enabled"] = True; cfg["overlay"]["text"] = data.get("overlay_text", [""])[0]; cfg["clock"]["enabled"] = "clock_enabled" in data
        try: cfg["timings"]["image_duration"] = int(data.get("image_duration", ["8"])[0])
        except Exception: cfg["timings"]["image_duration"] = 8
        self.write_config(cfg); self.redirect("/display")

    def handle_save_services(self, data):
        cfg = self.read_config(); cfg.setdefault("countdown", {}); cfg["countdown"]["enabled"] = "countdown_enabled" in data
        try: cfg["countdown"]["start_minutes"] = int(data.get("countdown_start_minutes", ["20"])[0])
        except Exception: cfg["countdown"]["start_minutes"] = 20
        cfg["countdown"]["services"] = [{"day": d.strip(), "time": t.strip()} for d,t in zip(data.get("service_day", []), data.get("service_time", [])) if d.strip() and t.strip()]
        self.write_config(cfg); self.redirect("/services")

    def handle_save_events(self, data):
        cfg = self.read_config(); dynamic = []
        for label, date_value, time_value, amount, unit in zip(data.get("dynamic_label", []), data.get("dynamic_date", []), data.get("dynamic_time", []), data.get("dynamic_show_amount", []), data.get("dynamic_show_unit", [])):
            label = label.strip(); date_value = date_value.strip(); time_value = time_value.strip()
            if label and date_value and time_value:
                dynamic.append({"label": label, "target": f"{date_value}T{time_value}:00", "show_before_minutes": self.amount_unit_to_minutes(amount, unit)})
        cfg["dynamic_countdowns"] = dynamic; self.write_config(cfg); self.redirect("/events")

    def handle_save_schedule(self, data):
        cfg = self.read_config(); scheduled = []
        for msg, pri, sd, ed, st, et in zip(data.get("sched_message", []), data.get("sched_priority", []), data.get("sched_start_date", []), data.get("sched_end_date", []), data.get("sched_start_time", []), data.get("sched_end_time", [])):
            msg = msg.strip()
            if not msg: continue
            try: priority = int(pri)
            except Exception: priority = 100
            scheduled.append({"enabled": True, "message": msg, "priority": priority, "start_date": sd.strip(), "end_date": ed.strip(), "start_time": st.strip(), "end_time": et.strip(), "days": []})
        cfg["scheduled_overlays"] = scheduled; self.write_config(cfg); self.redirect("/schedule")


    def handle_save_sync(self, data):
        remote = data.get("sync_remote", ["gdrive"])[0].strip() or "gdrive"
        folder = data.get("sync_folder", ["Weekly"])[0].strip() or "Weekly"
        self.write_sync_config(remote, folder)
        self.redirect("/sync")

    def handle_sync_now(self):
        try:
            subprocess.Popen([SYNC_SCRIPT_PATH])
        except Exception as e:
            print("SYNC NOW ERROR:", e)
        self.redirect("/sync")

    def handle_raw(self, data):
        try:
            self.write_config(json.loads(data.get("raw_json", ["{}"])[0])); self.redirect("/advanced")
        except Exception as e: self.error(f"Raw JSON save failed:\n{e}")

    def handle_restore_backup(self, data):
        name = self.safe_backup_name(data.get("name", [""])[0]); path = os.path.join(self.get_backup_dir(), name)
        if not name or not os.path.exists(path): return self.error("Backup not found.", 404)
        try: self.write_config(self.read_json_file(path, {})); self.redirect("/advanced")
        except Exception as e: self.error(f"Restore failed:\n{e}")

    def handle_download_backup(self):
        q = parse_qs(urlparse(self.path).query); name = self.safe_backup_name(q.get("name", [""])[0]); path = os.path.join(self.get_backup_dir(), name)
        if not name or not os.path.exists(path): return self.error("Backup not found.", 404)
        payload = open(path, "rb").read(); self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Disposition", f'attachment; filename="{name}"'); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)

    def handle_restart(self): subprocess.Popen(["sudo", "systemctl", "restart", "church-display.service"]); self.redirect("/system")
    def handle_reboot(self): subprocess.Popen(["sudo", "reboot"]); self.redirect("/system")

    def redirect(self, location="/"):
        self.send_response(303); self.send_header("Location", location); self.end_headers()

    def error(self, message, status=400):
        self.send_response(status); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(message.encode("utf-8"))


def start_admin_server(config_path, host="0.0.0.0", port=8080):
    ConfigAdminHandler.config_path = config_path
    server = ThreadingHTTPServer((host, port), ConfigAdminHandler)
    print(f"Admin server running on http://{host}:{port}")
    server.serve_forever()








