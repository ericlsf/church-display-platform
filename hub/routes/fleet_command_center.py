from flask import Blueprint, jsonify, redirect, url_for
from services.fleet_command_center import build_fleet_command_center

fleet_command_center_bp=Blueprint("fleet_command_center",__name__)

@fleet_command_center_bp.route("/command-center")
def page():
    return redirect(url_for("fleet_dashboard.page"), code=302)

@fleet_command_center_bp.route("/command-center/state")
def state():
    return jsonify({"ok":True,**build_fleet_command_center()})
