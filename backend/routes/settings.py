"""System settings endpoints used by the administrator settings page."""

from flask import Blueprint, jsonify, request

from utils.auth import (
    current_session_id,
    get_current_user,
    require_super_admin,
)
from utils.db import get_db
from utils.system_settings import (
    DEFAULT_BANK_CARD_BG_PATH,
    DEFAULT_BANK_ICON_PATH,
    DEFAULT_DOCUMENT_PATH,
    DEFAULT_RECEIPT_PATH,
    REPORT_PATH_KEY,
    get_browse_roots,
    get_default_report_path,
    get_report_path,
    get_setting,
    inspect_directory,
    list_directories,
    normalize_server_path,
    set_setting,
)


settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


def _save_directory_setting(key, value, default_path, label):
    normalized = normalize_server_path(value or default_path)
    try:
        # 路径配置保存时自动创建目录，之后测试和上传接口都能直接使用。
        import os

        os.makedirs(normalized, exist_ok=True)
    except OSError as error:
        raise ValueError(f"{label}不可用：{error}")
    status = inspect_directory(normalized)
    if not status["is_directory"] or not status["readable"] or not status["writable"]:
        raise ValueError(f"{label}不可用：{status['message']}")
    set_setting(key, normalized)
    return normalized, status


@settings_bp.route("/paths", methods=["GET"])
def get_path_settings():
    configured_report_path = get_setting(REPORT_PATH_KEY, "").strip()
    report_path = get_report_path()
    report_status = inspect_directory(report_path)

    return jsonify(
        {
            "success": True,
            "data": {
                "reportPath": report_path,
                "documentPath": get_setting("documents.path", DEFAULT_DOCUMENT_PATH),
                "receiptPath": get_setting("receipts.path", DEFAULT_RECEIPT_PATH),
                "bankCardBgPath": get_setting(
                    "bank_cards.bg_path", DEFAULT_BANK_CARD_BG_PATH
                ),
                "bankIconPath": get_setting(
                    "bank_cards.icon_path", DEFAULT_BANK_ICON_PATH
                ),
                "reportPathConfigured": bool(configured_report_path),
                "reportPathDefault": get_default_report_path(),
                "reportStatus": report_status,
            },
        }
    )


