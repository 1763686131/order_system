"""Request-level operation audit logging for selected business APIs."""
import json
import re
import uuid

from flask import current_app, g, request, session

from utils.auth import _client_ip, get_current_user
from utils.db import get_db


_RULES = (
    (r"/api/auth/login", {"POST"}, "account_security", "账号安全", "account"),
    (r"/api/auth/logout", {"POST"}, "account_security", "账号安全", "account"),
    (r"/api/auth/password", {"PUT"}, "account_security", "账号安全", "account"),
    (r"/api/auth/profile", {"PUT"}, "account_security", "账号安全", "account"),
    (
        r"/api/admin/users(?:/\d+(?:/password)?)?",
        {"POST", "PUT", "DELETE"},
        "account_security",
        "账号安全",
        "account",
    ),
    (
        r"/api/admin/roles(?:/\d+(?:/members)?)?",
        {"POST", "PUT"},
        "role_permissions",
        "角色权限",
        "role",
    ),
    (
        r"/api/admin/employees(?:/\d+(?:/(?:avatar|account))?)?",
        {"POST", "PUT", "DELETE"},
        "employees",
        "员工管理",
        "employee",
    ),
    (
        r"/api/admin/departments(?:/\d+)?",
        {"POST", "PUT", "DELETE"},
        "departments",
        "部门管理",
        "department",
    ),
    (
        r"/api/orders(?:/\d+(?:/(?:edit|upload_receipt|receipt|paid-amount))?)?",
        {"POST", "PUT", "DELETE"},
        "sales_orders",
        "销售订单",
        "sales_order",
    ),
    (
        r"/api/freight-records|/api/freight-records/reserve-fund(?:/latest|/[^/]+)?",
        {"POST", "PUT", "DELETE"},
        "logistics",
        "物流管理",
        "freight_record",
    ),
    (
        r"/api/carrier_tags",
        {"POST"},
        "logistics",
        "物流管理",
        "carrier_tag",
    ),
    (
        r"/api/raw-material-products(?:/\d+)?",
        {"POST", "PUT", "DELETE"},
        "raw_materials",
        "原材料",
        "raw_material",
    ),
    (
        r"/api/products(?:/(?:inventory(?:/(?:batch|\d+))?|units(?:/(?:measurements|packagings|\d+))?|attributes(?:/\d+(?:/options(?:/\d+)?)?)?))?",
        {"POST", "PUT", "DELETE"},
        "inventory",
        "商品与库存",
        "product_inventory",
    ),
    (
        r"/api/(?:warehouses(?:/\d+(?:/categories(?:/\d+)?)?)?|suppliers(?:/\d+)?|stock-inbounds(?:/\d+(?:/(?:audit|restart))?)?|stock-balances|stock-movements)",
        {"POST", "PUT", "DELETE"},
        "inventory",
        "库存管理",
        "stock_record",
    ),
    (
        r"/api/material-outbound-settings|/api/material-outbounds(?:/\d+(?:/(?:audit|restart))?)?",
        {"POST", "PUT", "DELETE"},
        "inventory",
        "库存管理",
        "material_outbound",
    ),
    (
        r"/api/payment-receipts(?:/(?:attachments|\d+(?:/audit)?))?",
        {"POST", "PUT", "DELETE"},
        "payment_history",
        "收款历史",
        "payment_receipt",
    ),
    (
        r"/api/bank-accounts(?:/(?:options|\d+))?",
        {"POST", "PUT", "DELETE"},
        "bank_accounts",
        "银行账户",
        "bank_account",
    ),
    (
        r"/api/upload/bank-(?:card-background|icon)",
        {"POST"},
        "bank_accounts",
        "银行账户",
        "bank_account_asset",
    ),
    (
        r"/api/print-templates(?:/(?:\d+(?:/set-default)?|migrate))?",
        {"POST", "PUT", "DELETE"},
        "print_templates",
        "打印模板",
        "print_template",
    ),
)

_ACTION_NAMES = {
    "create": "新增",
    "update": "修改",
    "delete": "删除",
    "login_success": "登录成功",
    "login_failure": "登录失败",
    "logout": "退出登录",
    "password_change": "修改密码",
    "password_reset": "重置密码",
    "clear": "清空日志",
}
_SENSITIVE_FIELD = re.compile(
    r"(password|token|secret|cookie|authorization|id.?card|account.?number|"
    r"bank.?code|phone|mobile|email|avatar|attachment|image|content)",
    re.IGNORECASE,
)
_MODULE_LABELS = {
    "account_security": "账号安全",
    "role_permissions": "角色权限",
    "employees": "员工管理",
    "departments": "部门管理",
    "sales_orders": "销售订单",
    "logistics": "物流管理",
    "raw_materials": "原材料",
    "inventory": "库存管理",
    "payment_history": "收款历史",
    "bank_accounts": "银行账户",
    "print_templates": "打印模板",
    "operation_logs": "操作日志",
}


