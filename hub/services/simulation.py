from datetime import datetime

from services.config import load_config, load_hub_settings
from services.media import get_playlist_entry
from services.resilience import load_resilience
from services.schedules import load_schedules, parse_run_at


def display_name(display_id):
    for display in load_config().get('displays', []):
        if display.get('id') == display_id:
            return display.get('name') or display_id
    return display_id


def resolve_simulation(display_id, when):
    if isinstance(when, str):
        when = datetime.fromisoformat(when)
    settings = load_hub_settings()
    remote = settings.get('drive_remote', 'gdrive')
    applicable=[]
    for schedule in load_schedules().get('schedules', []):
        if not schedule.get('enabled', True):
            continue
        if schedule.get('display_id') not in {display_id, 'all'}:
            continue
        run_at=parse_run_at(schedule.get('run_at',''))
        if not run_at or run_at > when:
            continue
        recurrence=schedule.get('recurrence','once')
        if recurrence == 'daily':
            candidate=when.replace(hour=run_at.hour, minute=run_at.minute, second=0, microsecond=0)
            if candidate > when:
                continue
        applicable.append((run_at, schedule))
    applicable.sort(key=lambda pair: pair[0], reverse=True)
    chosen=applicable[0][1] if applicable else None
    folder=''
    playlist=[]
    job_type=''
    if chosen:
        payload=chosen.get('payload') or {}
        folder=str(payload.get('folder') or '').strip().strip('/')
        job_type=chosen.get('job_type','')
        if folder:
            playlist=get_playlist_entry(payload.get('remote') or remote, folder).get('published_order', [])
    resilience=load_resilience()
    maintenance=resilience.get('maintenance', {})
    return {
        'display_id': display_id,
        'display_name': display_name(display_id),
        'when': when.isoformat(timespec='minutes'),
        'maintenance_enabled': bool(maintenance.get('enabled')),
        'maintenance_message': maintenance.get('message',''),
        'schedule': chosen,
        'job_type': job_type,
        'folder': folder,
        'playlist': playlist,
        'first_media': playlist[0] if playlist else '',
        'reason': 'maintenance' if maintenance.get('enabled') else ('schedule' if chosen else 'current/default'),
    }
