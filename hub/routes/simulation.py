from datetime import datetime
from flask import Blueprint, render_template, request
from services.config import load_config
from services.simulation import resolve_simulation

simulation_bp=Blueprint('simulation', __name__, url_prefix='/simulation')

@simulation_bp.route('')
def simulation_page():
    displays=load_config().get('displays', [])
    display_id=request.args.get('display_id','').strip()
    when_raw=request.args.get('when','').strip()
    if not when_raw:
        when_raw=datetime.now().isoformat(timespec='minutes')
    result=None; error=''
    if display_id:
        try: result=resolve_simulation(display_id, when_raw)
        except Exception as exc: error=str(exc)
    return render_template('simulation.html', active='simulation', displays=displays,
                           selected_display=display_id, selected_when=when_raw,
                           result=result, error=error)
