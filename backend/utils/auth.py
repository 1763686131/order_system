"""Session authentication and permission helpers."""

from datetime import datetime, timedelta, timezone
from functools import wraps
import hashlib
import os
import secrets

from flask import g, jsonify, request, session

from utils.db import get_db


SESSION_TOKEN_KEY = "auth_session_token"
STANDARD_SESSION_DAYS = 7
LONG_SESSION_DAYS = 365
SESSION_TOUCH_INTERVAL_MINUTES = 5


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _format_db_datetime(value):
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _session_token_hash(token):
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def _safe_text(value, max_length):
    return str(value or "").strip()[:max_length]


def _client_ip():
    if os.environ.get("TRUST_PROXY_HEADERS", "0") == "1":
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return _safe_text(forwarded.split(",", 1)[0], 64)
    return _safe_text(request.remote_addr, 64)


def _parse_user_agent(user_agent):
    value = str(user_agent or "")
    if "Edg/" in value:
        browser = "Microsoft Edge"
    elif "Chrome/" in value and "Chromium/" not in value:
        browser = "Chrome"
    elif "Firefox/" in value:
        browser = "Firefox"
    elif "Safari/" in value and "Chrome/" not in value:
        browser = "Safari"
    elif "Chromium/" in value:
        browser = "Chromium"
    else:
        browser = "浏览器"

    if "Windows" in value:
        operating_system = "Windows"
    elif "Android" in value:
        operating_system = "Android"
    elif "iPhone" in value or "iPad" in value:
        operating_system = "iOS"
    elif "Mac OS X" in value:
        operating_system = "macOS"
    elif "Linux" in value:
        operating_system = "Linux"
    else:
        operating_system = "未知系统"
    return browser, operating_system


def current_session_id():
    return getattr(g, "current_auth_session_id", None)


def revoke_current_session(conn, revoked_by=None):
    token = session.get(SESSION_TOKEN_KEY)
    if not token:
        return
    conn.execute(
        """
        UPDATE auth_sessions
        SET revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP),
            revoked_by = COALESCE(revoked_by, ?)
        WHERE session_token_hash = ?
        """,
        (revoked_by, _session_token_hash(token)),
    )


def _load_roles_and_permissions(conn, user_id):
    roles = [
        dict(row)
        for row in conn.execute(
            """
            SELECT roles.id, roles.code, roles.name, roles.description,
                   roles.full_access, roles.can_access_admin,
                   roles.long_session, roles.data_scope
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
    can_access_admin = full_access or any(
        bool(role["can_access_admin"]) for role in roles
    )
    long_session = any(bool(role["long_session"]) for role in roles)
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
    return roles, permissions, full_access, can_access_admin, long_session


def serialize_user(conn, row):
    (
        roles,
        permissions,
        full_access,
        can_access_admin,
        long_session,
    ) = _load_roles_and_permissions(conn, row["id"])
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
        "canAccessAdmin": can_access_admin,
        "longSession": long_session,
    }


def get_current_user():
    if hasattr(g, "current_user"):
        return g.current_user

    user_id = session.get("user_id")
    session_token = session.get(SESSION_TOKEN_KEY)
    if not user_id or not session_token:
        g.current_user = None
        return None

    with get_db() as conn:
        now = _utc_now()
        session_row = conn.execute(
            """
            SELECT id, user_id, session_kind, last_seen_at, expires_at, revoked_at
            FROM auth_sessions
            WHERE session_token_hash = ?
            LIMIT 1
            """,
            (_session_token_hash(session_token),),
        ).fetchone()
        if (
            not session_row
            or int(session_row["user_id"]) != int(user_id)
            or session_row["revoked_at"]
            or session_row["expires_at"] <= _format_db_datetime(now)
        ):
            session.clear()
            g.current_user = None
            return None

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
        last_seen = datetime.strptime(
            session_row["last_seen_at"],
            "%Y-%m-%d %H:%M:%S",
        )
        current_user = serialize_user(conn, row)
        if now - last_seen >= timedelta(minutes=SESSION_TOUCH_INTERVAL_MINUTES):
            duration = (
                LONG_SESSION_DAYS
                if current_user.get("longSession")
                else STANDARD_SESSION_DAYS
            )
            session_kind = (
                "admin" if current_user.get("canAccessAdmin") else "touch"
            )
            conn.execute(
                """
                UPDATE auth_sessions
                SET session_kind = ?, last_seen_at = ?,
                    expires_at = ?, ip_address = ?
                WHERE id = ?
                """,
                (
                    session_kind,
                    _format_db_datetime(now),
                    _format_db_datetime(now + timedelta(days=duration)),
                    _client_ip(),
                    session_row["id"],
                ),
            )
        g.current_auth_session_id = session_row["id"]
        g.current_user = current_user
        return g.current_user


def login_session(conn, user_row, user, device=None):
    device = device if isinstance(device, dict) else {}
    token = secrets.token_urlsafe(32)
    now = _utc_now()
    session_kind = "admin" if user.get("canAccessAdmin") else "touch"
    duration = (
        LONG_SESSION_DAYS
        if user.get("longSession")
        else STANDARD_SESSION_DAYS
    )
    user_agent = _safe_text(request.headers.get("User-Agent"), 500)
    browser, operating_system = _parse_user_agent(user_agent)
    device_name = _safe_text(device.get("name"), 100)
    if not device_name:
        device_name = f"{operating_system} · {browser}"

    session.clear()
    session.permanent = True
    session["user_id"] = user_row["id"]
    session["permission_version"] = int(user_row["permission_version"] or 1)
    session[SESSION_TOKEN_KEY] = token
    cursor = conn.execute(
        """
        INSERT INTO auth_sessions (
            session_token_hash, user_id, device_id, device_name,
            session_kind, browser, operating_system, timezone,
            user_agent, ip_address, created_at, last_seen_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _session_token_hash(token),
            user_row["id"],
            _safe_text(device.get("id"), 100),
            device_name,
            session_kind,
            browser,
            operating_system,
            _safe_text(device.get("timezone"), 80),
            user_agent,
            _client_ip(),
            _format_db_datetime(now),
            _format_db_datetime(now),
            _format_db_datetime(now + timedelta(days=duration)),
        ),
    )
    g.current_auth_session_id = cursor.lastrowid


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
