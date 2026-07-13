from flask import Blueprint, render_template, request
from services.config import load_config
from services.history import query_events, query_health, summarize_health

history_bp=Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('')
def history_page():
    display_id=request.args.get('display_id','').strip()
    category=request.args.get('category','').strip()
    try: days=max(1,min(int(request.args.get('days','7')),90))
    except Exception: days=7
    health=query_health(display_id=display_id, days=days)
    events=query_events(category=category, display_id=display_id, days=days)
    categories=sorted({e.get('category','general') for e in query_events(days=90,limit=2000)})
    return render_template('history.html', active='history', displays=load_config().get('displays', []),
                           selected_display=display_id, selected_category=category, days=days,
                           health_summary=summarize_health(health), health_rows=health[:200],
                           events=events, categories=categories)
