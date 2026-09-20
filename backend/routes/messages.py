"""Private employee messages and server-stored attachment APIs."""

from datetime import datetime
import hashlib
import os
import uuid

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from utils.auth import get_current_user, require_admin_permission
from utils.db import get_db
from utils.permission_catalog import ADMIN_MESSAGE_PERMISSIONS


messages_bp = Blueprint("messages", __name__, url_prefix="/api/admin/messages")

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
if os.path.exists("/app/frontend/index.html") and os.path.isdir("/app/uploads"):
    UPLOAD_ROOT = "/app/uploads"
else:
    UPLOAD_ROOT = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "uploads",
    )
ATTACHMENT_ROOT = os.path.join(UPLOAD_ROOT, "chat-attachments")


def _employee_id():
    user = get_current_user() or {}
    return int(user.get("employeeId") or 0)


def _limit_arg(default=50, maximum=100):
    try:
        return min(max(int(request.args.get("limit", default)), 1), maximum)
    except (TypeError, ValueError):
        return default


def _conversation_pair(first_id, second_id):
    return tuple(sorted((int(first_id), int(second_id))))


def _validate_recipient(conn, employee_id, recipient_id):
    try:
        recipient_id = int(recipient_id)
    except (TypeError, ValueError):
        raise ValueError("收件人无效")
    if recipient_id == employee_id:
        raise ValueError("不能给自己发送留言")
    recipient = conn.execute(
        """
        SELECT employees.id
        FROM employees
        INNER JOIN users ON users.id = employees.user_id
        WHERE employees.id = ?
          AND users.status = 'active'
          AND employees.account_status = 'active'
          AND employees.employment_status IN ('active', 'probation')
        """,
        (recipient_id,),
    ).fetchone()
    if not recipient:
        raise ValueError("收件人不存在或账号不可用")
    return recipient_id


def _find_or_create_conversation(conn, employee_id, recipient_id):
    employee_a_id, employee_b_id = _conversation_pair(employee_id, recipient_id)
    conn.execute(
        """
        INSERT OR IGNORE INTO chat_conversations (employee_a_id, employee_b_id)
        VALUES (?, ?)
        """,
        (employee_a_id, employee_b_id),
    )
    row = conn.execute(
        """
        SELECT id FROM chat_conversations
        WHERE employee_a_id = ? AND employee_b_id = ?
        """,
        (employee_a_id, employee_b_id),
    ).fetchone()
    return row["id"]


def _conversation_for_participant(conn, conversation_id, employee_id):
    return conn.execute(
        """
        SELECT * FROM chat_conversations
        WHERE id = ? AND (employee_a_id = ? OR employee_b_id = ?)
        """,
        (conversation_id, employee_id, employee_id),
    ).fetchone()


def _serialize_message(row, employee_id):
    item = dict(row)
    attachment = None
    if item.get("attachment_id"):
        attachment = {
            "id": item["attachment_id"],
            "fileName": item["original_name"],
            "fileSize": item["file_size"],
            "mimeType": item["mime_type"],
            "downloadUrl": f"/api/admin/messages/attachments/{item['attachment_id']}/download",
        }
    return {
        "id": item["id"],
        "conversationId": item["conversation_id"],
        "senderEmployeeId": item["sender_employee_id"],
        "recipientEmployeeId": item["recipient_employee_id"],
        "sender": "me" if item["sender_employee_id"] == employee_id else "them",
        "type": "file" if item["message_type"] == "server_file" else "text",
        "text": item["content"],
        "createdAt": item["created_at"],
        "readAt": item["read_at"],
        "status": item["status"],
        "attachment": attachment,
    }


MESSAGE_SELECT = """
    SELECT chat_messages.*,
           chat_attachments.id AS attachment_id,
           chat_attachments.original_name,
           chat_attachments.file_size,
           chat_attachments.mime_type
    FROM chat_messages
    LEFT JOIN chat_attachments ON chat_attachments.message_id = chat_messages.id
"""


