"""Read and clear the system operation audit log."""
import json
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from utils.auth import _client_ip, get_current_user, require_admin_permission
from utils.db import get_db
from utils.operation_logs import insert_operation_log
from utils.permission_catalog import ADMIN_OPERATION_LOG_PERMISSIONS


operation_logs_bp = Blueprint(
    "operation_logs",
    __name__,
    url_prefix="/api/admin/operation-logs",
)


def _date_bound(value, end=False):
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError("日期格式必须为 YYYY-MM-DD") from error
    suffix = "23:59:59" if end else "00:00:00"
    return f"{parsed.strftime('%Y-%m-%d')} {suffix}"


def _actor_snapshot(user):
    if not user:
        return None
    return {
        "user_id": user.get("id"),
        "employee_id": user.get("employeeId"),
        "username": user.get("username") or "",
        "display_name": user.get("displayName") or user.get("name") or "",
        "role_names": [
            role.get("name")
            for role in user.get("roles") or []
            if isinstance(role, dict) and role.get("name")
        ],
    }


def _sales_order_number_map(conn, rows):
    ids = []
    for row in rows:
        if row["target_type"] not in {"sales_order", "logistics_order"}:
            continue
        if row["target_label"] or not str(row["target_id"] or "").isdigit():
            continue
        ids.append(int(row["target_id"]))
    ids = sorted(set(ids))
    if not ids:
        return {}

    placeholders = ",".join("?" for _ in ids)
    order_rows = conn.execute(
        f"""
        SELECT id, order_number
        FROM orders
        WHERE id IN ({placeholders})
          AND COALESCE(order_number, '') != ''
        """,
        ids,
    ).fetchall()
    return {
        str(row["id"]): row["order_number"]
        for row in order_rows
        if row["order_number"]
    }


@operation_logs_bp.route("", methods=["GET"])
@require_admin_permission(ADMIN_OPERATION_LOG_PERMISSIONS["read"])
def list_operation_logs():
    try:
        start_date = _date_bound(request.args.get("startDate"))
        end_date = _date_bound(request.args.get("endDate"), end=True)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    page = max(request.args.get("page", 1, type=int) or 1, 1)
    page_size = min(max(request.args.get("pageSize", 50, type=int) or 50, 1), 200)
    module_code = (request.args.get("module") or "").strip()[:80]
    action_code = (request.args.get("action") or "").strip()[:80]
    actor = (request.args.get("actor") or "").strip()[:100]
    keyword = (request.args.get("keyword") or "").strip()[:120]
    outcome = (request.args.get("outcome") or "").strip().lower()

    clauses = []
    params = []
    if start_date:
        clauses.append("occurred_at >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("occurred_at <= ?")
        params.append(end_date)
    if module_code:
        clauses.append("module_code = ?")
        params.append(module_code)
    if action_code:
        clauses.append("action_code = ?")
        params.append(action_code)
    if actor:
        clauses.append(
            "(actor_username LIKE ? OR actor_display_name LIKE ? OR actor_role_names LIKE ?)"
        )
        pattern = f"%{actor}%"
        params.extend((pattern, pattern, pattern))
    if outcome in {"success", "failure"}:
        clauses.append("succeeded = ?")
        params.append(1 if outcome == "success" else 0)
    if keyword:
        clauses.append(
            "(target_id LIKE ? OR target_label LIKE ? OR request_path LIKE ? OR ip_address LIKE ?)"
        )
        pattern = f"%{keyword}%"
        params.extend((pattern, pattern, pattern, pattern))

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS count FROM operation_logs {where_sql}",
            params,
        ).fetchone()["count"]
        rows = conn.execute(
            f"""
            SELECT *
            FROM operation_logs
            {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, (page - 1) * page_size),
        ).fetchall()
        sales_order_numbers = _sales_order_number_map(conn, rows)

    items = []
    for row in rows:
        try:
            details = json.loads(row["details_json"] or "{}")
        except (TypeError, ValueError):
            details = {}
        try:
            role_names = json.loads(row["actor_role_names"] or "[]")
        except (TypeError, ValueError):
            role_names = []
        target_id = row["target_id"]
        target_label = row["target_label"]
        if (
            row["target_type"] in {"sales_order", "logistics_order"}
            and not target_label
            and str(target_id or "") in sales_order_numbers
        ):
            target_id = sales_order_numbers[str(target_id)]
            target_label = "销售订单"
        items.append(
            {
                "id": row["id"],
                "occurredAt": row["occurred_at"],
                "actorUserId": row["actor_user_id"],
                "actorEmployeeId": row["actor_employee_id"],
                "actorUsername": row["actor_username"],
                "actorDisplayName": row["actor_display_name"],
                "actorRoleNames": role_names,
                "moduleCode": row["module_code"],
                "moduleName": row["module_name"],
                "actionCode": row["action_code"],
                "actionName": row["action_name"],
                "targetType": row["target_type"],
                "targetId": target_id,
                "targetLabel": target_label,
                "requestMethod": row["request_method"],
                "requestPath": row["request_path"],
                "requestId": row["request_id"],
                "sourceSurface": row["source_surface"],
                "ipAddress": row["ip_address"],
                "userAgent": row["user_agent"],
                "statusCode": row["status_code"],
                "succeeded": bool(row["succeeded"]),
                "details": details,
            }
        )

    return jsonify(
        {
            "success": True,
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
    )


@operation_logs_bp.route("", methods=["DELETE"])
@require_admin_permission(ADMIN_OPERATION_LOG_PERMISSIONS["clear"])
def clear_operation_logs():
    user = get_current_user()
    actor = _actor_snapshot(user)
    request_id = (
        str(request.headers.get("X-Request-ID") or "").strip()[:100]
        or uuid.uuid4().hex
    )
    with get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM operation_logs"
        ).fetchone()["count"]
        conn.execute("DELETE FROM operation_logs")
        insert_operation_log(
            conn,
            actor=actor,
            module_code="operation_logs",
            action_code="clear",
            target_type="operation_log",
            target_label="清空全部日志",
            request_method="DELETE",
            request_path=request.path,
            request_id=request_id,
            source_surface="admin",
            ip_address=_client_ip(),
            user_agent=request.headers.get("User-Agent", ""),
            status_code=200,
            succeeded=True,
            details={"clearedCount": count},
        )
    return jsonify(
        {
            "success": True,
            "message": f"已清空 {count} 条操作日志",
            "clearedCount": count,
        }
    )
