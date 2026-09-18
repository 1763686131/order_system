"""Public authentication and current-account APIs."""

from datetime import datetime

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from utils.auth import get_current_user, login_session, require_login, serialize_user
from utils.db import get_db
from utils.employee_links import ensure_employee_for_user, sync_employee_from_user


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _text(value, max_length):
    return str(value or "").strip()[:max_length]


def _validate_credentials(data, require_name=False):
    username = _text(data.get("username"), 50)
    password = str(data.get("password") or "")
    display_name = _text(data.get("displayName") or data.get("name"), 80)
    if not username:
        raise ValueError("请输入登录账号")
    if len(password) < 8:
        raise ValueError("密码至少需要 8 位")
    if require_name and not display_name:
        raise ValueError("请输入管理员姓名")
    return username, password, display_name


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


@auth_bp.route("/bootstrap-status", methods=["GET"])
def bootstrap_status():
    with get_db() as conn:
        setup_required = _active_super_admin_count(conn) == 0
    return jsonify(
        {
            "success": True,
            "setupRequired": setup_required,
            "reason": "missing_super_admin" if setup_required else "ready",
        }
    )


@auth_bp.route("/bootstrap", methods=["POST"])
def bootstrap():
    data = request.get_json(silent=True) or {}
    try:
        username, password, display_name = _validate_credentials(
            data,
            require_name=True,
        )
        if password != str(data.get("confirmPassword") or ""):
            raise ValueError("两次输入的密码不一致")

        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if _active_super_admin_count(conn) > 0:
                return jsonify(
                    {"success": False, "message": "系统已经存在超级管理员"}
                ), 409
            duplicate = conn.execute(
                "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()
            if duplicate:
                return jsonify(
                    {"success": False, "message": "该登录账号已存在，请更换账号"}
                ), 409
            role = conn.execute(
                """
                SELECT id FROM roles
                WHERE code = 'super_admin' AND status = 'active'
                LIMIT 1
                """
            ).fetchone()
            if not role:
                return jsonify(
                    {"success": False, "message": "超级管理员权限组未初始化"}
                ), 500

            cursor = conn.execute(
                """
                INSERT INTO users (
                    username, password_hash, display_name, name,
                    avatar_url, status, must_change_password,
                    permission_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, '', 'active', 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    username,
                    generate_password_hash(password),
                    display_name,
                    display_name,
                ),
            )
            employee_id = ensure_employee_for_user(
                conn,
                cursor.lastrowid,
                display_name,
                account_status="active",
            )
            conn.execute(
                """
                INSERT INTO employee_roles (employee_id, role_id)
                VALUES (?, ?)
                """,
                (employee_id, role["id"]),
            )
            conn.execute(
                """
                INSERT INTO system_meta (setting_key, setting_value, updated_at)
                VALUES ('auth_bootstrap_completed', '1', CURRENT_TIMESTAMP)
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value = '1',
                    updated_at = CURRENT_TIMESTAMP
                """
            )

        return jsonify(
            {
                "success": True,
                "message": "超级管理员创建成功，请使用新账号登录",
            }
        ), 201
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = _text(data.get("username"), 50)
    password = str(data.get("password") or "")
    if not username or not password:
        return jsonify({"success": False, "message": "请输入账号和密码"}), 400

    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id, username, password_hash, display_name, avatar_url,
                   status, must_change_password, last_login_at,
                   permission_version, created_at
            FROM users
            WHERE username = ? COLLATE NOCASE
            LIMIT 1
            """,
            (username,),
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            return jsonify({"success": False, "message": "账号或密码错误"}), 401
        if row["status"] != "active":
            return jsonify({"success": False, "message": "该账号已停用"}), 403

        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (now, now, row["id"]),
        )
        refreshed = conn.execute(
            """
            SELECT id, username, display_name, avatar_url, status,
                   must_change_password, last_login_at, permission_version,
                   created_at
            FROM users WHERE id = ?
            """,
            (row["id"],),
        ).fetchone()
        login_session(refreshed)
        user = serialize_user(conn, refreshed)

    return jsonify({"success": True, "user": user})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@auth_bp.route("/me", methods=["GET"])
@require_login
def current_account():
    return jsonify({"success": True, "user": get_current_user()})


@auth_bp.route("/profile", methods=["PUT"])
@require_login
def update_profile():
    data = request.get_json(silent=True) or {}
    display_name = _text(data.get("displayName") or data.get("name"), 80)
    avatar_url = _text(data.get("avatarUrl"), 500)
    if not display_name:
        return jsonify({"success": False, "message": "显示姓名不能为空"}), 400

    current_user = get_current_user()
    with get_db() as conn:
        conn.execute(
            """
            UPDATE users
            SET display_name = ?, name = ?, avatar_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (display_name, display_name, avatar_url, current_user["id"]),
        )
        sync_employee_from_user(
            conn,
            current_user["id"],
            display_name,
            avatar_url,
            account_status="active",
        )
        row = conn.execute(
            """
            SELECT id, username, display_name, avatar_url, status,
                   must_change_password, last_login_at, permission_version,
                   created_at
            FROM users WHERE id = ?
            """,
            (current_user["id"],),
        ).fetchone()
        user = serialize_user(conn, row)
    return jsonify({"success": True, "message": "资料已更新", "user": user})


@auth_bp.route("/password", methods=["PUT"])
@require_login
def update_password():
    data = request.get_json(silent=True) or {}
    current_password = str(data.get("currentPassword") or "")
    new_password = str(data.get("newPassword") or "")
    confirm_password = str(data.get("confirmPassword") or "")
    if len(new_password) < 8:
        return jsonify({"success": False, "message": "新密码至少需要 8 位"}), 400
    if new_password != confirm_password:
        return jsonify({"success": False, "message": "两次输入的新密码不一致"}), 400

    current_user = get_current_user()
    with get_db() as conn:
        row = conn.execute(
            "SELECT password_hash, permission_version FROM users WHERE id = ?",
            (current_user["id"],),
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], current_password):
            return jsonify({"success": False, "message": "当前密码错误"}), 400
        next_version = int(row["permission_version"] or 1) + 1
        conn.execute(
            """
            UPDATE users
            SET password_hash = ?, must_change_password = 0,
                permission_version = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                generate_password_hash(new_password),
                next_version,
                current_user["id"],
            ),
        )
        session["permission_version"] = next_version
    return jsonify({"success": True, "message": "密码修改成功"})
