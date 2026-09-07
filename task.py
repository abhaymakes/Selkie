from flask import Blueprint, render_template, request, jsonify, redirect, url_for

from db_manager import get_session, Beacon, Task
from sqlalchemy import or_
import json

task = Blueprint("task", __name__, url_prefix="/task")


@task.route("/create", methods=["POST"])
def create_task():
    request_data = request.form

    name = request_data.get("name")
    task_type = request_data.get("task_type")
    description = request_data.get("description")
    beacon_id = request_data.get("beacon_id")

    is_global = request_data.get("is_global") == "on"

    parameters_raw = request_data.get("parameters", "").strip()

    if parameters_raw:
        try:
            parameters = json.loads(parameters_raw)
        except json.JSONDecodeError:
            return "Invalid parameters JSON", 400
    else:
        parameters = None

    if not name or not task_type:
        return "Name and task type are required", 400

    if is_global:
        beacon_id = None

    with get_session() as session:

        if beacon_id:
            beacon = session.query(Beacon).filter_by(id=beacon_id).first()

            if not beacon:
                return "Beacon not found", 404

        new_task = Task(
            beacon_id=beacon_id,
            is_global=is_global,
            name=name,
            description=description,
            task_type=task_type,
            parameters=parameters,
        )

        session.add(new_task)
        session.commit()

    if is_global:
        return redirect("/dashboard/beacons")

    return redirect(url_for("task.view_tasks", beacon_id=beacon_id))


@task.route("/<beacon_id>/<task_id>/delete", methods=["POST"])
def delete_task(beacon_id, task_id):
    with get_session() as session:
        task_to_delete = session.query(Task).filter_by(id=task_id).first()

        if not task_to_delete:
            return "Task not found", 404

        session.delete(task_to_delete)
        session.commit()

    return redirect(url_for("task.view_tasks", beacon_id=beacon_id))


@task.route("/tasks/<beacon_id>", methods=["GET"])
def view_tasks(beacon_id):
    """View and manage tasks of a beacon."""

    with get_session() as session:
        beacon = session.query(Beacon).filter_by(id=beacon_id).first()

        if not beacon:
            return "Beacon not found", 404

        tasks = (
            session.query(Task)
            .join(Beacon, isouter=True)
            .filter(or_(Task.beacon_id == beacon_id, Task.is_global.is_(True)))
            .all()
        )

    return render_template("tasks.html", beacon=beacon, tasks=tasks)


@task.route("/tasks/get/<beacon_id>", methods=["GET"])
def get_task(beacon_id):
    with get_session() as session:
        task = (
            session.query(Task)
            .filter(
                Task.status == "pending",
                or_(Task.beacon_id == beacon_id, Task.is_global.is_(True)),
            )
            .order_by(Task.created_at.asc())
            .first()
        )

        if not task:
            return jsonify({"task": None}), 200

        return (
            jsonify(
                {
                    "task": {
                        "id": task.id,
                        "task": task.task_type,
                        "args": task.parameters or {},
                    }
                }
            ),
            200,
        )

@task.route("/tasks/set", methods=["POST"])
def set_task():
    data = request.get_json()

    task_id = data.get("task_id")
    beacon_id = data.get("beacon_id")
    status = data.get("status")

    if not task_id or not beacon_id or not status:
        return jsonify({
            "error": "task_id, beacon_id and status are required"
        }), 400

    if status not in ["assigned", "running", "completed", "failed"]:
        return jsonify({
            "error": "Invalid task status"
        }), 400

    now = datetime.now()

    try:
        # Status update
        if status == "assigned":
            db_manager.set_task_status(
                task_id=task_id,
                beacon_id=beacon_id,
                status=status,
                assigned_at=now
            )

        elif status == "running":
            db_manager.set_task_status(
                task_id=task_id,
                beacon_id=beacon_id,
                status=status,
                started_at=now
            )

        # Final result
        elif status == "completed":
            db_manager.set_task_result(
                task_id=task_id,
                beacon_id=beacon_id,
                status=status,
                result=data.get("result"),
                completed_at=now
            )

        elif status == "failed":
            db_manager.set_task_result(
                task_id=task_id,
                beacon_id=beacon_id,
                status=status,
                error=data.get("error"),
                completed_at=now
            )

        return jsonify({
            "success": True,
            "task_id": task_id,
            "beacon_id": beacon_id,
            "status": status
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500