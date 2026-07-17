from flask import Blueprint, jsonify, render_template
from services.fleet_command_center import build_fleet_command_center

fleet_command_center_bp=Blueprint("fleet_command_center",__name__)

@fleet_command_center_bp.route("/command-center")
def page():
    return render_template("fleet_command_center.html",center=build_fleet_command_center())

@fleet_command_center_bp.route("/command-center/state")
def state():
    return jsonify({"ok":True,**build_fleet_command_center()})
