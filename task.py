from flask import Blueprint, render_template, request, jsonify, redirect, url_for

from db_manager import get_session, Beacon, Task, TaskExecution
from sqlalchemy import or_

import json

from datetime import datetime
from zoneinfo import ZoneInfo

task = Blueprint("task", __name__, url_prefix="/task")


# ============================================================
# CREATE TASK
# ============================================================


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


# ============================================================
# VIEW TASKS
# ============================================================


@task.route("/tasks/<beacon_id>", methods=["GET"])
def view_tasks(beacon_id):
    """View and manage tasks of a beacon."""

    with get_session() as session:

        beacon = session.query(Beacon).filter_by(id=beacon_id).first()

        if not beacon:
            return "Beacon not found", 404

        tasks = (
            session.query(Task)
            .filter(or_(Task.beacon_id == beacon_id, Task.is_global.is_(True)))
            .order_by(Task.created_at.asc())
            .all()
        )

        task_data = []

        for task_item in tasks:

            execution = (
                session.query(TaskExecution)
                .filter_by(task_id=task_item.id, beacon_id=beacon_id)
                .first()
            )

            task_data.append(
                {
                    "id": task_item.id,
                    "name": task_item.name,
                    "description": task_item.description,
                    "task_type": task_item.task_type,
                    "parameters": task_item.parameters or {},
                    "is_global": task_item.is_global,
                    "created_at": task_item.created_at,
                    "execution": {
                        "status": execution.status if execution else "pending",
                        "assigned_at": execution.assigned_at if execution else None,
                        "started_at": execution.started_at if execution else None,
                        "completed_at": execution.completed_at if execution else None,
                        "result": execution.result if execution else None,
                        "error": execution.error if execution else None,
                    },
                }
            )

    return render_template("tasks.html", beacon=beacon, tasks=task_data)


# ============================================================
# GET ONE TASK FOR BEACON
# ============================================================


@task.route("/tasks/get/<beacon_id>", methods=["GET"])
def get_task(beacon_id):

    with get_session() as session:

        task = (
            session.query(Task)
            .filter(or_(Task.beacon_id == beacon_id, Task.is_global.is_(True)))
            .order_by(Task.created_at.asc())
            .all()
        )

        for available_task in task:

            execution = (
                session.query(TaskExecution)
                .filter_by(task_id=available_task.id, beacon_id=beacon_id)
                .first()
            )

            # This beacon has already received this task
            if execution:
                continue

            # Create execution record for this beacon
            execution = TaskExecution(
                task_id=available_task.id,
                beacon_id=beacon_id,
                status="assigned",
                assigned_at=datetime.now(ZoneInfo("Asia/Kolkata")),
            )

            session.add(execution)
            session.commit()

            return (
                jsonify(
                    {
                        "task": {
                            "id": available_task.id,
                            "task": available_task.task_type,
                            "args": available_task.parameters or {},
                        }
                    }
                ),
                200,
            )

        return jsonify({"task": None}), 200


# ============================================================
# TASK EXECUTION STATUS
# ============================================================


def set_task_status(task_id, beacon_id, status, assigned_at=None, started_at=None):
    with get_session() as session:

        execution = (
            session.query(TaskExecution)
            .filter_by(task_id=task_id, beacon_id=beacon_id)
            .first()
        )

        if not execution:
            return False

        execution.status = status

        if assigned_at is not None:
            execution.assigned_at = assigned_at

        if started_at is not None:
            execution.started_at = started_at

        session.commit()

        return True


# ============================================================
# TASK EXECUTION RESULT
# ============================================================


def set_task_result(
    task_id, beacon_id, status, result=None, error=None, completed_at=None
):
    with get_session() as session:

        execution = (
            session.query(TaskExecution)
            .filter_by(task_id=task_id, beacon_id=beacon_id)
            .first()
        )

        if not execution:
            return False

        execution.status = status
        execution.result = result
        execution.error = error
        execution.completed_at = completed_at

        session.commit()

        return True


# ============================================================
# SET TASK EXECUTION STATUS / RESULT
# ============================================================


@task.route("/tasks/set", methods=["POST"])
def set_task():
    data = request.get_json()

    task_id = data.get("task_id")
    beacon_id = data.get("beacon_id")
    status = data.get("status")

    if not task_id or not beacon_id or not status:
        return jsonify({"error": "task_id, beacon_id and status are required"}), 400

    allowed_statuses = {"assigned", "running", "completed", "failed"}

    if status not in allowed_statuses:
        return jsonify({"error": "Invalid task status"}), 400

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    try:

        if status == "assigned":

            success = set_task_status(
                task_id=task_id, beacon_id=beacon_id, status="assigned", assigned_at=now
            )

        elif status == "running":

            success = set_task_status(
                task_id=task_id, beacon_id=beacon_id, status="running", started_at=now
            )

        elif status == "completed":

            success = set_task_result(
                task_id=task_id,
                beacon_id=beacon_id,
                status="completed",
                result=data.get("result"),
                completed_at=now,
            )

        elif status == "failed":

            success = set_task_result(
                task_id=task_id,
                beacon_id=beacon_id,
                status="failed",
                error=data.get("error"),
                completed_at=now,
            )

        if not success:
            return jsonify({"error": "Task execution not found"}), 404

        return (
            jsonify(
                {
                    "success": True,
                    "task_id": task_id,
                    "beacon_id": beacon_id,
                    "status": status,
                }
            ),
            200,
        )

    except Exception as e:

        print("ERROR IN /tasks/set:")
        print(type(e).__name__)
        print(str(e))

        return jsonify({"error": str(e)}), 500


# ============================================================
# DELETE TASK
# ============================================================


@task.route("/<beacon_id>/<task_id>/delete", methods=["POST"])
def delete_task(beacon_id, task_id):
    with get_session() as session:

        task_to_delete = session.query(Task).filter_by(id=task_id).first()

        if not task_to_delete:
            return "Task not found", 404

        session.delete(task_to_delete)
        session.commit()

    return redirect(url_for("task.view_tasks", beacon_id=beacon_id))
