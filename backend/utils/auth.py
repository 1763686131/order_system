"""Session authentication and permission helpers."""

from functools import wraps

from flask import g, jsonify, session

from utils.db import get_db


def _load_roles_and_permissions(conn, user_id):
    roles = [
        dict(row)
        for row in conn.execute(
            """
            SELECT roles.id, roles.code, roles.name, roles.description,
                   roles.full_access, roles.data_scope
            FROM roles
            INNER JOIN employee_roles ON employee_roles.role_id = roles.id
            INNER JOIN employees ON employees.id = employee_roles.employee_id
            WHERE employees.user_id = ? AND roles.status = 'active'
            ORDER BY roles.is_system DESC, roles.id
            """,
            (user_id,),
        ).fetchall()
    ]
    full_access = any(bool(role["full_access"]) for role in roles)
    permissions = []
    if not full_access:
        permissions = [
            row["code"]
            for row in conn.execute(
                """
                SELECT DISTINCT permissions.code
                FROM permissions
                INNER JOIN role_permissions
                    ON role_permissions.permission_id = permissions.id
                INNER JOIN employee_roles
                    ON employee_roles.role_id = role_permissions.role_id
                INNER JOIN employees
                    ON employees.id = employee_roles.employee_id
                INNER JOIN roles ON roles.id = employee_roles.role_id
                WHERE employees.user_id = ? AND roles.status = 'active'
                ORDER BY permissions.sort_order, permissions.id
                """,
                (user_id,),
            ).fetchall()
        ]
    return roles, permissions, full_access


def serialize_user(conn, row):
    roles, permissions, full_access = _load_roles_and_permissions(conn, row["id"])
    role_codes = [role["code"] for role in roles]
    employee = conn.execute(
        """
        SELECT id, employee_no
        FROM employees
        WHERE user_id = ?
        LIMIT 1
        """,
        (row["id"],),
    ).fetchone()
    return {
        "id": row["id"],
        "employeeId": employee["id"] if employee else None,
        "employeeNo": employee["employee_no"] if employee else "",
        "username": row["username"],
        "name": row["display_name"],
        "displayName": row["display_name"],
        "avatarUrl": row["avatar_url"] or "",
        "status": row["status"],
        "mustChangePassword": bool(row["must_change_password"]),
        "lastLoginAt": row["last_login_at"],
        "createdAt": row["created_at"],
        "roleIds": [role["id"] for role in roles],
        "roles": roles,
        "role": "super_admin" if "super_admin" in role_codes else (
            role_codes[0] if role_codes else "user"
        ),
        "permissions": permissions,
        "isSuperAdmin": full_access,
        "canAccessAdmin": full_access,
    }


def get_current_user():
    if hasattr(g, "current_user"):
        return g.current_user

    user_id = session.get("user_id")
    if not user_id:
        g.current_user = None
        return None

    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id, username, display_name, avatar_url, status,
                   must_change_password, last_login_at, permission_version,
                   created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        if (
            not row
            or row["status"] != "active"
            or int(row["permission_version"] or 0)
            != int(session.get("permission_version") or 0)
        ):
            session.clear()
            g.current_user = None
            return None
        g.current_user = serialize_user(conn, row)
        return g.current_user


def login_session(user_row):
    session.clear()
    session.permanent = True
    session["user_id"] = user_row["id"]
    session["permission_version"] = int(user_row["permission_version"] or 1)


def current_identity(default="系统用户"):
    user = get_current_user()
    if not user:
        return default
    return user.get("displayName") or user.get("username") or default


def permission_granted(permission_code):
    user = get_current_user()
    if not user:
        return False
    return bool(
        user.get("isSuperAdmin")
        or permission_code in set(user.get("permissions") or [])
    )


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            return jsonify({"success": False, "message": "请先登录"}), 401
        return view(*args, **kwargs)

    return wrapped


def require_super_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "message": "请先登录"}), 401
        if not user.get("isSuperAdmin"):
            return jsonify({"success": False, "message": "仅超级管理员可操作"}), 403
        return view(*args, **kwargs)

    return wrapped


def require_permission(permission_code):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"success": False, "message": "请先登录"}), 401
            if not permission_granted(permission_code):
                return jsonify(
                    {
                        "success": False,
                        "message": "当前账号没有执行此操作的权限",
                        "permission": permission_code,
                    }
                ), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator
