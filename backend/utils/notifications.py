"""Helpers for creating and completing user-specific audit notifications."""

import json

from utils.permission_catalog import (
    ADMIN_AUDIT_NOTIFICATION_PERMISSIONS,
    ADMIN_SALES_ORDER_PERMISSIONS,
)


AUDIT_NOTIFICATION_CONFIG = {
    "sales_order": {
        "permission": ADMIN_SALES_ORDER_PERMISSIONS["audit"],
        "title": "销售订单待审核",
        "route": "admin-sales",
    },
    "stock_inbound": {
        "permission": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["stock_inbound"],
        "title": "采购入库单待审核",
        "route": "admin-stock-in",
    },
    "material_outbound": {
        "permission": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["material_outbound"],
        "title": "原材料出库单待审核",
        "route": "admin-inventory-material-outbounds",
    },
    "payment_receipt": {
        "permission": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["payment_receipt"],
        "title": "收款单待审核",
        "route": "admin-finance-payment-history",
    },
    "return_order": {
        "permission": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["return_order"],
        "title": "退货单待审核",
        "route": "admin-sales-returns",
    },
}


def create_audit_notifications(
    conn,
    document_type,
    document_id,
    document_no,
    content="",
    event_version="submitted",
):
    """Notify active employees whose role can audit this document type."""
    config = AUDIT_NOTIFICATION_CONFIG.get(document_type)
    if not config:
        return 0

    recipients = conn.execute(
        """
        SELECT DISTINCT employees.id
        FROM employees
        INNER JOIN users ON users.id = employees.user_id
        INNER JOIN employee_roles ON employee_roles.employee_id = employees.id
        INNER JOIN roles ON roles.id = employee_roles.role_id
        WHERE users.status = 'active'
          AND employees.account_status = 'active'
          AND employees.employment_status IN ('active', 'probation')
          AND roles.status = 'active'
          AND (
              roles.full_access = 1
              OR EXISTS (
                  SELECT 1
                  FROM role_permissions
                  INNER JOIN permissions
                      ON permissions.id = role_permissions.permission_id
                  WHERE role_permissions.role_id = roles.id
                    AND permissions.code = ?
              )
          )
        """,
        (config["permission"],),
    ).fetchall()

    document_no = str(document_no or document_id)
    event_key = f"audit:{document_type}:{document_id}:{event_version}"
    target = {
        "name": config["route"],
        "query": {
            "documentId": str(document_id),
            "documentNo": document_no,
        },
    }
    notification_content = content or f"单据 {document_no} 已提交，请及时审核。"
    created = 0
    for recipient in recipients:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO notifications (
                recipient_employee_id, notification_type, title, content,
                document_type, document_id, document_no, target_json,
                event_key, status, created_at
            ) VALUES (?, 'audit', ?, ?, ?, ?, ?, ?, ?, 'unread', CURRENT_TIMESTAMP)
            """,
            (
                recipient["id"],
                config["title"],
                notification_content,
                document_type,
                str(document_id),
                document_no,
                json.dumps(target, ensure_ascii=False),
                event_key,
            ),
        )
        created += cursor.rowcount
    return created


def complete_audit_notifications(conn, document_type, document_id):
    """Mark outstanding audit notifications handled after a successful audit."""
    conn.execute(
        """
        UPDATE notifications
        SET status = 'handled',
            read_at = COALESCE(read_at, CURRENT_TIMESTAMP),
            handled_at = COALESCE(handled_at, CURRENT_TIMESTAMP)
        WHERE document_type = ?
          AND document_id = ?
          AND status <> 'handled'
        """,
        (document_type, str(document_id)),
    )
