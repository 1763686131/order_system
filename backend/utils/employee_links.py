"""Helpers that keep login accounts attached to employee profiles."""


def next_employee_no(conn):
    sequence = int(
        conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM employees"
        ).fetchone()["next_id"]
    )
    while True:
        employee_no = f"E-{sequence:04d}"
        if not conn.execute(
            "SELECT 1 FROM employees WHERE employee_no = ? COLLATE NOCASE",
            (employee_no,),
        ).fetchone():
            return employee_no
        sequence += 1


def ensure_employee_for_user(
    conn,
    user_id,
    display_name,
    avatar_url="",
    account_status="active",
):
    existing = conn.execute(
        "SELECT id FROM employees WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if existing:
        return existing["id"]

    cursor = conn.execute(
        """
        INSERT INTO employees (
            user_id, employee_no, display_name, avatar_url,
            employment_status, employment_type, account_status,
            created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, 'active', '正式', ?,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        """,
        (
            user_id,
            next_employee_no(conn),
            display_name,
            avatar_url or "",
            account_status if account_status in {"active", "disabled"} else "pending",
        ),
    )
    return cursor.lastrowid


def sync_employee_from_user(
    conn,
    user_id,
    display_name,
    avatar_url="",
    account_status="active",
):
    employee_id = ensure_employee_for_user(
        conn,
        user_id,
        display_name,
        avatar_url,
        account_status,
    )
    conn.execute(
        """
        UPDATE employees
        SET display_name = ?, avatar_url = ?, account_status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            display_name,
            avatar_url or "",
            account_status if account_status in {"active", "disabled"} else "pending",
            employee_id,
        ),
    )
    return employee_id
