from flask import Blueprint, render_template

from db_manager import get_session, Beacon

dashboard = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard.route("/")
def index():
    return render_template("dashboard.html")


@dashboard.route("/beacons")
def beacons():
    with get_session() as session:
        beacons = (
            session.query(Beacon)
            .order_by(Beacon.status.desc(), Beacon.last_active.desc())
            .all()
        )

    return render_template("beacons.html", beacons=beacons)


@dashboard.route("/beacons/status")
def beacon_status():
    with get_session() as session:
        beacons = (
            session.query(Beacon)
            .order_by(Beacon.status.desc(), Beacon.last_active.desc())
            .all()
        )

    return render_template("partials/beacon_list.html", beacons=beacons)

import json

@dashboard.route("/beacons/<beacon_id>")
def beacon_details(beacon_id):
    with get_session() as session:
        beacon = session.query(Beacon).filter_by(id=beacon_id).first()

        if not beacon:
            return "Beacon not found", 404

        system_info = beacon.system_info

        json_system_info = json.loads(system_info)

        print("TYPE:", type(json_system_info))
        print("VALUE:", repr(beacon.system_info))

    return render_template(
        "beacon_details.html",
        beacon=beacon,
        system_info=json_system_info
    )


@dashboard.route("/beacons/<beacon_id>/edit")
def edit_beacon(beacon_id):
    return f"Edit beacon: {beacon_id}"
