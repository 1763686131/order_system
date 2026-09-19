"""Read-only employee directory for authenticated admin users."""

from flask import Blueprint, jsonify

from utils.auth import require_admin_access
from utils.db import get_db


directory_bp = Blueprint(
    "directory",
    __name__,
    url_prefix="/api/admin/directory",
)

ONLINE_WINDOW_MINUTES = 10


@directory_bp.route("", methods=["GET"])
@require_admin_access
def get_directory():
    with get_db() as conn:
        department_rows = conn.execute(
            """
            SELECT id, name, parent_id, sort_order
            FROM departments
            WHERE status = 'active'
            ORDER BY sort_order, id
            """
        ).fetchall()
        employee_rows = conn.execute(
            """
            SELECT employees.id, employees.display_name, employees.avatar_url,
                   employees.phone, employees.position, employees.department_id,
                   employees.employment_status,
                   (
                       SELECT MAX(auth_sessions.last_seen_at)
                       FROM auth_sessions
                       WHERE auth_sessions.user_id = employees.user_id
                         AND auth_sessions.revoked_at IS NULL
                         AND datetime(auth_sessions.expires_at) > CURRENT_TIMESTAMP
                   ) AS last_active_at,
                   CASE
                       WHEN EXISTS (
                           SELECT 1
                           FROM auth_sessions
                           INNER JOIN users
                               ON users.id = auth_sessions.user_id
                           WHERE auth_sessions.user_id = employees.user_id
                             AND users.status = 'active'
                             AND auth_sessions.revoked_at IS NULL
                             AND datetime(auth_sessions.expires_at) > CURRENT_TIMESTAMP
                             AND datetime(auth_sessions.last_seen_at) >=
                                 datetime(CURRENT_TIMESTAMP, '-10 minutes')
                       )
                       THEN 1
                       ELSE 0
                   END AS is_online
            FROM employees
            WHERE employees.employment_status IN ('active', 'probation', 'leave')
            ORDER BY
                CASE employees.employment_status
                    WHEN 'active' THEN 0
                    WHEN 'probation' THEN 1
                    ELSE 2
                END,
                employees.display_name COLLATE NOCASE,
                employees.id
            """
        ).fetchall()
        assignment_rows = conn.execute(
            """
            SELECT employee_departments.employee_id,
                   employee_departments.department_id
            FROM employee_departments
            INNER JOIN departments
                ON departments.id = employee_departments.department_id
            WHERE departments.status = 'active'
            ORDER BY employee_departments.is_primary DESC,
                     departments.sort_order,
                     departments.id
            """
        ).fetchall()

    active_department_ids = {row["id"] for row in department_rows}
    employee_departments = {}
    for row in assignment_rows:
        employee_departments.setdefault(row["employee_id"], []).append(
            row["department_id"]
        )

    employees = []
    department_counts = {department_id: 0 for department_id in active_department_ids}
    for row in employee_rows:
        department_ids = list(employee_departments.get(row["id"], []))
        legacy_department_id = row["department_id"]
        if (
            legacy_department_id in active_department_ids
            and legacy_department_id not in department_ids
        ):
            department_ids.append(legacy_department_id)
        for department_id in department_ids:
            department_counts[department_id] += 1
        employees.append(
            {
                "id": row["id"],
                "displayName": row["display_name"],
                "avatarUrl": row["avatar_url"] or "",
                "phone": row["phone"] or "",
                "position": row["position"] or "",
                "departmentIds": department_ids,
                "employmentStatus": row["employment_status"],
                "online": bool(row["is_online"]),
                "lastActiveAt": row["last_active_at"],
            }
        )

    departments = [
        {
            "id": row["id"],
            "name": row["name"],
            "parentId": row["parent_id"],
            "sortOrder": row["sort_order"],
            "employeeCount": department_counts[row["id"]],
        }
        for row in department_rows
    ]
    return jsonify(
        {
            "success": True,
            "departments": departments,
            "employees": employees,
            "onlineWindowMinutes": ONLINE_WINDOW_MINUTES,
        }
    )