@messages_bp.route("/unread-count", methods=["GET"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["read"])
def unread_count():
    employee_id = _employee_id()
    with get_db() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*) AS total FROM chat_messages
            WHERE recipient_employee_id = ? AND read_at IS NULL AND status = 'sent'
            """,
            (employee_id,),
        ).fetchone()["total"]
    return jsonify({"success": True, "unreadCount": count})


@messages_bp.route("/conversations", methods=["GET"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["read"])
def list_conversations():
    employee_id = _employee_id()
    limit = _limit_arg()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT conversations.id, conversations.last_message_at,
                   contacts.id AS contact_id,
                   contacts.display_name, contacts.avatar_url,
                   contacts.phone, contacts.position,
                   messages.message_type, messages.content,
                   attachments.original_name,
                   (
                       SELECT COUNT(*) FROM chat_messages AS unread
                       WHERE unread.conversation_id = conversations.id
                         AND unread.recipient_employee_id = ?
                         AND unread.read_at IS NULL
                         AND unread.status = 'sent'
                   ) AS unread_count,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM auth_sessions
                       WHERE auth_sessions.user_id = contacts.user_id
                         AND auth_sessions.revoked_at IS NULL
                         AND datetime(auth_sessions.expires_at) > CURRENT_TIMESTAMP
                         AND datetime(auth_sessions.last_seen_at) >= datetime(CURRENT_TIMESTAMP, '-10 minutes')
                   ) THEN 1 ELSE 0 END AS is_online
            FROM chat_conversations AS conversations
            INNER JOIN employees AS contacts
                ON contacts.id = CASE
                    WHEN conversations.employee_a_id = ? THEN conversations.employee_b_id
                    ELSE conversations.employee_a_id
                END
            LEFT JOIN chat_messages AS messages
                ON messages.id = conversations.last_message_id
            LEFT JOIN chat_attachments AS attachments
                ON attachments.message_id = messages.id
            WHERE conversations.employee_a_id = ? OR conversations.employee_b_id = ?
            ORDER BY datetime(conversations.last_message_at) DESC, conversations.id DESC
            LIMIT ?
            """,
            (employee_id, employee_id, employee_id, employee_id, limit),
        ).fetchall()
        conversations = []
        for row in rows:
            preview = row["content"] or ""
            if row["message_type"] == "server_file":
                preview = f"[附件] {row['original_name'] or '文件'}"
            conversations.append(
                {
                    "id": row["id"],
                    "contact": {
                        "id": row["contact_id"],
                        "displayName": row["display_name"],
                        "avatarUrl": row["avatar_url"] or "",
                        "phone": row["phone"] or "",
                        "position": row["position"] or "",
                        "online": bool(row["is_online"]),
                    },
                    "preview": preview,
                    "lastMessageAt": row["last_message_at"],
                    "unreadCount": row["unread_count"],
                }
            )
    return jsonify({"success": True, "conversations": conversations})


@messages_bp.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["read"])
def list_messages(conversation_id):
    employee_id = _employee_id()
    limit = _limit_arg()
    before_id = request.args.get("beforeId", type=int)
    with get_db() as conn:
        if not _conversation_for_participant(conn, conversation_id, employee_id):
            return jsonify({"success": False, "message": "会话不存在"}), 404
        params = [conversation_id]
        before_sql = ""
        if before_id:
            before_sql = " AND chat_messages.id < ?"
            params.append(before_id)
        params.append(limit)
        rows = conn.execute(
            MESSAGE_SELECT
            + """
            WHERE chat_messages.conversation_id = ?
              AND chat_messages.status = 'sent'
            """
            + before_sql
            + " ORDER BY chat_messages.id DESC LIMIT ?",
            params,
        ).fetchall()
        messages = [_serialize_message(row, employee_id) for row in reversed(rows)]
    return jsonify({"success": True, "messages": messages, "hasMore": len(rows) == limit})


