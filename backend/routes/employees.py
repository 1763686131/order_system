"""Employee profile APIs with optional login-account binding."""

import csv
import io

from flask import Blueprint, jsonify, request, session
from flask import Response
from werkzeug.security import generate_password_hash

from utils.auth import get_current_user, require_super_admin, serialize_user
from utils.avatar_storage import (
    MAX_AVATAR_BYTES,
    delete_managed_avatar,
    normalize_avatar_url,
    save_avatar_upload,
)
from utils.db import get_db


employees_bp = Blueprint(
    "employees",
    __name__,
    url_prefix="/api/admin/employees",
)


def _text(value, max_length):
    return str(value or "").strip()[:max_length]


def _account_status(value):
    return value if value in {"active", "pending", "disabled"} else "pending"


def _employment_status(value):
    return (
        value
        if value in {"active", "probation", "leave", "resigned"}
        else "active"
    )


def _department_ids(value):
    if value in (None, ""):
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    department_ids = []
    for item in values:
        if item in (None, ""):
            continue
        try:
            department_id = int(item)
        except (TypeError, ValueError):
            raise ValueError("部门选择无效")
        if department_id <= 0:
            raise ValueError("部门选择无效")
        if department_id not in department_ids:
            department_ids.append(department_id)
    return department_ids


def _user_row(conn, user_id):
    if not user_id:
        return None
    return conn.execute(
        """
        SELECT id, username, display_name, avatar_url, status,
               must_change_password, last_login_at, permission_version,
               created_at
        FROM users WHERE id = ?
        """,
        (user_id,),
    ).fetchone()


def _latest_auth_session(conn, user_id):
    if not user_id:
        return None
    return conn.execute(
        """
        SELECT device_name, session_kind, browser, operating_system,
               ip_address, last_seen_at,
               CASE
                   WHEN revoked_at IS NOT NULL THEN 'revoked'
                   WHEN datetime(expires_at) <= CURRENT_TIMESTAMP THEN 'expired'
                   ELSE 'active'
               END AS session_status
        FROM auth_sessions
        WHERE user_id = ?
        ORDER BY datetime(last_seen_at) DESC, id DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()


def _employee_department_rows(conn, employee_id):
    return conn.execute(
        """
        SELECT departments.id, departments.name, departments.status,
               employee_departments.is_primary
        FROM employee_departments
        INNER JOIN departments ON departments.id = employee_departments.department_id
        WHERE employee_departments.employee_id = ?
        ORDER BY employee_departments.is_primary DESC,
                 departments.sort_order, departments.id
        """,
        (employee_id,),
    ).fetchall()


def _serialize_employee(conn, row):
    user = None
    latest_session = None
    department_rows = _employee_department_rows(conn, row["id"])
    if not department_rows and row["department_id"]:
        department = conn.execute(
            "SELECT id, name, status, 1 AS is_primary FROM departments WHERE id = ?",
            (row["department_id"],),
        ).fetchone()
        department_rows = [department] if department else []
    if row["user_id"]:
        user_row = _user_row(conn, row["user_id"])
        if user_row:
            user = serialize_user(conn, user_row)
            latest_session = _latest_auth_session(conn, row["user_id"])
    primary_department = department_rows[0] if department_rows else None
    roles = [
        dict(role)
        for role in conn.execute(
            """
            SELECT roles.id, roles.code, roles.name, roles.description,
                   roles.full_access, roles.data_scope
            FROM employee_roles
            INNER JOIN roles ON roles.id = employee_roles.role_id
            WHERE employee_roles.employee_id = ?
            ORDER BY roles.is_system DESC, roles.id
            """,
            (row["id"],),
        ).fetchall()
    ]
    return {
        "id": row["id"],
        "userId": row["user_id"],
        "employeeNo": row["employee_no"],
        "displayName": row["display_name"],
        "avatarUrl": row["avatar_url"] or "",
        "avatarColor": "#e9f8f3",
        "username": user["username"] if user else "",
        "passwordSet": bool(user),
        "accountStatus": row["account_status"] if user else "pending",
        "lastLoginAt": user["lastLoginAt"] if user else None,
        "lastActiveAt": latest_session["last_seen_at"] if latest_session else None,
        "lastActiveDevice": {
            "deviceName": latest_session["device_name"],
            "sessionKind": latest_session["session_kind"],
            "browser": latest_session["browser"],
            "operatingSystem": latest_session["operating_system"],
            "ipAddress": latest_session["ip_address"],
            "status": latest_session["session_status"],
        } if latest_session else None,
        "departmentId": primary_department["id"] if primary_department else None,
        "departmentIds": [department["id"] for department in department_rows],
        "departments": [
            {
                "id": department["id"],
                "name": department["name"],
                "status": department["status"],
            }
            for department in department_rows
        ],
        "department": "、".join(department["name"] for department in department_rows),
        "departmentStatus": primary_department["status"] if primary_department else None,
        "position": row["position"] or "",
        "phone": row["phone"] or "",
        "idCard": row["id_card"] or "",
        "gender": row["gender"] or "",
        "nation": row["nation"] or "",
        "birthDate": row["birth_date"] or "",
        "politicalStatus": row["political_status"] or "",
        "maritalStatus": row["marital_status"] or "",
        "healthStatus": row["health_status"] or "",
        "nativePlace": row["native_place"] or "",
        "educationLevel": row["education_level"] or "",
        "major": row["major"] or "",
        "graduationSchool": row["graduation_school"] or "",
        "graduationDate": row["graduation_date"] or "",
        "workYears": row["work_years"] or "",
        "email": row["email"] or "",
        "currentAddress": row["current_address"] or "",
        "residentialAddress": row["residential_address"] or "",
        "emergencyContact": row["emergency_contact"] or "",
        "emergencyPhone": row["emergency_phone"] or "",
        "employmentStatus": row["employment_status"],
        "employmentType": row["employment_type"],
        "hireDate": row["hire_date"] or "",
        "roleIds": [role["id"] for role in roles],
        "roles": roles,
        "createdAt": row["created_at"],
    }


def _employee_row(conn, employee_id):
    return conn.execute(
        "SELECT * FROM employees WHERE id = ?",
        (employee_id,),
    ).fetchone()


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


def _is_active_super_admin(conn, user_id):
    if not user_id:
        return False
    return bool(
        conn.execute(
            """
            SELECT 1
            FROM users
            INNER JOIN employees ON employees.user_id = users.id
            INNER JOIN employee_roles
                ON employee_roles.employee_id = employees.id
            INNER JOIN roles ON roles.id = employee_roles.role_id
            WHERE users.id = ?
              AND users.status = 'active'
              AND roles.status = 'active'
              AND roles.full_access = 1
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    )


