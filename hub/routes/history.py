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
    action_type=request.args.get('action_type','').strip()
    result=request.args.get('result','').strip()
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
    event_filters=dict(
        category=category, display_id=display_id,
        action_type=action_type, result=result, days=days,
    )
    events=query_events(**event_filters, limit=per_page, offset=offset)
    all_for_summary=query_events(**event_filters, limit=2000)
    total_events=count_events(**event_filters)
    categories=sorted({e.get('category','general') for e in query_events(days=90,limit=2000)})
    event_catalog=query_events(days=90,limit=2000)
    action_types=sorted({
        e.get('metadata',{}).get('job_type')
        for e in event_catalog if e.get('metadata',{}).get('job_type')
    })
    return render_template(
        'history.html', active='history', displays=load_config().get('displays', []),
        selected_display=display_id, selected_category=category, days=days, view=view,
        selected_action=action_type, selected_result=result,
        action_types=action_types,
        health_summary=summarize_health(health),
        health_rows=health[:100] if view == 'detailed' else [],
        event_summary=summarize_events(all_for_summary),
        events=events, categories=categories, page=page, per_page=per_page,
        total_events=total_events, has_more=(offset + len(events) < total_events),
    )
