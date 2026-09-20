"""Authenticated WebRTC signaling for LAN peer-to-peer file transfers."""

import json
import uuid

from flask import Blueprint, jsonify, request

from utils.auth import get_current_user, require_admin_permission
from utils.db import get_db
from utils.permission_catalog import ADMIN_MESSAGE_PERMISSIONS


peer_transfers_bp = Blueprint(
    "peer_transfers",
    __name__,
    url_prefix="/api/admin/peer-transfers",
)

OFFER_TTL_MINUTES = 5
ACTIVE_TTL_HOURS = 24
MAX_SDP_LENGTH = 256 * 1024
MAX_SAFE_FILE_SIZE = 9007199254740991
TERMINAL_STATUSES = {"completed", "rejected", "cancelled", "failed", "expired"}


def _employee_id():
    return int((get_current_user() or {}).get("employeeId") or 0)


def _safe_file_name(value):
    name = str(value or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    name = "".join(character for character in name if ord(character) >= 32)
    return name[:255] or "file"


def _session_description(value, expected_type):
    if not isinstance(value, dict) or value.get("type") != expected_type:
        raise ValueError("连接协商数据无效")
    sdp = str(value.get("sdp") or "")
    if not sdp or len(sdp) > MAX_SDP_LENGTH:
        raise ValueError("连接协商数据无效或过大")
    return json.dumps(
        {"type": expected_type, "sdp": sdp},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _parse_description(value):
    try:
        return json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}


def _expire_stale(conn):
    conn.execute(
        """
        UPDATE peer_file_transfers
        SET status = 'expired', revision = revision + 1,
            offer_sdp = '', answer_sdp = '', updated_at = CURRENT_TIMESTAMP
        WHERE status IN ('offered', 'accepted', 'transferring')
          AND datetime(expires_at) <= CURRENT_TIMESTAMP
        """
    )
    conn.execute(
        """
        DELETE FROM peer_file_transfers
        WHERE status IN ('completed', 'rejected', 'cancelled', 'failed', 'expired')
          AND datetime(updated_at) < datetime(CURRENT_TIMESTAMP, '-7 days')
        """
    )


def _contact(conn, employee_id):
    return conn.execute(
        """
        SELECT employees.id, employees.display_name, employees.avatar_url,
               employees.phone, employees.position
        FROM employees
        WHERE employees.id = ?
        """,
        (employee_id,),
    ).fetchone()


def _serialize(conn, row, employee_id):
    item = dict(row)
    is_sender = item["sender_employee_id"] == employee_id
    peer_id = item["recipient_employee_id"] if is_sender else item["sender_employee_id"]
    peer = _contact(conn, peer_id)
    result = {
        "id": item["id"],
        "direction": "outgoing" if is_sender else "incoming",
        "senderEmployeeId": item["sender_employee_id"],
        "recipientEmployeeId": item["recipient_employee_id"],
        "fileName": item["file_name"],
        "fileSize": item["file_size"],
        "mimeType": item["mime_type"],
        "status": item["status"],
        "failureReason": item["failure_reason"],
        "createdAt": item["created_at"],
        "updatedAt": item["updated_at"],
        "expiresAt": item["expires_at"],
        "peer": {
            "id": peer["id"] if peer else peer_id,
            "displayName": peer["display_name"] if peer else "员工",
            "avatarUrl": (peer["avatar_url"] or "") if peer else "",
            "phone": (peer["phone"] or "") if peer else "",
            "position": (peer["position"] or "") if peer else "",
            "online": item["status"] in {"offered", "accepted", "transferring"},
        },
    }
    if not is_sender and item["status"] == "offered":
        result["offer"] = _parse_description(item["offer_sdp"])
    if is_sender and item["status"] in {"accepted", "transferring"}:
        result["answer"] = _parse_description(item["answer_sdp"])
    return result


def _find_transfer(conn, transfer_id, employee_id):
    return conn.execute(
        """
        SELECT * FROM peer_file_transfers
        WHERE id = ? AND (sender_employee_id = ? OR recipient_employee_id = ?)
        """,
        (transfer_id, employee_id, employee_id),
    ).fetchone()


def _recipient_is_online(conn, recipient_id):
    return conn.execute(
        """
        SELECT employees.id
        FROM employees
        INNER JOIN users ON users.id = employees.user_id
        WHERE employees.id = ?
          AND employees.account_status = 'active'
          AND employees.employment_status IN ('active', 'probation')
          AND users.status = 'active'
          AND EXISTS (
              SELECT 1
              FROM employee_roles
              INNER JOIN roles ON roles.id = employee_roles.role_id
              LEFT JOIN role_permissions ON role_permissions.role_id = roles.id
              LEFT JOIN permissions ON permissions.id = role_permissions.permission_id
              WHERE employee_roles.employee_id = employees.id
                AND roles.status = 'active'
                AND (
                    roles.full_access = 1
                    OR permissions.code = ?
                )
          )
          AND EXISTS (
              SELECT 1 FROM auth_sessions
              WHERE auth_sessions.user_id = users.id
                AND auth_sessions.session_kind = 'admin'
                AND auth_sessions.revoked_at IS NULL
                AND datetime(auth_sessions.expires_at) > CURRENT_TIMESTAMP
                AND datetime(auth_sessions.last_seen_at) >=
                    datetime(CURRENT_TIMESTAMP, '-2 minutes')
          )
        """,
        (recipient_id, ADMIN_MESSAGE_PERMISSIONS["attachment"]),
    ).fetchone()


def _conversation_id(conn, first_id, second_id):
    employee_a_id, employee_b_id = sorted((first_id, second_id))
    conn.execute(
        """
        INSERT OR IGNORE INTO chat_conversations (employee_a_id, employee_b_id)
        VALUES (?, ?)
        """,
        (employee_a_id, employee_b_id),
    )
    return conn.execute(
        """
        SELECT id FROM chat_conversations
        WHERE employee_a_id = ? AND employee_b_id = ?
        """,
        (employee_a_id, employee_b_id),
    ).fetchone()["id"]


def _file_size_text(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    return f"{size / 1024 / 1024 / 1024:.2f} GB"


@peer_transfers_bp.route("", methods=["POST"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["attachment"])
def create_transfer():
    employee_id = _employee_id()
    data = request.get_json(silent=True) or {}
    try:
        recipient_id = int(data.get("recipientEmployeeId"))
        file_size = int(data.get("fileSize"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "收件人或文件大小无效"}), 400
    if recipient_id == employee_id:
        return jsonify({"success": False, "message": "不能给自己发送文件"}), 400
    if file_size <= 0 or file_size > MAX_SAFE_FILE_SIZE:
        return jsonify({"success": False, "message": "文件大小无效"}), 400
    try:
        offer_sdp = _session_description(data.get("offer"), "offer")
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    transfer_id = uuid.uuid4().hex
    with get_db() as conn:
        _expire_stale(conn)
        if not _recipient_is_online(conn, recipient_id):
            return jsonify(
                {
                    "success": False,
                    "message": "对方当前不在线或没有附件权限，请改用10MB以内的服务器附件",
                }
            ), 409
        conn.execute(
            """
            INSERT INTO peer_file_transfers (
                id, sender_employee_id, recipient_employee_id,
                file_name, file_size, mime_type, offer_sdp, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(CURRENT_TIMESTAMP, ?))
            """,
            (
                transfer_id,
                employee_id,
                recipient_id,
                _safe_file_name(data.get("fileName")),
                file_size,
                str(data.get("mimeType") or "application/octet-stream")[:150],
                offer_sdp,
                f"+{OFFER_TTL_MINUTES} minutes",
            ),
        )
        row = _find_transfer(conn, transfer_id, employee_id)
        transfer = _serialize(conn, row, employee_id)
    return jsonify({"success": True, "transfer": transfer}), 201


@peer_transfers_bp.route("/pending", methods=["GET"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["attachment"])
def pending_transfers():
    employee_id = _employee_id()
    with get_db() as conn:
        _expire_stale(conn)
        rows = conn.execute(
            """
            SELECT * FROM peer_file_transfers
            WHERE recipient_employee_id = ? AND status = 'offered'
              AND datetime(expires_at) > CURRENT_TIMESTAMP
            ORDER BY datetime(created_at), id
            LIMIT 10
            """,
            (employee_id,),
        ).fetchall()
        transfers = [_serialize(conn, row, employee_id) for row in rows]
    return jsonify({"success": True, "transfers": transfers})


@peer_transfers_bp.route("/<transfer_id>", methods=["GET"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["attachment"])
def get_transfer(transfer_id):
    employee_id = _employee_id()
    with get_db() as conn:
        _expire_stale(conn)
        row = _find_transfer(conn, transfer_id, employee_id)
        if not row:
            return jsonify({"success": False, "message": "传输请求不存在"}), 404
        transfer = _serialize(conn, row, employee_id)
    return jsonify({"success": True, "transfer": transfer})


@peer_transfers_bp.route("/<transfer_id>/respond", methods=["POST"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["attachment"])
def respond_to_transfer(transfer_id):
    employee_id = _employee_id()
    data = request.get_json(silent=True) or {}
    accepted = data.get("accepted")
    if not isinstance(accepted, bool):
        return jsonify({"success": False, "message": "accepted 必须是布尔值"}), 400
    with get_db() as conn:
        _expire_stale(conn)
        row = _find_transfer(conn, transfer_id, employee_id)
        if not row or row["recipient_employee_id"] != employee_id:
            return jsonify({"success": False, "message": "传输请求不存在"}), 404
        if row["status"] != "offered":
            return jsonify({"success": False, "message": "传输请求已处理或已过期"}), 409
        if not accepted:
            conn.execute(
                """
                UPDATE peer_file_transfers
                SET status = 'rejected', revision = revision + 1,
                    offer_sdp = '', answer_sdp = '', responded_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (transfer_id,),
            )
        else:
            try:
                answer_sdp = _session_description(data.get("answer"), "answer")
            except ValueError as error:
                return jsonify({"success": False, "message": str(error)}), 400
            conn.execute(
                """
                UPDATE peer_file_transfers
                SET status = 'accepted', revision = revision + 1,
                    answer_sdp = ?, responded_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP,
                    expires_at = datetime(CURRENT_TIMESTAMP, ?)
                WHERE id = ?
                """,
                (answer_sdp, f"+{ACTIVE_TTL_HOURS} hours", transfer_id),
            )
        updated = _find_transfer(conn, transfer_id, employee_id)
        transfer = _serialize(conn, updated, employee_id)
    return jsonify({"success": True, "transfer": transfer})


@peer_transfers_bp.route("/<transfer_id>/status", methods=["POST"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["attachment"])
def update_transfer_status(transfer_id):
    employee_id = _employee_id()
    data = request.get_json(silent=True) or {}
    next_status = str(data.get("status") or "").strip()
    if next_status not in {"transferring", "completed", "cancelled", "failed"}:
        return jsonify({"success": False, "message": "传输状态无效"}), 400

    with get_db() as conn:
        _expire_stale(conn)
        row = _find_transfer(conn, transfer_id, employee_id)
        if not row:
            return jsonify({"success": False, "message": "传输请求不存在"}), 404
        current_status = row["status"]
        if current_status in TERMINAL_STATUSES:
            if current_status == next_status:
                return jsonify({"success": True, "transfer": _serialize(conn, row, employee_id)})
            return jsonify({"success": False, "message": "传输已经结束"}), 409

        allowed = (
            next_status in {"cancelled", "failed"}
            or (
                next_status == "transferring"
                and employee_id == row["sender_employee_id"]
                and current_status == "accepted"
            )
            or (
                next_status == "completed"
                and employee_id == row["recipient_employee_id"]
                and current_status in {"accepted", "transferring"}
            )
        )
        if not allowed:
            return jsonify({"success": False, "message": "当前状态不能执行此操作"}), 409

        failure_reason = str(data.get("reason") or "").strip()[:200]
        completed_at = "CURRENT_TIMESTAMP" if next_status == "completed" else "completed_at"
        clear_sdp = next_status in {"completed", "cancelled", "failed"}
        conn.execute(
            f"""
            UPDATE peer_file_transfers
            SET status = ?, revision = revision + 1, failure_reason = ?,
                updated_at = CURRENT_TIMESTAMP, completed_at = {completed_at},
                offer_sdp = CASE WHEN ? THEN '' ELSE offer_sdp END,
                answer_sdp = CASE WHEN ? THEN '' ELSE answer_sdp END
            WHERE id = ?
            """,
            (next_status, failure_reason, clear_sdp, clear_sdp, transfer_id),
        )

        if next_status == "completed" and not row["completion_message_id"]:
            conversation_id = _conversation_id(
                conn, row["sender_employee_id"], row["recipient_employee_id"]
            )
            message_text = (
                f"[在线直传文件] {row['file_name']} "
                f"({_file_size_text(row['file_size'])}，文件未保存在服务器)"
            )
            cursor = conn.execute(
                """
                INSERT INTO chat_messages (
                    conversation_id, sender_employee_id, recipient_employee_id,
                    message_type, content
                ) VALUES (?, ?, ?, 'text', ?)
                """,
                (
                    conversation_id,
                    row["sender_employee_id"],
                    row["recipient_employee_id"],
                    message_text,
                ),
            )
            conn.execute(
                """
                UPDATE chat_conversations
                SET last_message_id = ?, last_message_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (cursor.lastrowid, conversation_id),
            )
            conn.execute(
                """
                UPDATE peer_file_transfers SET completion_message_id = ? WHERE id = ?
                """,
                (cursor.lastrowid, transfer_id),
            )

        updated = _find_transfer(conn, transfer_id, employee_id)
        transfer = _serialize(conn, updated, employee_id)
    return jsonify({"success": True, "transfer": transfer})