def _next_employee_no(conn):
    sequence = conn.execute(
        "SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM employees"
    ).fetchone()["next_id"]
    while True:
        employee_no = f"E-{int(sequence):04d}"
        exists = conn.execute(
            "SELECT 1 FROM employees WHERE employee_no = ? COLLATE NOCASE",
            (employee_no,),
        ).fetchone()
        if not exists:
            return employee_no
        sequence += 1


def _employee_values(data):
    display_name = _text(data.get("displayName"), 80)
    if not display_name:
        raise ValueError("员工姓名不能为空")
    avatar_url = normalize_avatar_url(data.get("avatarUrl"))
    department_ids = _department_ids(
        data.get("departmentIds")
        if "departmentIds" in data
        else data.get("departmentId")
    )
    return {
        "display_name": display_name,
        "avatar_url": avatar_url,
        "department_ids": department_ids,
        "department_id": department_ids[0] if department_ids else None,
        "position": _text(data.get("position"), 80),
        "phone": _text(data.get("phone"), 30),
        "id_card": _text(data.get("idCard"), 40),
        "gender": _text(data.get("gender"), 20),
        "nation": _text(data.get("nation", data.get("ethnicity")), 30),
        "birth_date": _text(data.get("birthDate", data.get("birthday")), 10) or None,
        "political_status": _text(
            data.get("politicalStatus", data.get("politicalOutlook")), 40
        ),
        "marital_status": _text(
            data.get("maritalStatus", data.get("marital")), 30
        ),
        "health_status": _text(data.get("healthStatus", data.get("health")), 80),
        "native_place": _text(
            data.get("nativePlace", data.get("nativeOrigin")), 120
        ),
        "education_level": _text(
            data.get("educationLevel", data.get("education")), 50
        ),
        "major": _text(data.get("major"), 100),
        "graduation_school": _text(
            data.get("graduationSchool", data.get("school")), 120
        ),
        "graduation_date": _text(
            data.get("graduationDate", data.get("graduationTime")), 10
        ) or None,
        "work_years": _text(data.get("workYears"), 30),
        "email": _text(data.get("email"), 120),
        "current_address": _text(data.get("currentAddress"), 300),
        "residential_address": _text(
            data.get("residentialAddress", data.get("presentAddress")), 300
        ),
        "emergency_contact": _text(data.get("emergencyContact"), 80),
        "emergency_phone": _text(data.get("emergencyPhone"), 30),
        "employment_status": _employment_status(data.get("employmentStatus")),
        "employment_type": _text(data.get("employmentType"), 30) or "正式",
        "hire_date": _text(data.get("hireDate"), 10) or None,
        "account_status": _account_status(data.get("accountStatus")),
    }