def _matched_rule(path, method):
    for pattern, methods, module_code, module_name, target_type in _RULES:
        if method in methods and re.fullmatch(pattern, path):
            return {
                "module_code": module_code,
                "module_name": module_name,
                "target_type": target_type,
            }
    return None


def _request_action(rule, path, method, status_code):
    if path == "/api/auth/login":
        return "login_success" if status_code < 400 else "login_failure"
    if path == "/api/auth/logout":
        return "logout"
    if path == "/api/auth/password":
        return "password_change"
    if re.fullmatch(r"/api/admin/users/\d+/password", path):
        return "password_reset"
    if path.endswith("/account") and method == "DELETE":
        return "update"
    if path.endswith("/avatar"):
        return "update" if method == "POST" else "delete"
    if path.endswith("/attachments") and method == "POST":
        return "create"
    if path.startswith("/api/upload/bank-") and method == "POST":
        return "update"
    if path.startswith("/api/stock-inbounds/") and method == "DELETE":
        return "delete"
    if path.startswith("/api/material-outbounds/") and method == "DELETE":
        return "delete"
    if path.endswith("/audit"):
        return "update"
    if path.endswith("/restart"):
        return "update"
    if path.endswith("/set-default") or path.endswith("/migrate"):
        return "update"
    return {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }.get(method, "update")


def _safe_text(value, limit=250):
    return str(value or "").replace("\x00", "").strip()[:limit]


def _field_names(values):
    if not isinstance(values, dict):
        return []
    return sorted(
        key for key in values
        if isinstance(key, str) and not _SENSITIVE_FIELD.search(key)
    )[:80]


def _request_details():
    payload = request.get_json(silent=True)
    return {
        "fields": _field_names(payload),
        "filters": sorted(
            key for key in request.args.keys()
            if isinstance(key, str) and not _SENSITIVE_FIELD.search(key)
        )[:40],
    }


def _actor_snapshot(user):
    if not user:
        return None
    roles = user.get("roles") or []
    return {
        "user_id": user.get("id"),
        "employee_id": user.get("employeeId"),
        "username": _safe_text(user.get("username"), 80),
        "display_name": _safe_text(
            user.get("displayName") or user.get("name"), 100
        ),
        "role_names": [
            _safe_text(role.get("name"), 80)
            for role in roles
            if isinstance(role, dict) and role.get("name")
        ][:20],
    }


def _actor_for_session(conn):
    user_id = session.get("user_id")
    if not user_id:
        return None

    row = conn.execute(
        """
        SELECT users.id, users.username, users.display_name, employees.id AS employee_id
        FROM users
        LEFT JOIN employees ON employees.user_id = users.id
        WHERE users.id = ?
        """,
        (user_id,),
    ).fetchone()
    if not row:
        return None
    roles = conn.execute(
        """
        SELECT roles.name
        FROM employees
        INNER JOIN employee_roles ON employee_roles.employee_id = employees.id
        INNER JOIN roles ON roles.id = employee_roles.role_id
        WHERE employees.user_id = ?
        ORDER BY roles.name
        """,
        (user_id,),
    ).fetchall()
    return {
        "user_id": row["id"],
        "employee_id": row["employee_id"],
        "username": _safe_text(row["username"], 80),
        "display_name": _safe_text(row["display_name"], 100),
        "role_names": [_safe_text(role["name"], 80) for role in roles[:20]],
    }


def _target_id():
    values = request.view_args or {}
    for key, value in values.items():
        if key.lower().endswith("id") or key.lower() in {"fund_id"}:
            return _safe_text(value, 100)
    return ""


def _target_from_response(response):
    if response.is_streamed or not response.is_json:
        return ""
    try:
        payload = response.get_json(silent=True)
    except (TypeError, ValueError):
        return ""
    if not isinstance(payload, dict):
        return ""
    for key in ("id", "employeeId", "accountId"):
        if payload.get(key) is not None:
            return _safe_text(payload[key], 100)
    for key in (
        "data", "employee", "order", "receipt", "account", "template",
        "record", "department",
    ):
        value = payload.get(key)
        if isinstance(value, dict) and value.get("id") is not None:
            return _safe_text(value["id"], 100)
    return ""


def _source_surface():
    requested = _safe_text(request.headers.get("X-Client-Surface"), 20).lower()
    if requested in {"admin", "touch", "web"}:
        return requested
    referrer_path = _safe_text(request.referrer, 500)
    if "/main" in referrer_path:
        return "touch"
    if "/admin" in referrer_path:
        return "admin"
    actor = getattr(g, "operation_log_actor", None)
    if actor and not getattr(g, "operation_log_can_access_admin", True):
        return "touch"
    return "api"


