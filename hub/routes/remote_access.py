from flask import Blueprint, jsonify, render_template

from services.remote_access import remote_access_status

remote_access_bp = Blueprint('remote_access', __name__, url_prefix='/remote-access')


@remote_access_bp.route('')
def remote_access_page():
    return render_template('remote_access.html', active='remote-access', status=remote_access_status())


@remote_access_bp.route('/api/status')
def remote_access_api_status():
    return jsonify(remote_access_status())