def _create_bound_user(conn, data, values):
    username = _text(data.get("username"), 50)
    if not username:
        return None
    if any(char.isspace() for char in username):
        raise ValueError("登录账号不能包含空格")
    password = str(data.get("password") or "")
    if len(password) < 8:
        raise ValueError("开通登录账号时，密码至少需要 8 位")
    if conn.execute(
        "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
        (username,),
    ).fetchone():
        raise ValueError("登录账号已存在")
    user_status = "active" if values["account_status"] == "active" else "disabled"
    cursor = conn.execute(
        """
        INSERT INTO users (
            username, password_hash, display_name, name,
            avatar_url, status, must_change_password,
            permission_version, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            username,
            generate_password_hash(password),
            values["display_name"],
            values["display_name"],
            values["avatar_url"],
            user_status,
        ),
    )
    return cursor.lastrowid


def _validate_departments(conn, department_ids, allow_disabled_ids=None):
    if not department_ids:
        return []
    allow_disabled_ids = set(allow_disabled_ids or [])
    placeholders = ", ".join("?" for _ in department_ids)
    rows = conn.execute(
        f"""
        SELECT id, name, status
        FROM departments
        WHERE id IN ({placeholders})
        """,
        tuple(department_ids),
    ).fetchall()
    departments = {row["id"]: row for row in rows}
    if len(departments) != len(set(department_ids)):
        raise ValueError("部门不存在")
    for department_id in department_ids:
        department = departments[department_id]
        if department["status"] != "active" and department_id not in allow_disabled_ids:
            raise ValueError("停用部门不能分配新员工")
    return [departments[department_id] for department_id in department_ids]


def _employee_department_ids(conn, employee_id):
    department_ids = [
        row["department_id"]
        for row in conn.execute(
            """
            SELECT department_id
            FROM employee_departments
            WHERE employee_id = ?
            ORDER BY is_primary DESC, department_id
            """,
            (employee_id,),
        ).fetchall()
    ]
    if not department_ids:
        legacy_row = conn.execute(
            "SELECT department_id FROM employees WHERE id = ?",
            (employee_id,),
        ).fetchone()
        if legacy_row and legacy_row["department_id"]:
            department_ids = [legacy_row["department_id"]]
    return department_ids


def _set_employee_departments(conn, employee_id, department_ids):
    conn.execute(
        "DELETE FROM employee_departments WHERE employee_id = ?",
        (employee_id,),
    )
    conn.executemany(
        """
        INSERT INTO employee_departments (employee_id, department_id, is_primary)
        VALUES (?, ?, ?)
        """,
        [
            (employee_id, department_id, 1 if index == 0 else 0)
            for index, department_id in enumerate(department_ids)
        ],
    )


@employees_bp.route("", methods=["GET"])
@require_super_admin
def list_employees():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM employees
            ORDER BY CASE employment_status
                WHEN 'active' THEN 0
                WHEN 'probation' THEN 1
                WHEN 'leave' THEN 2
                ELSE 3
            END, id DESC
            """
        ).fetchall()
        employees = [_serialize_employee(conn, row) for row in rows]
    return jsonify({"success": True, "employees": employees})