@messages_bp.route("/with/<int:contact_id>/messages", methods=["GET"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["read"])
def list_messages_with_contact(contact_id):
    employee_id = _employee_id()
    with get_db() as conn:
        try:
            _validate_recipient(conn, employee_id, contact_id)
        except ValueError as error:
            return jsonify({"success": False, "message": str(error)}), 400
        employee_a_id, employee_b_id = _conversation_pair(employee_id, contact_id)
        conversation = conn.execute(
            """
            SELECT id FROM chat_conversations
            WHERE employee_a_id = ? AND employee_b_id = ?
            """,
            (employee_a_id, employee_b_id),
        ).fetchone()
        if not conversation:
            return jsonify({"success": True, "conversationId": None, "messages": []})
        rows = conn.execute(
            MESSAGE_SELECT
            + """
            WHERE chat_messages.conversation_id = ?
              AND chat_messages.status = 'sent'
            ORDER BY chat_messages.id DESC LIMIT 100
            """,
            (conversation["id"],),
        ).fetchall()
        conn.execute(
            """
            UPDATE chat_messages
            SET read_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ? AND recipient_employee_id = ?
              AND read_at IS NULL AND status = 'sent'
            """,
            (conversation["id"], employee_id),
        )
        messages = [_serialize_message(row, employee_id) for row in reversed(rows)]
    return jsonify(
        {
            "success": True,
            "conversationId": conversation["id"],
            "messages": messages,
        }
    )


@messages_bp.route("", methods=["POST"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["send"])
def send_message():
    employee_id = _employee_id()
    data = request.get_json(silent=True) or {}
    content = str(data.get("content") or "").strip()
    client_message_id = str(data.get("clientMessageId") or "").strip()[:100]
    if not content:
        return jsonify({"success": False, "message": "留言内容不能为空"}), 400
    if len(content) > 2000:
        return jsonify({"success": False, "message": "留言内容不能超过2000字"}), 400
    try:
        with get_db() as conn:
            recipient_id = _validate_recipient(conn, employee_id, data.get("recipientEmployeeId"))
            if client_message_id:
                duplicate = conn.execute(
                    MESSAGE_SELECT
                    + " WHERE chat_messages.sender_employee_id = ? AND chat_messages.client_message_id = ?",
                    (employee_id, client_message_id),
                ).fetchone()
                if duplicate:
                    return jsonify({"success": True, "message": _serialize_message(duplicate, employee_id)})
            conversation_id = _find_or_create_conversation(conn, employee_id, recipient_id)
            insert_clause = "INSERT OR IGNORE" if client_message_id else "INSERT"
            cursor = conn.execute(
                f"""
                {insert_clause} INTO chat_messages (
                    conversation_id, sender_employee_id, recipient_employee_id,
                    message_type, content, client_message_id
                ) VALUES (?, ?, ?, 'text', ?, ?)
                """,
                (conversation_id, employee_id, recipient_id, content, client_message_id),
            )
            if cursor.rowcount == 0:
                duplicate = conn.execute(
                    MESSAGE_SELECT
                    + " WHERE chat_messages.sender_employee_id = ? AND chat_messages.client_message_id = ?",
                    (employee_id, client_message_id),
                ).fetchone()
                return jsonify(
                    {"success": True, "message": _serialize_message(duplicate, employee_id)}
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
            row = conn.execute(
                MESSAGE_SELECT + " WHERE chat_messages.id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return jsonify({"success": True, "message": _serialize_message(row, employee_id)}), 201
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400


@messages_bp.route("/conversations/<int:conversation_id>/read", methods=["POST"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["read"])
def mark_conversation_read(conversation_id):
    employee_id = _employee_id()
    with get_db() as conn:
        if not _conversation_for_participant(conn, conversation_id, employee_id):
            return jsonify({"success": False, "message": "会话不存在"}), 404
        cursor = conn.execute(
            """
            UPDATE chat_messages
            SET read_at = CURRENT_TIMESTAMP
            WHERE conversation_id = ? AND recipient_employee_id = ?
              AND read_at IS NULL AND status = 'sent'
            """,
            (conversation_id, employee_id),
        )
    return jsonify({"success": True, "updated": cursor.rowcount})


@messages_bp.route("/read-all", methods=["POST"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["read"])
def mark_all_messages_read():
    employee_id = _employee_id()
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE chat_messages
            SET read_at = CURRENT_TIMESTAMP
            WHERE recipient_employee_id = ? AND read_at IS NULL AND status = 'sent'
            """,
            (employee_id,),
        )
    return jsonify({"success": True, "updated": cursor.rowcount})


@messages_bp.route("/attachments", methods=["POST"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["attachment"])
def upload_attachment():
    employee_id = _employee_id()
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"success": False, "message": "请选择附件"}), 400
    if request.content_length and request.content_length > MAX_ATTACHMENT_SIZE + 256 * 1024:
        return jsonify({"success": False, "message": "附件不能超过10MB"}), 413

    data = upload.stream.read(MAX_ATTACHMENT_SIZE + 1)
    if len(data) > MAX_ATTACHMENT_SIZE:
        return jsonify({"success": False, "message": "附件不能超过10MB"}), 413
    if not data:
        return jsonify({"success": False, "message": "附件内容为空"}), 400

    original_name = os.path.basename(upload.filename.replace("\\", "/")).strip()
    original_name = "".join(
        character for character in original_name if ord(character) >= 32
    )[:255] or "attachment"
    safe_name = secure_filename(original_name) or "attachment"
    month = datetime.now().strftime("%Y-%m")
    extension = os.path.splitext(safe_name)[1][:20]
    stored_name = f"{uuid.uuid4().hex}{extension}"
    relative_path = os.path.join(month, stored_name).replace("\\", "/")
    target_dir = os.path.join(ATTACHMENT_ROOT, month)
    target_path = os.path.join(target_dir, stored_name)
    os.makedirs(target_dir, exist_ok=True)

    try:
        with get_db() as conn:
            recipient_id = _validate_recipient(conn, employee_id, request.form.get("recipientEmployeeId"))
            conversation_id = _find_or_create_conversation(conn, employee_id, recipient_id)
            with open(target_path, "xb") as target:
                target.write(data)
            cursor = conn.execute(
                """
                INSERT INTO chat_messages (
                    conversation_id, sender_employee_id, recipient_employee_id,
                    message_type, content
                ) VALUES (?, ?, ?, 'server_file', ?)
                """,
                (conversation_id, employee_id, recipient_id, str(request.form.get("content") or "").strip()[:2000]),
            )
            conn.execute(
                """
                INSERT INTO chat_attachments (
                    message_id, original_name, stored_name, storage_path,
                    file_size, mime_type, sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cursor.lastrowid,
                    original_name,
                    stored_name,
                    relative_path,
                    len(data),
                    upload.mimetype or "application/octet-stream",
                    hashlib.sha256(data).hexdigest(),
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
            row = conn.execute(
                MESSAGE_SELECT + " WHERE chat_messages.id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return jsonify({"success": True, "message": _serialize_message(row, employee_id)}), 201
    except ValueError as error:
        if os.path.exists(target_path):
            os.remove(target_path)
        return jsonify({"success": False, "message": str(error)}), 400
    except Exception:
        if os.path.exists(target_path):
            os.remove(target_path)
        raise


@messages_bp.route("/attachments/<int:attachment_id>/download", methods=["GET"])
@require_admin_permission(ADMIN_MESSAGE_PERMISSIONS["attachment"])
def download_attachment(attachment_id):
    employee_id = _employee_id()
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT chat_attachments.*,
                   chat_messages.sender_employee_id,
                   chat_messages.recipient_employee_id
            FROM chat_attachments
            INNER JOIN chat_messages ON chat_messages.id = chat_attachments.message_id
            WHERE chat_attachments.id = ?
              AND (chat_messages.sender_employee_id = ? OR chat_messages.recipient_employee_id = ?)
            """,
            (attachment_id, employee_id, employee_id),
        ).fetchone()
    if not row:
        return jsonify({"success": False, "message": "附件不存在或无权访问"}), 404
    file_path = os.path.abspath(os.path.join(ATTACHMENT_ROOT, row["storage_path"]))
    if os.path.commonpath((os.path.abspath(ATTACHMENT_ROOT), file_path)) != os.path.abspath(ATTACHMENT_ROOT):
        return jsonify({"success": False, "message": "附件路径无效"}), 400
    if not os.path.isfile(file_path):
        return jsonify({"success": False, "message": "附件文件已丢失"}), 404
    return send_file(
        file_path,
        as_attachment=True,
        download_name=row["original_name"],
        mimetype=row["mime_type"],
    )
