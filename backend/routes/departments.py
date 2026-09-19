"""Department configuration APIs used by employee management."""

from flask import Blueprint, jsonify, request

from utils.auth import require_super_admin
from utils.db import get_db


departments_bp = Blueprint(
    "departments",
    __name__,
    url_prefix="/api/admin/departments",
)


def _text(value, max_length):
    return str(value or "").strip()[:max_length]


def _status(value):
    return value if value in {"active", "disabled"} else "active"


def _sort_order(value, default=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _serialize_department(conn, row):
    employee_count = conn.execute(
        "SELECT COUNT(*) AS total FROM employees WHERE department_id = ?",
        (row["id"],),
    ).fetchone()["total"]
    return {
        "id": row["id"],
        "name": row["name"],
        "parentId": row["parent_id"],
        "status": row["status"],
        "sortOrder": row["sort_order"],
        "employeeCount": employee_count,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _department_row(conn, department_id):
    return conn.execute(
        """
        SELECT id, name, parent_id, status, sort_order, created_at, updated_at
        FROM departments
        WHERE id = ?
        """,
        (department_id,),
    ).fetchone()


def _validate_parent(conn, parent_id, department_id=None):
    if parent_id is None:
        return
    if department_id is not None and parent_id == department_id:
        raise ValueError("上级部门不能是当前部门")
    if not _department_row(conn, parent_id):
        raise ValueError("上级部门不存在")


@departments_bp.route("", methods=["GET"])
@require_super_admin
def list_departments():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, parent_id, status, sort_order, created_at, updated_at
            FROM departments
            ORDER BY sort_order, id
            """
        ).fetchall()
        departments = [_serialize_department(conn, row) for row in rows]
    return jsonify({"success": True, "departments": departments})


@departments_bp.route("", methods=["POST"])
@require_super_admin
def create_department():
    data = request.get_json(silent=True) or {}
    name = _text(data.get("name"), 80)
    if not name:
        return jsonify({"success": False, "message": "部门名称不能为空"}), 400
    parent_id = data.get("parentId")
    try:
        parent_id = None if parent_id in (None, "") else int(parent_id)
        sort_order = _sort_order(data.get("sortOrder"))
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            _validate_parent(conn, parent_id)
            if conn.execute(
                "SELECT 1 FROM departments WHERE name = ? COLLATE NOCASE",
                (name,),
            ).fetchone():
                return jsonify({"success": False, "message": "部门名称已存在"}), 409
            cursor = conn.execute(
                """
                INSERT INTO departments (name, parent_id, status, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (name, parent_id, _status(data.get("status")), sort_order),
            )
            department = _serialize_department(
                conn, _department_row(conn, cursor.lastrowid)
            )
    except (TypeError, ValueError) as exc:
        return jsonify({"success": False, "message": str(exc) or "部门参数无效"}), 400
    return jsonify({"success": True, "message": "部门已创建", "department": department}), 201


@departments_bp.route("/<int:department_id>", methods=["PUT"])
@require_super_admin
def update_department(department_id):
    data = request.get_json(silent=True) or {}
    name = _text(data.get("name"), 80)
    if not name:
        return jsonify({"success": False, "message": "部门名称不能为空"}), 400
    try:
        parent_id = None if data.get("parentId") in (None, "") else int(data["parentId"])
        sort_order = _sort_order(data.get("sortOrder"))
        next_status = _status(data.get("status"))
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            current = _department_row(conn, department_id)
            if not current:
                return jsonify({"success": False, "message": "部门不存在"}), 404
            _validate_parent(conn, parent_id, department_id)
            if conn.execute(
                """
                SELECT 1 FROM departments
                WHERE name = ? COLLATE NOCASE AND id <> ?
                """,
                (name, department_id),
            ).fetchone():
                return jsonify({"success": False, "message": "部门名称已存在"}), 409
            if next_status == "disabled" and conn.execute(
                "SELECT 1 FROM employees WHERE department_id = ?",
                (department_id,),
            ).fetchone():
                return jsonify(
                    {
                        "success": False,
                        "message": "该部门还有员工，不能停用，请先调整员工部门",
                    }
                ), 409
            conn.execute(
                """
                UPDATE departments
                SET name = ?, parent_id = ?, status = ?, sort_order = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, parent_id, next_status, sort_order, department_id),
            )
            department = _serialize_department(
                conn, _department_row(conn, department_id)
            )
    except (TypeError, ValueError) as exc:
        return jsonify({"success": False, "message": str(exc) or "部门参数无效"}), 400
    return jsonify({"success": True, "message": "部门已更新", "department": department})


@departments_bp.route("/<int:department_id>", methods=["DELETE"])
@require_super_admin
def delete_department(department_id):
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = _department_row(conn, department_id)
        if not current:
            return jsonify({"success": False, "message": "部门不存在"}), 404
        employee_count = conn.execute(
            "SELECT COUNT(*) AS total FROM employees WHERE department_id = ?",
            (department_id,),
        ).fetchone()["total"]
        if employee_count:
            return jsonify(
                {
                    "success": False,
                    "message": f"该部门还有 {employee_count} 名员工，不能删除",
                }
            ), 409
        child_count = conn.execute(
            "SELECT COUNT(*) AS total FROM departments WHERE parent_id = ?",
            (department_id,),
        ).fetchone()["total"]
        if child_count:
            return jsonify(
                {"success": False, "message": "该部门还有下级部门，不能删除"}
            ), 409
        conn.execute("DELETE FROM departments WHERE id = ?", (department_id,))
    return jsonify({"success": True, "message": "部门已删除"})