@employees_bp.route("/export", methods=["GET"])
@require_super_admin
def export_employees():
    """Export the same employee fields used by the management page as CSV."""
    keyword = _text(request.args.get("keyword"), 80).lower()
    employment_status = _text(request.args.get("employmentStatus"), 20)
    account_status = _text(request.args.get("accountStatus"), 20)
    department_id = request.args.get("departmentId")
    try:
        department_id = int(department_id) if department_id else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "部门筛选无效"}), 400

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM employees
            ORDER BY CASE employment_status
                WHEN 'active' THEN 0
                WHEN 'probation' THEN 1
                WHEN 'leave' THEN 2
                ELSE 3
            END, id DESC
            """
        ).fetchall()
        employees = [_serialize_employee(conn, row) for row in rows]

    def matches(employee):
        if employment_status and employee["employmentStatus"] != employment_status:
            return False
        if account_status and employee["accountStatus"] != account_status:
            return False
        if department_id and department_id not in employee["departmentIds"]:
            return False
        if keyword:
            haystack = " ".join(
                str(employee.get(key) or "")
                for key in ("displayName", "employeeNo", "username", "phone", "department")
            ).lower()
            if keyword not in haystack:
                return False
        return True

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "姓名", "工号", "登录账号", "部门", "职位", "联系电话", "邮箱",
        "在职状态", "账号状态", "入职日期", "性别", "民族", "出生日期",
        "政治面貌", "婚姻状况", "身体状况", "籍贯", "文化水平", "专业", "毕业学校",
        "毕业时间", "工作年限", "身份证号", "家庭住址", "现住地址", "紧急联系人", "紧急联系电话",
    ])
    for employee in filter(matches, employees):
        writer.writerow([
            employee.get("displayName", ""), employee.get("employeeNo", ""),
            employee.get("username", ""), employee.get("department", ""),
            employee.get("position", ""), employee.get("phone", ""), employee.get("email", ""),
            employee.get("employmentStatus", ""), employee.get("accountStatus", ""),
            employee.get("hireDate", ""), employee.get("gender", ""), employee.get("nation", ""),
            employee.get("birthDate", ""), employee.get("politicalStatus", ""),
            employee.get("maritalStatus", ""), employee.get("healthStatus", ""),
            employee.get("nativePlace", ""),
            employee.get("educationLevel", ""), employee.get("major", ""),
            employee.get("graduationSchool", ""), employee.get("graduationDate", ""),
            employee.get("workYears", ""), employee.get("idCard", ""),
            employee.get("currentAddress", ""), employee.get("residentialAddress", ""),
            employee.get("emergencyContact", ""),
            employee.get("emergencyPhone", ""),
        ])
    body = "\ufeff" + output.getvalue()
    return Response(
        body,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=employees.csv"},
    )


@employees_bp.route("", methods=["POST"])
@require_super_admin
def create_employee():
    data = request.get_json(silent=True) or {}
    try:
        values = _employee_values(data)
        values["avatar_url"] = ""
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            _validate_departments(conn, values["department_ids"])
            employee_no = _text(data.get("employeeNo"), 40) or _next_employee_no(conn)
            if conn.execute(
                "SELECT 1 FROM employees WHERE employee_no = ? COLLATE NOCASE",
                (employee_no,),
            ).fetchone():
                return jsonify({"success": False, "message": "员工工号已存在"}), 409
            user_id = _create_bound_user(conn, data, values)
            cursor = conn.execute(
                """
                INSERT INTO employees (
                    user_id, employee_no, display_name, avatar_url, department_id,
                    department, position, phone, id_card, current_address,
                    residential_address, emergency_contact, emergency_phone, employment_status,
                    employment_type, hire_date, account_status, gender, nation,
                    birth_date, political_status, marital_status, health_status,
                    native_place, education_level, major, graduation_school, graduation_date,
                    work_years, email,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """,
                (
                    user_id,
                    employee_no,
                    values["display_name"],
                    values["avatar_url"],
                    values["department_id"],
                    "",
                    values["position"],
                    values["phone"],
                    values["id_card"],
                    values["current_address"],
                    values["residential_address"],
                    values["emergency_contact"],
                    values["emergency_phone"],
                    values["employment_status"],
                    values["employment_type"],
                    values["hire_date"],
                    values["account_status"] if user_id else "pending",
                    values["gender"],
                    values["nation"],
                    values["birth_date"],
                    values["political_status"],
                    values["marital_status"],
                    values["health_status"],
                    values["native_place"],
                    values["education_level"],
                    values["major"],
                    values["graduation_school"],
                    values["graduation_date"],
                    values["work_years"],
                    values["email"],
                ),
            )
            _set_employee_departments(conn, cursor.lastrowid, values["department_ids"])
            employee = _serialize_employee(
                conn,
                _employee_row(conn, cursor.lastrowid),
            )
        return jsonify(
            {"success": True, "message": "员工档案已创建", "employee": employee}
        ), 201
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@employees_bp.route("/<int:employee_id>", methods=["PUT"])
@require_super_admin
def update_employee(employee_id):
    data = request.get_json(silent=True) or {}
    try:
        values = _employee_values(data)
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = _employee_row(conn, employee_id)
            if not existing:
                return jsonify({"success": False, "message": "员工档案不存在"}), 404
            employee_no = _text(data.get("employeeNo"), 40) or existing["employee_no"]
            duplicate = conn.execute(
                """
                SELECT 1 FROM employees
                WHERE employee_no = ? COLLATE NOCASE AND id <> ?
                """,
                (employee_no, employee_id),
            ).fetchone()
            if duplicate:
                return jsonify({"success": False, "message": "员工工号已存在"}), 409

            user_id = existing["user_id"]
            values["avatar_url"] = existing["avatar_url"] or ""
            password = str(data.get("password") or "")
            existing_department_ids = _employee_department_ids(conn, employee_id)
            allow_disabled_departments = set(existing_department_ids).intersection(
                values["department_ids"]
            )
            _validate_departments(
                conn,
                values["department_ids"],
                allow_disabled_ids=allow_disabled_departments,
            )
            if user_id:
                if (
                    values["account_status"] != "active"
                    and _is_active_super_admin(conn, user_id)
                    and _active_super_admin_count(conn) <= 1
                ):
                    return jsonify(
                        {
                            "success": False,
                            "message": "不能通过员工档案停用最后一个超级管理员",
                        }
                    ), 409
                user_status = (
                    "active" if values["account_status"] == "active" else "disabled"
                )
                password_sql = ""
                params = [
                    values["display_name"],
                    values["display_name"],
                    values["avatar_url"],
                    user_status,
                ]
                if password:
                    if len(password) < 8:
                        raise ValueError("新密码至少需要 8 位")
                    password_sql = ", password_hash = ?, must_change_password = 0"
                    params.append(generate_password_hash(password))
                params.append(user_id)
                conn.execute(
                    f"""
                    UPDATE users
                    SET display_name = ?, name = ?, avatar_url = ?, status = ?,
                        permission_version = permission_version + 1,
                        updated_at = CURRENT_TIMESTAMP
                        {password_sql}
                    WHERE id = ?
                    """,
                    params,
                )
                current_user = get_current_user()
                if current_user and current_user["id"] == user_id:
                    next_version = conn.execute(
                        "SELECT permission_version FROM users WHERE id = ?",
                        (user_id,),
                    ).fetchone()["permission_version"]
                    session["permission_version"] = next_version
            elif _text(data.get("username"), 50):
                user_id = _create_bound_user(conn, data, values)

            conn.execute(
                """
                UPDATE employees SET
                    user_id = ?, employee_no = ?, display_name = ?,
                    avatar_url = ?, department_id = ?, department = ?, position = ?, phone = ?,
                    id_card = ?, current_address = ?, residential_address = ?, emergency_contact = ?,
                    emergency_phone = ?, employment_status = ?,
                    employment_type = ?, hire_date = ?, account_status = ?,
                    gender = ?, nation = ?, birth_date = ?, political_status = ?,
                    marital_status = ?, health_status = ?, native_place = ?, education_level = ?,
                    major = ?, graduation_school = ?, graduation_date = ?,
                    work_years = ?, email = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    user_id,
                    employee_no,
                    values["display_name"],
                    values["avatar_url"],
                    values["department_id"],
                    "",
                    values["position"],
                    values["phone"],
                    values["id_card"],
                    values["current_address"],
                    values["residential_address"],
                    values["emergency_contact"],
                    values["emergency_phone"],
                    values["employment_status"],
                    values["employment_type"],
                    values["hire_date"],
                    values["account_status"] if user_id else "pending",
                    values["gender"],
                    values["nation"],
                    values["birth_date"],
                    values["political_status"],
                    values["marital_status"],
                    values["health_status"],
                    values["native_place"],
                    values["education_level"],
                    values["major"],
                    values["graduation_school"],
                    values["graduation_date"],
                    values["work_years"],
                    values["email"],
                    employee_id,
                ),
            )
            _set_employee_departments(conn, employee_id, values["department_ids"])
            employee = _serialize_employee(
                conn,
                _employee_row(conn, employee_id),
            )
        return jsonify(
            {"success": True, "message": "员工档案已更新", "employee": employee}
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@employees_bp.route("/<int:employee_id>/avatar", methods=["POST"])
@require_super_admin
def upload_employee_avatar(employee_id):
    if (
        request.content_length
        and request.content_length > MAX_AVATAR_BYTES + 64 * 1024
    ):
        return jsonify({"success": False, "message": "头像图片不能超过 5MB"}), 413
    avatar_file = request.files.get("avatar")
    if not avatar_file or not avatar_file.filename:
        return jsonify({"success": False, "message": "请选择头像图片"}), 400

    with get_db() as conn:
        if not _employee_row(conn, employee_id):
            return jsonify({"success": False, "message": "员工档案不存在"}), 404

    new_avatar_url = ""
    old_avatar_url = ""
    try:
        new_avatar_url = save_avatar_upload(avatar_file, employee_id)
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            employee_row = _employee_row(conn, employee_id)
            if not employee_row:
                delete_managed_avatar(new_avatar_url)
                return jsonify({"success": False, "message": "员工档案不存在"}), 404

            old_avatar_url = employee_row["avatar_url"] or ""
            conn.execute(
                """
                UPDATE employees
                SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_avatar_url, employee_id),
            )
            if employee_row["user_id"]:
                conn.execute(
                    """
                    UPDATE users
                    SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_avatar_url, employee_row["user_id"]),
                )
            employee = _serialize_employee(conn, _employee_row(conn, employee_id))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception:
        if new_avatar_url:
            try:
                delete_managed_avatar(new_avatar_url)
            except OSError:
                pass
        return jsonify({"success": False, "message": "头像上传失败"}), 500

    if old_avatar_url and old_avatar_url != new_avatar_url:
        try:
            delete_managed_avatar(old_avatar_url)
        except OSError:
            pass
    return jsonify(
        {
            "success": True,
            "message": "头像上传成功，旧头像已清理",
            "avatarUrl": new_avatar_url,
            "employee": employee,
        }
    )


