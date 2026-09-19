"""Super-admin account management APIs."""

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash

from utils.auth import get_current_user, require_super_admin, serialize_user
from utils.avatar_storage import normalize_avatar_url
from utils.db import get_db
from utils.employee_links import ensure_employee_for_user, sync_employee_from_user


users_bp = Blueprint("users", __name__, url_prefix="/api/admin/users")


def _text(value, max_length):
    return str(value or "").strip()[:max_length]


def _normalize_role_ids(value):
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        try:
            role_id = int(item)
        except (TypeError, ValueError):
            continue
        if role_id not in result:
            result.append(role_id)
    return result


def _validate_roles(conn, role_ids):
    if not role_ids:
        return []
    placeholders = ",".join("?" for _ in role_ids)
    rows = conn.execute(
        f"""
        SELECT id FROM roles
        WHERE id IN ({placeholders}) AND status = 'active'
        """,
        role_ids,
    ).fetchall()
    valid_ids = [row["id"] for row in rows]
    if len(valid_ids) != len(role_ids):
        raise ValueError("包含不存在或已停用的权限组")
    return valid_ids


def _active_super_admin_count(conn):
    return conn.execute(
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
        """
    ).fetchone()["total"]


def _is_active_super_admin(conn, user_id):
    return bool(
        conn.execute(
            """
            SELECT 1
            FROM users
            INNER JOIN employees ON employees.user_id = users.id
            INNER JOIN employee_roles
                ON employee_roles.employee_id = employees.id
            INNER JOIN roles ON roles.id = employee_roles.role_id
            WHERE users.id = ?
              AND users.status = 'active'
              AND roles.status = 'active'
              AND roles.full_access = 1
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    )


def _roles_include_full_access(conn, role_ids):
    if not role_ids:
        return False
    placeholders = ",".join("?" for _ in role_ids)
    return bool(
        conn.execute(
            f"""
            SELECT 1 FROM roles
            WHERE id IN ({placeholders})
              AND status = 'active'
              AND full_access = 1
            LIMIT 1
            """,
            role_ids,
        ).fetchone()
    )


def _user_row(conn, user_id):
    return conn.execute(
        """
        SELECT id, username, display_name, avatar_url, status,
               must_change_password, last_login_at, permission_version,
               created_at
        FROM users WHERE id = ?
        """,
        (user_id,),
    ).fetchone()


@users_bp.route("", methods=["GET"])
@require_super_admin
def list_users():
    keyword = _text(request.args.get("keyword"), 80)
    with get_db() as conn:
        sql = """
            SELECT id, username, display_name, avatar_url, status,
                   must_change_password, last_login_at, permission_version,
                   created_at
            FROM users
        """
        params = []
        if keyword:
            sql += " WHERE username LIKE ? OR display_name LIKE ?"
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern])
        sql += " ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END, id"
        rows = conn.execute(sql, params).fetchall()
        users = [serialize_user(conn, row) for row in rows]
    return jsonify({"success": True, "users": users})


@users_bp.route("", methods=["POST"])
@require_super_admin
def create_user():
    data = request.get_json(silent=True) or {}
    username = _text(data.get("username"), 50)
    display_name = _text(data.get("displayName") or data.get("name"), 80)
    password = str(data.get("password") or "")
    status = "disabled" if data.get("status") == "disabled" else "active"
    role_ids = _normalize_role_ids(data.get("roleIds"))
    if not username or any(char.isspace() for char in username):
        return jsonify({"success": False, "message": "登录账号不能为空或包含空格"}), 400
    if not display_name:
        return jsonify({"success": False, "message": "请输入显示姓名"}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "初始密码至少需要 8 位"}), 400

    try:
        avatar_url = normalize_avatar_url(data.get("avatarUrl"))
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute(
                "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone():
                return jsonify({"success": False, "message": "登录账号已存在"}), 409
            role_ids = _validate_roles(conn, role_ids)
            cursor = conn.execute(
                """
                INSERT INTO users (
                    username, password_hash, display_name, name,
                    avatar_url, status, must_change_password,
                    permission_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    username,
                    generate_password_hash(password),
                    display_name,
                    display_name,
                    avatar_url,
                    status,
                ),
            )
            employee_id = ensure_employee_for_user(
                conn,
                cursor.lastrowid,
                display_name,
                avatar_url,
                status,
            )
            for role_id in role_ids:
                conn.execute(
                    """
                    INSERT INTO employee_roles (employee_id, role_id)
                    VALUES (?, ?)
                    """,
                    (employee_id, role_id),
                )
            user = serialize_user(conn, _user_row(conn, cursor.lastrowid))
        return jsonify(
            {"success": True, "message": "账号创建成功", "user": user}
        ), 201
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@users_bp.route("/<int:user_id>", methods=["PUT"])
@require_super_admin
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    display_name = _text(data.get("displayName") or data.get("name"), 80)
    status = "disabled" if data.get("status") == "disabled" else "active"
    role_ids = _normalize_role_ids(data.get("roleIds"))
    if not display_name:
        return jsonify({"success": False, "message": "显示姓名不能为空"}), 400

    try:
        avatar_url = normalize_avatar_url(data.get("avatarUrl"))
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = _user_row(conn, user_id)
            if not existing:
                return jsonify({"success": False, "message": "账号不存在"}), 404
            role_ids = _validate_roles(conn, role_ids)
            loses_super_access = (
                status != "active"
                or not _roles_include_full_access(conn, role_ids)
            )
            if (
                _is_active_super_admin(conn, user_id)
                and loses_super_access
                and _active_super_admin_count(conn) <= 1
            ):
                return jsonify(
                    {"success": False, "message": "不能停用或移除最后一个超级管理员"}
                ), 409

            conn.execute(
                """
                UPDATE users
                SET display_name = ?, name = ?, avatar_url = ?, status = ?,
                    permission_version = permission_version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (display_name, display_name, avatar_url, status, user_id),
            )
            employee_id = sync_employee_from_user(
                conn,
                user_id,
                display_name,
                avatar_url,
                status,
            )
            conn.execute(
                "DELETE FROM employee_roles WHERE employee_id = ?",
                (employee_id,),
            )
            for role_id in role_ids:
                conn.execute(
                    """
                    INSERT INTO employee_roles (employee_id, role_id)
                    VALUES (?, ?)
                    """,
                    (employee_id, role_id),
                )
            updated_row = _user_row(conn, user_id)
            user = serialize_user(conn, updated_row)
            current_user = get_current_user()
            if current_user and current_user["id"] == user_id:
                session["permission_version"] = updated_row["permission_version"]
        return jsonify({"success": True, "message": "账号信息已更新", "user": user})
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@users_bp.route("/<int:user_id>/password", methods=["PUT"])
@require_super_admin
def reset_user_password(user_id):
    data = request.get_json(silent=True) or {}
    password = str(data.get("password") or "")
    if len(password) < 8:
        return jsonify({"success": False, "message": "新密码至少需要 8 位"}), 400

    with get_db() as conn:
        existing = _user_row(conn, user_id)
        if not existing:
            return jsonify({"success": False, "message": "账号不存在"}), 404
        next_version = int(existing["permission_version"] or 1) + 1
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, must_change_password = 1,
                permission_version = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (generate_password_hash(password), next_version, user_id),
        )
        current_user = get_current_user()
        if current_user and current_user["id"] == user_id:
            session["permission_version"] = next_version
    return jsonify({"success": True, "message": "密码已重置"})