@settings_bp.route("/paths", methods=["PUT"])
def save_path_settings():
    data = request.get_json(silent=True) or {}
    report_path = normalize_server_path(data.get("reportPath", ""))

    # An empty value explicitly restores the deployment default.
    if report_path:
        report_status = inspect_directory(report_path)
        if not report_status["is_directory"] or not report_status["readable"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"检测报告路径不可用：{report_status['message']}",
                        "data": report_status,
                    }
                ),
                400,
            )
        set_setting(REPORT_PATH_KEY, report_path)
    else:
        set_setting(REPORT_PATH_KEY, "")

    document_path = str(data.get("documentPath", DEFAULT_DOCUMENT_PATH)).strip()
    receipt_path = str(data.get("receiptPath", DEFAULT_RECEIPT_PATH)).strip()
    set_setting("documents.path", document_path)
    set_setting("receipts.path", receipt_path)

    try:
        bank_bg_path, bank_bg_status = _save_directory_setting(
            "bank_cards.bg_path",
            data.get(
                "bankCardBgPath",
                get_setting("bank_cards.bg_path", DEFAULT_BANK_CARD_BG_PATH),
            ),
            DEFAULT_BANK_CARD_BG_PATH,
            "银行卡背景图路径",
        )
        bank_icon_path, bank_icon_status = _save_directory_setting(
            "bank_cards.icon_path",
            data.get(
                "bankIconPath",
                get_setting("bank_cards.icon_path", DEFAULT_BANK_ICON_PATH),
            ),
            DEFAULT_BANK_ICON_PATH,
            "银行图标路径",
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify(
        {
            "success": True,
            "message": "路径配置已保存",
            "data": {
                "reportPath": get_report_path(),
                "documentPath": document_path,
                "receiptPath": receipt_path,
                "bankCardBgPath": bank_bg_path,
                "bankIconPath": bank_icon_path,
                "reportStatus": inspect_directory(get_report_path()),
                "bankCardBgStatus": bank_bg_status,
                "bankIconStatus": bank_icon_status,
            },
        }
    )


@settings_bp.route("/paths/test", methods=["POST"])
def test_path():
    data = request.get_json(silent=True) or {}
    status = inspect_directory(data.get("path", ""))
    return jsonify(
        {
            "success": status["is_directory"] and status["readable"],
            "message": status["message"],
            "data": status,
        }
    )


@settings_bp.route("/directories", methods=["GET"])
def browse_directories():
    path = request.args.get("path")
    data = list_directories(path)
    if not path:
        data["roots"] = get_browse_roots()
    return jsonify({"success": True, "data": data})


@settings_bp.route("/login-devices", methods=["GET"])
@require_super_admin
def get_login_devices():
    active_session_id = current_session_id()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT auth_sessions.id, auth_sessions.device_name,
                   auth_sessions.session_kind, auth_sessions.browser,
                   auth_sessions.operating_system, auth_sessions.timezone,
                   auth_sessions.ip_address, auth_sessions.created_at,
                   auth_sessions.last_seen_at, auth_sessions.expires_at,
                   auth_sessions.revoked_at, users.username, users.display_name,
                   CASE
                       WHEN auth_sessions.revoked_at IS NOT NULL THEN 'revoked'
                       WHEN datetime(auth_sessions.expires_at) <= CURRENT_TIMESTAMP
                           THEN 'expired'
                       ELSE 'active'
                   END AS session_status
            FROM auth_sessions
            INNER JOIN users ON users.id = auth_sessions.user_id
            ORDER BY
                CASE
                    WHEN auth_sessions.revoked_at IS NULL
                         AND datetime(auth_sessions.expires_at) > CURRENT_TIMESTAMP
                    THEN 0
                    ELSE 1
                END,
                auth_sessions.last_seen_at DESC,
                auth_sessions.id DESC
            """
        ).fetchall()

    devices = [
        {
            "id": row["id"],
            "deviceName": row["device_name"],
            "sessionKind": row["session_kind"],
            "browser": row["browser"],
            "operatingSystem": row["operating_system"],
            "timezone": row["timezone"],
            "ipAddress": row["ip_address"],
            "createdAt": row["created_at"],
            "lastSeenAt": row["last_seen_at"],
            "expiresAt": row["expires_at"],
            "revokedAt": row["revoked_at"],
            "status": row["session_status"],
            "username": row["username"],
            "displayName": row["display_name"],
            "currentSession": row["id"] == active_session_id,
        }
        for row in rows
    ]
    return jsonify(
        {
            "success": True,
            "data": devices,
            "activeCount": sum(item["status"] == "active" for item in devices),
        }
    )


@settings_bp.route("/login-devices/<int:session_id>/revoke", methods=["POST"])
@require_super_admin
def revoke_login_device(session_id):
    current_user = get_current_user()
    with get_db() as conn:
        target = conn.execute(
            "SELECT id, revoked_at FROM auth_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not target:
            return jsonify({"success": False, "message": "登录设备记录不存在"}), 404
        conn.execute(
            """
            UPDATE auth_sessions
            SET revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP),
                revoked_by = COALESCE(revoked_by, ?)
            WHERE id = ?
            """,
            (current_user["id"], session_id),
        )
    return jsonify({"success": True, "message": "设备登录已撤销"})


@settings_bp.route("/login-devices/<int:session_id>", methods=["DELETE"])
@require_super_admin
def delete_login_device(session_id):
    with get_db() as conn:
        target = conn.execute(
            "SELECT id FROM auth_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if not target:
            return jsonify({"success": False, "message": "登录设备记录不存在"}), 404
        conn.execute("DELETE FROM auth_sessions WHERE id = ?", (session_id,))
    return jsonify({"success": True, "message": "设备记录已删除"})
