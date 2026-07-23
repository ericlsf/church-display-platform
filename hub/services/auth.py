import sqlite3
from functools import wraps
from pathlib import Path

from flask import abort, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
DB_PATH = DATA_DIR / 'auth.db'
ROLES = ('admin', 'editor', 'viewer')


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    with connect() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','editor','viewer')),
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            username TEXT,
            role TEXT,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            remote_addr TEXT,
            status_code INTEGER,
            details TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        ''')


def user_count():
    init_auth_db()
    with connect() as conn:
        return int(conn.execute('SELECT COUNT(*) FROM users').fetchone()[0])


def create_user(username, password, role='viewer', display_name=None):
    username = (username or '').strip()
    password = password or ''
    role = (role or 'viewer').strip().lower()
    display_name = (display_name or username).strip()
    if not username:
        raise ValueError('Username is required')
    if len(password) < 10:
        raise ValueError('Password must be at least 10 characters')
    if role not in ROLES:
        raise ValueError('Invalid role')
    init_auth_db()
    with connect() as conn:
        conn.execute('INSERT INTO users (username, display_name, password_hash, role) VALUES (?, ?, ?, ?)',
                     (username, display_name, generate_password_hash(password), role))


def update_user(user_id, *, display_name=None, role=None, enabled=None, password=None):
    init_auth_db()
    fields, values = [], []
    if display_name is not None:
        fields.append('display_name = ?'); values.append(display_name.strip())
    if role is not None:
        role = role.strip().lower()
        if role not in ROLES:
            raise ValueError('Invalid role')
        fields.append('role = ?'); values.append(role)
    if enabled is not None:
        fields.append('enabled = ?'); values.append(1 if enabled else 0)
    if password:
        if len(password) < 10:
            raise ValueError('Password must be at least 10 characters')
        fields.append('password_hash = ?'); values.append(generate_password_hash(password))
    if not fields:
        return
    fields.append('updated_at = CURRENT_TIMESTAMP')
    values.append(int(user_id))
    with connect() as conn:
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)


def delete_user(user_id):
    init_auth_db()
    with connect() as conn:
        conn.execute('DELETE FROM users WHERE id = ?', (int(user_id),))


def authenticate(username, password):
    init_auth_db()
    with connect() as conn:
        row = conn.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE AND enabled = 1',
                           ((username or '').strip(),)).fetchone()
    if not row or not check_password_hash(row['password_hash'], password or ''):
        return None
    return dict(row)


def get_user(user_id):
    if not user_id:
        return None
    init_auth_db()
    with connect() as conn:
        row = conn.execute('SELECT id, username, display_name, role, enabled, created_at, updated_at FROM users WHERE id = ?',
                           (int(user_id),)).fetchone()
    return dict(row) if row else None


def list_users():
    init_auth_db()
    with connect() as conn:
        rows = conn.execute('SELECT id, username, display_name, role, enabled, created_at, updated_at FROM users ORDER BY username COLLATE NOCASE').fetchall()
    return [dict(row) for row in rows]


def log_audit(status_code=None, details=''):
    user = getattr(g, 'current_user', None) or {}
    init_auth_db()
    with connect() as conn:
        conn.execute('''INSERT INTO audit_log
            (user_id, username, role, method, path, remote_addr, status_code, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user.get('id'), user.get('username'), user.get('role'), request.method,
             request.path, request.remote_addr, status_code, details[:1000]))


def list_audit(limit=250):
    init_auth_db()
    with connect() as conn:
        rows = conn.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT ?', (int(limit),)).fetchall()
    return [dict(row) for row in rows]


def load_current_user():
    g.current_user = get_user(session.get('user_id'))


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user:
                return redirect(url_for('auth.login', next=request.full_path))
            if user.get('role') not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
