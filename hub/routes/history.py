from flask import Blueprint, render_template, request
from services.config import load_config
from services.history import (
    count_events, query_events, query_health, summarize_events, summarize_health,
)

history_bp=Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('')
def history_page():
    display_id=request.args.get('display_id','').strip()
    category=request.args.get('category','').strip()
    view=request.args.get('view','compact').strip()
    if view not in {'compact','detailed'}:
        view='compact'
    try: days=max(1,min(int(request.args.get('days','7')),90))
    except Exception: days=7
    try: page=max(1,int(request.args.get('page','1')))
    except Exception: page=1
    per_page=20 if view == 'compact' else 50
    offset=(page-1)*per_page

    health=query_health(display_id=display_id, days=days, limit=2000)
    events=query_events(category=category, display_id=display_id, days=days, limit=per_page, offset=offset)
    all_for_summary=query_events(category=category, display_id=display_id, days=days, limit=2000)
    total_events=count_events(category=category, display_id=display_id, days=days)
    categories=sorted({e.get('category','general') for e in query_events(days=90,limit=2000)})
    return render_template(
        'history.html', active='history', displays=load_config().get('displays', []),
        selected_display=display_id, selected_category=category, days=days, view=view,
        health_summary=summarize_health(health),
        health_rows=health[:100] if view == 'detailed' else [],
        event_summary=summarize_events(all_for_summary),
        events=events, categories=categories, page=page, per_page=per_page,
        total_events=total_events, has_more=(offset + len(events) < total_events),
    )
