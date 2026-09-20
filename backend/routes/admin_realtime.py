"""Server-Sent Events stream for admin messages and notifications."""

import json
import time

from flask import Blueprint, Response, stream_with_context

from utils.auth import current_session_id, get_current_user, require_admin_access
from utils.db import get_db


admin_realtime_bp = Blueprint(
    "admin_realtime",
    __name__,
    url_prefix="/api/admin/realtime",
)

POLL_INTERVAL_SECONDS = 1
KEEP_ALIVE_SECONDS = 15
PRESENCE_TOUCH_SECONDS = 60


def _event(name, payload):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"event: {name}\ndata: {data}\n\n"


def _snapshot(employee_id, session_id, touch_presence=False):
    with get_db() as conn:
        session_row = conn.execute(
            """
            SELECT id
            FROM auth_sessions
            WHERE id = ?
              AND revoked_at IS NULL
              AND datetime(expires_at) > CURRENT_TIMESTAMP
            """,
            (session_id,),
        ).fetchone()
        if not session_row:
            return None

        if touch_presence:
            conn.execute(
                """
                UPDATE auth_sessions
                SET last_seen_at = CURRENT_TIMESTAMP
                WHERE id = ? AND revoked_at IS NULL
                """,
                (session_id,),
            )

        message_row = conn.execute(
            """
            SELECT COALESCE(MAX(id), 0) AS latest_id,
                   COALESCE(SUM(
                       CASE
                           WHEN recipient_employee_id = ?
                            AND read_at IS NULL
                            AND status = 'sent'
                           THEN 1 ELSE 0
                       END
                   ), 0) AS unread_count,
                   COALESCE(MAX(
                       CASE
                           WHEN sender_employee_id = ?
                           THEN COALESCE(read_at, '')
                           ELSE ''
                       END
                   ), '') AS latest_read_at
            FROM chat_messages
            WHERE sender_employee_id = ? OR recipient_employee_id = ?
            """,
            (employee_id, employee_id, employee_id, employee_id),
        ).fetchone()
        notification_row = conn.execute(
            """
            SELECT COALESCE(MAX(id), 0) AS latest_id,
                   COALESCE(SUM(CASE WHEN status = 'unread' THEN 1 ELSE 0 END), 0)
                       AS unread_count,
                   COALESCE(MAX(COALESCE(handled_at, read_at, created_at)), '')
                       AS latest_change_at
            FROM notifications
            WHERE recipient_employee_id = ?
            """,
            (employee_id,),
        ).fetchone()
        transfer_row = conn.execute(
            """
            SELECT COALESCE(SUM(revision), 0) AS revision_total,
                   COALESCE(SUM(
                       CASE
                           WHEN recipient_employee_id = ? AND status = 'offered'
                            AND datetime(expires_at) > CURRENT_TIMESTAMP
                           THEN 1 ELSE 0
                       END
                   ), 0) AS pending_count
            FROM peer_file_transfers
            WHERE sender_employee_id = ? OR recipient_employee_id = ?
            """,
            (employee_id, employee_id, employee_id),
        ).fetchone()

    return {
        "messages": {
            "latestId": int(message_row["latest_id"] or 0),
            "unreadCount": int(message_row["unread_count"] or 0),
            "latestReadAt": message_row["latest_read_at"] or "",
        },
        "notifications": {
            "latestId": int(notification_row["latest_id"] or 0),
            "unreadCount": int(notification_row["unread_count"] or 0),
            "latestChangeAt": notification_row["latest_change_at"] or "",
        },
        "transfers": {
            "revision": int(transfer_row["revision_total"] or 0),
            "pendingCount": int(transfer_row["pending_count"] or 0),
        },
    }


@admin_realtime_bp.route("/events", methods=["GET"])
@require_admin_access
def admin_realtime_events():
    """Push compact change signals; clients fetch full authorized data over HTTP."""
    user = get_current_user() or {}
    employee_id = int(user.get("employeeId") or 0)
    session_id = current_session_id()

    def event_stream():
        previous = _snapshot(employee_id, session_id, touch_presence=True)
        if previous is None:
            return

        yield "retry: 3000\n" + _event("connected", previous)
        last_keep_alive = time.monotonic()
        last_presence_touch = last_keep_alive

        while True:
            time.sleep(POLL_INTERVAL_SECONDS)
            now = time.monotonic()
            touch_presence = now - last_presence_touch >= PRESENCE_TOUCH_SECONDS
            current = _snapshot(employee_id, session_id, touch_presence)
            if current is None:
                yield _event("session-ended", {})
                return
            if touch_presence:
                last_presence_touch = now

            if current["messages"] != previous["messages"]:
                yield _event("message-change", current["messages"])
            if current["notifications"] != previous["notifications"]:
                yield _event("notification-change", current["notifications"])
            if current["transfers"] != previous["transfers"]:
                yield _event("transfer-change", current["transfers"])

            if now - last_keep_alive >= KEEP_ALIVE_SECONDS:
                yield ": keep-alive\n\n"
                last_keep_alive = now
            previous = current

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