def _insert_log(conn, event):
    actor = event.get("actor") or {}
    conn.execute(
        """
        INSERT INTO operation_logs (
            actor_user_id, actor_employee_id, actor_username, actor_display_name,
            actor_role_names, module_code, module_name, action_code, action_name,
            target_type, target_id, target_label, request_method, request_path,
            request_id, source_surface, ip_address, user_agent, status_code,
            succeeded, details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            actor.get("user_id"),
            actor.get("employee_id"),
            actor.get("username", ""),
            actor.get("display_name", ""),
            json.dumps(actor.get("role_names") or [], ensure_ascii=False),
            event["module_code"],
            event["module_name"],
            event["action_code"],
            event["action_name"],
            event.get("target_type", ""),
            _safe_text(event.get("target_id"), 100),
            _safe_text(event.get("target_label"), 200),
            _safe_text(event.get("request_method"), 12),
            _safe_text(event.get("request_path"), 300),
            _safe_text(event.get("request_id"), 100),
            _safe_text(event.get("source_surface"), 20),
            _safe_text(event.get("ip_address"), 80),
            _safe_text(event.get("user_agent"), 500),
            event.get("status_code"),
            1 if event.get("succeeded") else 0,
            json.dumps(event.get("details") or {}, ensure_ascii=False),
        ),
    )


def insert_operation_log(
    conn,
    *,
    actor=None,
    module_code,
    action_code,
    target_type="",
    target_id="",
    target_label="",
    request_method="",
    request_path="",
    request_id="",
    source_surface="admin",
    ip_address="",
    user_agent="",
    status_code=200,
    succeeded=True,
    details=None,
):
    """Insert a sanitized operation log using the caller's transaction."""
    event = {
        "actor": actor,
        "module_code": module_code,
        "module_name": _MODULE_LABELS.get(module_code, module_code),
        "action_code": action_code,
        "action_name": _ACTION_NAMES.get(action_code, action_code),
        "target_type": target_type,
        "target_id": target_id,
        "target_label": target_label,
        "request_method": request_method,
        "request_path": request_path,
        "request_id": request_id,
        "source_surface": source_surface,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "status_code": status_code,
        "succeeded": succeeded,
        "details": details or {},
    }
    _insert_log(conn, event)


def register_operation_logging(app):
    @app.before_request
    def capture_operation_actor():
        rule = _matched_rule(request.path, request.method)
        if not rule or request.path == "/api/auth/login":
            return
        try:
            user = get_current_user()
            g.operation_log_actor = _actor_snapshot(user)
            g.operation_log_can_access_admin = bool(
                user and user.get("canAccessAdmin")
            )
        except Exception:
            g.operation_log_actor = None
            g.operation_log_can_access_admin = True
            current_app.logger.exception("Failed to snapshot operation-log actor")

    @app.after_request
    def write_operation_log(response):
        rule = _matched_rule(request.path, request.method)
        if not rule:
            return response

        action_code = _request_action(
            rule, request.path, request.method, response.status_code
        )
        actor = getattr(g, "operation_log_actor", None)
        details = _request_details()
        target_label = ""
        target_id = _target_id()
        if request.path == "/api/auth/login":
            attempted_username = _safe_text(
                (request.get_json(silent=True) or {}).get("username"), 80
            )
            if response.status_code < 400:
                target_id = str(session.get("user_id") or "")
            else:
                target_label = attempted_username
        elif action_code == "create" and not target_id:
            target_id = _target_from_response(response)

        module_code = rule["module_code"]
        page_hint = _safe_text(
            request.headers.get("X-Client-Page"), 120
        )
        if not page_hint and request.referrer:
            from urllib.parse import urlsplit

            page_hint = urlsplit(request.referrer).path
        if (
            request.path.startswith("/api/orders")
            and page_hint == "/admin/sales/logistics"
        ):
            module_code = "logistics"
            rule = {**rule, "module_name": "物流管理", "target_type": "logistics_order"}

        event = {
            **rule,
            "module_code": module_code,
            "module_name": _MODULE_LABELS.get(module_code, rule["module_name"]),
            "action_code": action_code,
            "action_name": _ACTION_NAMES.get(action_code, action_code),
            "actor": actor,
            "target_id": target_id,
            "target_label": target_label,
            "request_method": request.method,
            "request_path": request.path,
            "request_id": _safe_text(
                request.headers.get("X-Request-ID"), 100
            ) or uuid.uuid4().hex,
            "source_surface": _source_surface(),
            "ip_address": _client_ip(),
            "user_agent": _safe_text(request.headers.get("User-Agent"), 500),
            "status_code": response.status_code,
            "succeeded": response.status_code < 400,
            "details": details,
        }
        if request.path == "/api/auth/login" and response.status_code < 400:
            event["actor"] = None

        try:
            with get_db() as conn:
                if request.path == "/api/auth/login" and response.status_code < 400:
                    event["actor"] = _actor_for_session(conn)
                _insert_log(conn, event)
        except Exception:
            current_app.logger.exception(
                "Failed to persist operation log for %s %s",
                request.method,
                request.path,
            )
        return response
