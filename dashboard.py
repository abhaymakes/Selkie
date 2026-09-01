from flask import Blueprint, render_template

dashboard = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard.route("/")
def index():
    return render_template("dashboard.html")


@dashboard.route("/beacons")
def beacons():
    return "All Beacons"


@dashboard.route("/beacons/<beacon_id>")
def beacon_details(beacon_id):
    return f"Beacon details: {beacon_id}"


@dashboard.route("/beacons/<beacon_id>/edit")
def edit_beacon(beacon_id):
    return f"Edit beacon: {beacon_id}"