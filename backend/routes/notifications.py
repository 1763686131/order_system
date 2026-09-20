"""User-specific system and document audit notifications."""

import json

from flask import Blueprint, jsonify, request

from utils.auth import get_current_user, require_admin_access
from utils.db import get_db


notifications_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/admin/notifications",
)


def _employee_id():
    return int((get_current_user() or {}).get("employeeId") or 0)


def _limit_arg():
    try:
        return min(max(int(request.args.get("limit", 50)), 1), 100)
    except (TypeError, ValueError):
        return 50


def _serialize(row):
    item = dict(row)
    try:
        target = json.loads(item["target_json"] or "{}")
    except (TypeError, ValueError):
        target = {}
    return {
        "id": item["id"],
        "type": item["notification_type"],
        "typeLabel": "单据审核" if item["notification_type"] == "audit" else "系统通知",
        "title": item["title"],
        "preview": item["content"],
        "documentType": item["document_type"],
        "documentId": item["document_id"],
        "documentNo": item["document_no"],
        "target": target,
        "status": item["status"],
        "unread": item["status"] == "unread",
        "createdAt": item["created_at"],
        "readAt": item["read_at"],
        "handledAt": item["handled_at"],
    }


@notifications_bp.route("", methods=["GET"])
@require_admin_access
def list_notifications():
    employee_id = _employee_id()
    limit = _limit_arg()
    before_id = request.args.get("beforeId", type=int)
    unread_only = str(request.args.get("unreadOnly") or "").lower() in {"1", "true", "yes"}
    clauses = ["recipient_employee_id = ?"]
    params = [employee_id]
    if before_id:
        clauses.append("id < ?")
        params.append(before_id)
    if unread_only:
        clauses.append("status = 'unread'")
    params.append(limit)
    with get_db() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM notifications
            WHERE {' AND '.join(clauses)}
            ORDER BY id DESC LIMIT ?
            """,
            params,
        ).fetchall()
    return jsonify({"success": True, "notifications": [_serialize(row) for row in rows]})


@notifications_bp.route("/unread-count", methods=["GET"])
@require_admin_access
def unread_count():
    with get_db() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*) AS total FROM notifications
            WHERE recipient_employee_id = ? AND status = 'unread'
            """,
            (_employee_id(),),
        ).fetchone()["total"]
    return jsonify({"success": True, "unreadCount": count})


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@require_admin_access
def mark_notification_read(notification_id):
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE notifications
            SET status = CASE WHEN status = 'unread' THEN 'read' ELSE status END,
                read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
            WHERE id = ? AND recipient_employee_id = ?
            """,
            (notification_id, _employee_id()),
        )
    if cursor.rowcount != 1:
        return jsonify({"success": False, "message": "通知不存在"}), 404
    return jsonify({"success": True})


@notifications_bp.route("/read-all", methods=["POST"])
@require_admin_access
def mark_all_notifications_read():
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE notifications
            SET status = 'read', read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
            WHERE recipient_employee_id = ? AND status = 'unread'
            """,
            (_employee_id(),),
        )
    return jsonify({"success": True, "updated": cursor.rowcount})
