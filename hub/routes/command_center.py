from flask import Blueprint, jsonify, render_template
from services.command_center import command_center_data

command_center_bp = Blueprint("command_center", __name__, url_prefix="/command-center")

@command_center_bp.route("")
def page():
    return render_template("command_center.html", active="command_center", **command_center_data())

@command_center_bp.route("/summary")
def summary():
    data = command_center_data()
    return jsonify({"ok": True, "summary": data["summary"], "generated_at": data["generated_at"]})