@employees_bp.route("/<int:employee_id>/avatar", methods=["DELETE"])
@require_super_admin
def delete_employee_avatar(employee_id):
    old_avatar_url = ""
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        employee_row = _employee_row(conn, employee_id)
        if not employee_row:
            return jsonify({"success": False, "message": "员工档案不存在"}), 404

        old_avatar_url = employee_row["avatar_url"] or ""
        conn.execute(
            """
            UPDATE employees
            SET avatar_url = '', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (employee_id,),
        )
        if employee_row["user_id"]:
            conn.execute(
                """
                UPDATE users
                SET avatar_url = '', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (employee_row["user_id"],),
            )
        employee = _serialize_employee(conn, _employee_row(conn, employee_id))

    if old_avatar_url:
        try:
            delete_managed_avatar(old_avatar_url)
        except OSError:
            pass
    return jsonify(
        {
            "success": True,
            "message": "头像已删除",
            "avatarUrl": "",
            "employee": employee,
        }
    )


@employees_bp.route("/<int:employee_id>/account", methods=["DELETE"])
@require_super_admin
def unbind_employee_account(employee_id):
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        employee = _employee_row(conn, employee_id)
        if not employee:
            return jsonify({"success": False, "message": "员工档案不存在"}), 404
        user_id = employee["user_id"]
        if not user_id:
            return jsonify({"success": False, "message": "该员工尚未绑定登录账号"}), 409
        current_user = get_current_user()
        if current_user and current_user["id"] == user_id:
            return jsonify(
                {
                    "success": False,
                    "message": "不能解绑当前正在使用的登录账号",
                }
            ), 409
        if _is_active_super_admin(conn, user_id) and _active_super_admin_count(conn) <= 1:
            return jsonify(
                {
                    "success": False,
                    "message": "不能解绑最后一个超级管理员账号",
                }
            ), 409

        conn.execute(
            """
            UPDATE employees
            SET user_id = NULL, account_status = 'pending',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (employee_id,),
        )
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        updated_employee = _serialize_employee(conn, _employee_row(conn, employee_id))
    return jsonify(
        {
            "success": True,
            "message": "账号已解绑，员工档案和权限组已保留",
            "employee": updated_employee,
        }
    )
