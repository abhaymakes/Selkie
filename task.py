from flask import Blueprint, render_template, request

from db_manager import get_session, Beacon, Task
from sqlalchemy import or_

task = Blueprint("task", __name__, url_prefix="/task")


@task.route("/create", methods=["POST"])
def create_task():
    request_data = request.json

    print(request_data)


@task.route("/tasks/<int:beacon_id>", methods=["GET"])
def view_tasks(beacon_id):
    """View and manage tasks of a beacon."""
    with get_session() as session:
        tasks = (
            session.query(Task)
            .join(Beacon)
            .filter(or_(Beacon.id == beacon_id, Task.is_global == True))
            .all()
        )
