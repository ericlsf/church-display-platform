import json
from datetime import datetime, timedelta

from services.database import connection, initialize_database
from services.jobs import parse_iso


def initialize_history():
    initialize_database()
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS health_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                display_id TEXT NOT NULL,
                online INTEGER NOT NULL DEFAULT 0,
                display_app_running INTEGER NOT NULL DEFAULT 0,
                cpu_temp REAL,
                memory_percent REAL,
                disk_percent REAL,
                sync_state TEXT,
                current_media TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_health_display_time
                ON health_samples(display_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_health_time
                ON health_samples(created_at DESC);
            """
        )


def _number(value):
    if value is None:
        return None
    text = str(value).replace('°C', '').replace('%', '').strip()
    try:
        return float(text)
    except Exception:
        return None


def record_health_sample(display_id, payload):
    initialize_history()
    system = payload.get('system') or {}
    player = payload.get('player') or {}
    sync = payload.get('sync') or {}
    display_app = payload.get('display_app') or {}
    with connection() as db:
        db.execute(
            """
            INSERT INTO health_samples(
                display_id, online, display_app_running, cpu_temp,
                memory_percent, disk_percent, sync_state, current_media,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                display_id,
                1,
                1 if display_app.get('running') else 0,
                _number(system.get('cpu_temp')),
                _number(system.get('memory')),
                _number(system.get('disk')),
                str(sync.get('state') or ''),
                str(player.get('current_media') or ''),
                json.dumps(payload, sort_keys=True),
            ),
        )
        # Keep roughly 90 days of heartbeat history.
        cutoff = (datetime.now() - timedelta(days=90)).isoformat(timespec='seconds')
        db.execute('DELETE FROM health_samples WHERE created_at < ?', (cutoff,))


def query_health(display_id='', days=7, limit=2000):
    initialize_history()
    cutoff = (datetime.now() - timedelta(days=max(1, int(days)))).isoformat(timespec='seconds')
    sql = "SELECT * FROM health_samples WHERE created_at >= ?"
    params = [cutoff]
    if display_id:
        sql += " AND display_id = ?"
        params.append(display_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(max(1, min(int(limit), 5000)))
    with connection() as db:
        rows = db.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def summarize_health(rows):
    by_display = {}
    for row in rows:
        item = by_display.setdefault(row['display_id'], {
            'display_id': row['display_id'], 'samples': 0, 'online_samples': 0,
            'app_running_samples': 0, 'cpu_values': [], 'memory_values': [],
            'disk_values': [], 'sync_errors': 0,
        })
        item['samples'] += 1
        item['online_samples'] += int(bool(row.get('online')))
        item['app_running_samples'] += int(bool(row.get('display_app_running')))
        if row.get('cpu_temp') is not None: item['cpu_values'].append(row['cpu_temp'])
        if row.get('memory_percent') is not None: item['memory_values'].append(row['memory_percent'])
        if row.get('disk_percent') is not None: item['disk_values'].append(row['disk_percent'])
        if str(row.get('sync_state', '')).lower() in {'error', 'failed'}: item['sync_errors'] += 1
    result=[]
    for item in by_display.values():
        total=item['samples'] or 1
        result.append({
            'display_id': item['display_id'],
            'samples': item['samples'],
            'uptime_percent': round(item['online_samples'] * 100 / total, 1),
            'app_uptime_percent': round(item['app_running_samples'] * 100 / total, 1),
            'avg_cpu_temp': round(sum(item['cpu_values'])/len(item['cpu_values']),1) if item['cpu_values'] else None,
            'avg_memory': round(sum(item['memory_values'])/len(item['memory_values']),1) if item['memory_values'] else None,
            'avg_disk': round(sum(item['disk_values'])/len(item['disk_values']),1) if item['disk_values'] else None,
            'sync_errors': item['sync_errors'],
        })
    return sorted(result, key=lambda x: x['display_id'])


def query_events(
    category='', display_id='', action_type='', result='',
    days=30, limit=500, offset=0,
):
    initialize_database()
    cutoff=(datetime.now()-timedelta(days=max(1,int(days)))).isoformat(timespec='seconds')
    sql='SELECT created_at, category, level, message, metadata_json FROM events WHERE created_at >= ?'
    params=[cutoff]
    if category:
        sql += ' AND category = ?'; params.append(category)
    if display_id:
        sql += " AND (message LIKE ? OR metadata_json LIKE ?)"
        needle=f'%{display_id}%'; params.extend([needle, needle])
    if action_type:
        sql += " AND metadata_json LIKE ?"
        params.append(f'%"job_type": "{action_type}"%')
    if result:
        sql += " AND (level = ? OR metadata_json LIKE ?)"
        params.extend([result, f'%"status": "{result}"%'])
    sql += ' ORDER BY id DESC LIMIT ? OFFSET ?'; params.extend([max(1,min(int(limit),2000)), max(0,int(offset))])
    with connection() as db:
        rows=db.execute(sql,params).fetchall()
    result=[]
    for row in rows:
        item=dict(row)
        try: item['metadata']=json.loads(item.pop('metadata_json') or '{}')
        except Exception: item['metadata']={}
        parsed = parse_iso(item.get('created_at', ''))
        item['created_display'] = (
            parsed.strftime("%b %d, %Y %I:%M %p").replace(" 0", " ")
            if parsed else item.get('created_at', 'Unknown')
        )
        result.append(item)
    return result


def count_events(category='', display_id='', action_type='', result='', days=30):
    initialize_database()
    cutoff=(datetime.now()-timedelta(days=max(1,int(days)))).isoformat(timespec='seconds')
    sql='SELECT COUNT(*) AS total FROM events WHERE created_at >= ?'
    params=[cutoff]
    if category:
        sql += ' AND category = ?'; params.append(category)
    if display_id:
        sql += ' AND (message LIKE ? OR metadata_json LIKE ?)'
        needle=f'%{display_id}%'; params.extend([needle, needle])
    if action_type:
        sql += " AND metadata_json LIKE ?"
        params.append(f'%"job_type": "{action_type}"%')
    if result:
        sql += " AND (level = ? OR metadata_json LIKE ?)"
        params.extend([result, f'%"status": "{result}"%'])
    with connection() as db:
        row=db.execute(sql,params).fetchone()
    return int(row['total'] if row else 0)


def summarize_events(events):
    summary={}
    for event in events:
        key=event.get('category') or 'general'
        item=summary.setdefault(key, {'category': key, 'count': 0, 'latest_at': '', 'latest_message': ''})
        item['count'] += 1
        if not item['latest_at'] or str(event.get('created_at','')) > item['latest_at']:
            item['latest_at']=event.get('created_at','')
            item['latest_message']=event.get('message','')
    return sorted(summary.values(), key=lambda item: (-item['count'], item['category']))
