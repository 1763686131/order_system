"""Super-admin role and permission management APIs."""

import re

from flask import Blueprint, jsonify, request, session

from utils.auth import get_current_user, require_super_admin
from utils.db import get_db
from utils.permission_catalog import ALL_PERMISSION_CODES, PERMISSION_MODULES


access_bp = Blueprint("access", __name__, url_prefix="/api/admin")
ROLE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,39}$")


def _text(value, max_length):
    return str(value or "").strip()[:max_length]


def _permission_codes(value):
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        code = _text(item, 100)
        if code and code not in result:
            result.append(code)
    return result


def _integer_ids(value):
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        try:
            item_id = int(item)
        except (TypeError, ValueError):
            continue
        if item_id not in result:
            result.append(item_id)
    return result


def _serialize_role(conn, row):
    permission_codes = list(ALL_PERMISSION_CODES) if row["full_access"] else [
        permission["code"]
        for permission in conn.execute(
            """
            SELECT permissions.code
            FROM permissions
            INNER JOIN role_permissions
                ON role_permissions.permission_id = permissions.id
            WHERE role_permissions.role_id = ?
            ORDER BY permissions.sort_order, permissions.id
            """,
            (row["id"],),
        ).fetchall()
    ]
    member_ids = [
        member["id"]
        for member in conn.execute(
            """
            SELECT employees.id
            FROM employee_roles
            INNER JOIN employees
                ON employees.id = employee_roles.employee_id
            WHERE employee_roles.role_id = ?
            ORDER BY employees.display_name, employees.id
            """,
            (row["id"],),
        ).fetchall()
    ]
    store_ids = [
        item["store_id"]
        for item in conn.execute(
            "SELECT store_id FROM role_stores WHERE role_id = ? ORDER BY store_id",
            (row["id"],),
        ).fetchall()
    ]
    warehouse_ids = [
        item["warehouse_id"]
        for item in conn.execute(
            """
            SELECT warehouse_id
            FROM role_warehouses
            WHERE role_id = ?
            ORDER BY warehouse_id
            """,
            (row["id"],),
        ).fetchall()
    ]
    return {
        "id": row["id"],
        "code": row["code"],
        "name": row["name"],
        "description": row["description"],
        "status": row["status"],
        "isSystem": bool(row["is_system"]),
        "fullAccess": bool(row["full_access"]),
        "canAccessAdmin": bool(row["can_access_admin"]),
        "longSession": bool(row["long_session"]),
        "dataScope": row["data_scope"],
        "permissionCodes": permission_codes,
        "memberIds": member_ids,
        "memberCount": len(member_ids),
        "storeIds": store_ids,
        "warehouseIds": warehouse_ids,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _role_row(conn, role_id):
    return conn.execute(
        """
        SELECT id, code, name, description, status, is_system,
               full_access, can_access_admin, long_session,
               data_scope, created_at, updated_at
        FROM roles WHERE id = ?
        """,
        (role_id,),
    ).fetchone()


def _replace_permissions(conn, role_id, codes):
    if not codes:
        conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
        return
    placeholders = ",".join("?" for _ in codes)
    rows = conn.execute(
        f"SELECT id, code FROM permissions WHERE code IN ({placeholders})",
        codes,
    ).fetchall()
    if len(rows) != len(codes):
        raise ValueError("包含不存在的权限项")
    permission_ids = [row["id"] for row in rows]
    conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
    for permission_id in permission_ids:
        conn.execute(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            VALUES (?, ?)
            """,
            (role_id, permission_id),
        )


def _replace_scope(conn, role_id, store_ids, warehouse_ids):
    conn.execute("DELETE FROM role_stores WHERE role_id = ?", (role_id,))
    conn.execute("DELETE FROM role_warehouses WHERE role_id = ?", (role_id,))
    for store_id in store_ids:
        conn.execute(
            "INSERT INTO role_stores (role_id, store_id) VALUES (?, ?)",
            (role_id, store_id),
        )
    for warehouse_id in warehouse_ids:
        conn.execute(
            """
            INSERT INTO role_warehouses (role_id, warehouse_id)
            VALUES (?, ?)
            """,
            (role_id, warehouse_id),
        )


def _refresh_current_session_version(conn, affected_user_ids):
    current_user = get_current_user()
    if not current_user or current_user["id"] not in affected_user_ids:
        return
    row = conn.execute(
        "SELECT permission_version FROM users WHERE id = ?",
        (current_user["id"],),
    ).fetchone()
    if row:
        session["permission_version"] = int(row["permission_version"] or 1)


@access_bp.route("/permissions", methods=["GET"])
@require_super_admin
def list_permissions():
    return jsonify({"success": True, "modules": PERMISSION_MODULES})


@access_bp.route("/roles", methods=["GET"])
@require_super_admin
def list_roles():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, code, name, description, status, is_system,
                   full_access, can_access_admin, long_session,
                   data_scope, created_at, updated_at
            FROM roles
            ORDER BY is_system DESC, status, id
            """
        ).fetchall()
        roles = [_serialize_role(conn, row) for row in rows]
    return jsonify({"success": True, "roles": roles})


@access_bp.route("/roles", methods=["POST"])
@require_super_admin
def create_role():
    data = request.get_json(silent=True) or {}
    code = _text(data.get("code"), 40).lower()
    name = _text(data.get("name"), 80)
    description = _text(data.get("description"), 300)
    status = "disabled" if data.get("status") == "disabled" else "active"
    can_access_admin = 1 if data.get("canAccessAdmin") else 0
    long_session = 1 if data.get("longSession") else 0
    data_scope = _text(data.get("dataScope"), 30) or "all"
    permission_codes = _permission_codes(data.get("permissionCodes"))
    store_ids = _integer_ids(data.get("storeIds"))
    warehouse_ids = _integer_ids(data.get("warehouseIds"))
    if not ROLE_CODE_PATTERN.fullmatch(code):
        return jsonify(
            {
                "success": False,
                "message": "权限组编码需以字母开头，只能包含小写字母、数字和下划线",
            }
        ), 400
    if not name:
        return jsonify({"success": False, "message": "权限组名称不能为空"}), 400

    try:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute(
                "SELECT 1 FROM roles WHERE code = ? COLLATE NOCASE",
                (code,),
            ).fetchone():
                return jsonify({"success": False, "message": "权限组编码已存在"}), 409
            cursor = conn.execute(
                """
                INSERT INTO roles (
                    code, name, description, status, is_system,
                    full_access, can_access_admin, long_session,
                    data_scope, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, 0, 0, ?, ?, ?,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """,
                (
                    code,
                    name,
                    description,
                    status,
                    can_access_admin,
                    long_session,
                    data_scope,
                ),
            )
            _replace_permissions(conn, cursor.lastrowid, permission_codes)
            _replace_scope(
                conn,
                cursor.lastrowid,
                store_ids,
                warehouse_ids,
            )
            role = _serialize_role(conn, _role_row(conn, cursor.lastrowid))
        return jsonify(
            {"success": True, "message": "权限组创建成功", "role": role}
        ), 201
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@access_bp.route("/roles/<int:role_id>", methods=["PUT"])
@require_super_admin
def update_role(role_id):
    data = request.get_json(silent=True) or {}
    name = _text(data.get("name"), 80)
    description = _text(data.get("description"), 300)
    status = "disabled" if data.get("status") == "disabled" else "active"
    can_access_admin = 1 if data.get("canAccessAdmin") else 0
    long_session = 1 if data.get("longSession") else 0
    data_scope = _text(data.get("dataScope"), 30) or "all"
    permission_codes = _permission_codes(data.get("permissionCodes"))
    store_ids = _integer_ids(data.get("storeIds"))
    warehouse_ids = _integer_ids(data.get("warehouseIds"))
    if not name:
        return jsonify({"success": False, "message": "权限组名称不能为空"}), 400

    try:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = _role_row(conn, role_id)
            if not existing:
                return jsonify({"success": False, "message": "权限组不存在"}), 404
            if existing["is_system"]:
                return jsonify(
                    {"success": False, "message": "系统内置超级管理员组不可修改"}
                ), 409
            conn.execute(
                """
                UPDATE roles
                SET name = ?, description = ?, status = ?,
                    can_access_admin = ?, long_session = ?, data_scope = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    name,
                    description,
                    status,
                    can_access_admin,
                    long_session,
                    data_scope,
                    role_id,
                ),
            )
            _replace_permissions(conn, role_id, permission_codes)
            _replace_scope(conn, role_id, store_ids, warehouse_ids)
            conn.execute(
                """
                UPDATE users
                SET permission_version = permission_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id IN (
                    SELECT employees.user_id
                    FROM employee_roles
                    INNER JOIN employees
                        ON employees.id = employee_roles.employee_id
                    WHERE employee_roles.role_id = ?
                      AND employees.user_id IS NOT NULL
                )
                """,
                (role_id,),
            )
            affected_user_ids = {
                row["user_id"]
                for row in conn.execute(
                    """
                    SELECT employees.user_id
                    FROM employee_roles
                    INNER JOIN employees
                        ON employees.id = employee_roles.employee_id
                    WHERE employee_roles.role_id = ?
                      AND employees.user_id IS NOT NULL
                    """,
                    (role_id,),
                ).fetchall()
            }
            _refresh_current_session_version(conn, affected_user_ids)
            role = _serialize_role(conn, _role_row(conn, role_id))
        return jsonify({"success": True, "message": "权限组已更新", "role": role})
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@access_bp.route("/roles/<int:role_id>/members", methods=["PUT"])
@require_super_admin
def update_role_members(role_id):
    data = request.get_json(silent=True) or {}
    employee_ids = _integer_ids(data.get("employeeIds"))

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        role = _role_row(conn, role_id)
        if not role:
            return jsonify({"success": False, "message": "权限组不存在"}), 404

        employees = []
        if employee_ids:
            placeholders = ",".join("?" for _ in employee_ids)
            employees = conn.execute(
                f"""
                SELECT id, user_id, display_name, account_status
                FROM employees
                WHERE id IN ({placeholders})
                """,
                employee_ids,
            ).fetchall()
            if len(employees) != len(employee_ids):
                return jsonify(
                    {"success": False, "message": "包含不存在的员工档案"}
                ), 400
        new_employee_ids = {employee["id"] for employee in employees}
        old_employee_ids = {
            row["employee_id"]
            for row in conn.execute(
                "SELECT employee_id FROM employee_roles WHERE role_id = ?",
                (role_id,),
            ).fetchall()
        }

        if role["full_access"] and role["status"] == "active":
            selected_active_count = 0
            if new_employee_ids:
                placeholders = ",".join("?" for _ in new_employee_ids)
                selected_active_count = conn.execute(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM employees
                    INNER JOIN users ON users.id = employees.user_id
                    WHERE employees.id IN ({placeholders})
                      AND users.status = 'active'
                    """,
                    list(new_employee_ids),
                ).fetchone()["total"]
            other_active_count = conn.execute(
                """
                SELECT COUNT(DISTINCT users.id) AS total
                FROM users
                INNER JOIN employees ON employees.user_id = users.id
                INNER JOIN employee_roles
                    ON employee_roles.employee_id = employees.id
                INNER JOIN roles ON roles.id = employee_roles.role_id
                WHERE users.status = 'active'
                  AND roles.status = 'active'
                  AND roles.full_access = 1
                  AND roles.id <> ?
                """,
                (role_id,),
            ).fetchone()["total"]
            if selected_active_count + other_active_count == 0:
                return jsonify(
                    {
                        "success": False,
                        "message": "超级管理员组必须至少保留一名启用账号成员",
                    }
                ), 409

        conn.execute("DELETE FROM employee_roles WHERE role_id = ?", (role_id,))
        for employee_id in new_employee_ids:
            conn.execute(
                """
                INSERT INTO employee_roles (employee_id, role_id)
                VALUES (?, ?)
                """,
                (employee_id, role_id),
            )

        affected_employee_ids = old_employee_ids | new_employee_ids
        affected_user_ids = set()
        if affected_employee_ids:
            placeholders = ",".join("?" for _ in affected_employee_ids)
            affected_user_ids = {
                row["user_id"]
                for row in conn.execute(
                    f"""
                    SELECT user_id
                    FROM employees
                    WHERE id IN ({placeholders})
                      AND user_id IS NOT NULL
                    """,
                    list(affected_employee_ids),
                ).fetchall()
            }
        if affected_user_ids:
            placeholders = ",".join("?" for _ in affected_user_ids)
            conn.execute(
                f"""
                UPDATE users
                SET permission_version = permission_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
                """,
                list(affected_user_ids),
            )
        _refresh_current_session_version(conn, affected_user_ids)
        serialized = _serialize_role(conn, _role_row(conn, role_id))

    return jsonify(
        {
            "success": True,
            "message": "角色组成员已更新",
            "role": serialized,
        }
    )
