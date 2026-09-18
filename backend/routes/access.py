"""Super-admin role and permission management APIs."""

import re

from flask import Blueprint, jsonify, request

from utils.auth import require_super_admin
from utils.db import get_db
from utils.permission_catalog import PERMISSION_MODULES


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


def _serialize_role(conn, row):
    permission_codes = [
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
    member_count = conn.execute(
        "SELECT COUNT(*) AS total FROM user_roles WHERE role_id = ?",
        (row["id"],),
    ).fetchone()["total"]
    return {
        "id": row["id"],
        "code": row["code"],
        "name": row["name"],
        "description": row["description"],
        "status": row["status"],
        "isSystem": bool(row["is_system"]),
        "fullAccess": bool(row["full_access"]),
        "dataScope": row["data_scope"],
        "permissionCodes": permission_codes,
        "memberCount": member_count,
        "createdAt": row["created_at"],
    }


def _role_row(conn, role_id):
    return conn.execute(
        """
        SELECT id, code, name, description, status, is_system,
               full_access, data_scope, created_at
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
                   full_access, data_scope, created_at
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
    data_scope = _text(data.get("dataScope"), 30) or "all"
    permission_codes = _permission_codes(data.get("permissionCodes"))
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
                    full_access, data_scope, created_at, updated_at
                ) VALUES (?, ?, ?, 'active', 0, 0, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (code, name, description, data_scope),
            )
            _replace_permissions(conn, cursor.lastrowid, permission_codes)
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
    data_scope = _text(data.get("dataScope"), 30) or "all"
    permission_codes = _permission_codes(data.get("permissionCodes"))
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
                SET name = ?, description = ?, status = ?, data_scope = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, description, status, data_scope, role_id),
            )
            _replace_permissions(conn, role_id, permission_codes)
            conn.execute(
                """
                UPDATE users
                SET permission_version = permission_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id IN (
                    SELECT user_id FROM user_roles WHERE role_id = ?
                )
                """,
                (role_id,),
            )
            role = _serialize_role(conn, _role_row(conn, role_id))
        return jsonify({"success": True, "message": "权限组已更新", "role": role})
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
