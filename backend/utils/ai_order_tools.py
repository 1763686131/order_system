"""Read-only GuGu tools backed by the authenticated order API views."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
import sqlite3

from flask import current_app, make_response

from utils.auth import get_current_user, permission_granted
from utils.db_helper import read_stores


ORDER_READ_PERMISSION = "touch.order.read"
MAX_PAGE_SIZE = 20
MAX_DETAIL_ITEMS = 20
STATUS_LABELS = {
    "pending": "未完成",
    "completed": "已完成",
    "shipped": "已发货",
}
QUERY_PROPERTIES = {
    "keyword": {"type": "string", "description": "单号、客户、商品、联系人、电话、地址、项目或物流单号关键词"},
    "orderNumber": {"type": "string", "description": "完整订单编号，精确匹配"},
    "customerName": {"type": "string", "description": "客户名称，包含匹配"},
    "storeName": {"type": "string", "description": "门店名称，包含匹配，不要猜测门店 ID"},
    "storeId": {"type": "integer", "minimum": 1},
    "startDate": {"type": "string", "description": "订单日期起始日，YYYY-MM-DD，含当日"},
    "endDate": {"type": "string", "description": "订单日期结束日，YYYY-MM-DD，含当日"},
    "status": {"type": "string", "enum": list(STATUS_LABELS)},
    "auditState": {"type": "integer", "enum": [0, 1, 2], "description": "0 未过账，1 已过账，2 已作废"},
    "limit": {"type": "integer", "minimum": 1, "maximum": MAX_PAGE_SIZE, "description": "默认 10"},
    "offset": {"type": "integer", "minimum": 0, "maximum": 10000, "description": "分页跳过条数，默认 0"},
}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_orders",
            "description": (
                "查询当前账号可见的销售/物流订单，按日期和 ID 倒序，"
                "支持组合筛选及分页；返回全部匹配订单的数量、状态计数和本单应收合计，"
                "不能把本页明细当成全部结果。未完成=pending，已完成=completed，"
                "已发货=shipped，已过账另用 auditState=1。"
            ),
            "parameters": {"type": "object", "properties": QUERY_PROPERTIES, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_detail",
            "description": "用查询结果中的订单 ID 读取当前账号可见的订单详情；不能猜测 ID。",
            "parameters": {
                "type": "object",
                "properties": {"orderId": {"type": "integer", "minimum": 1}},
                "required": ["orderId"],
                "additionalProperties": False,
            },
        },
    },
]


def can_query_orders():
    user = get_current_user()
    return bool(user and user.get("canAccessAdmin") and permission_granted(ORDER_READ_PERMISSION))


def available_tools():
    return TOOLS if can_query_orders() else []


def _text(value, limit=160):
    text = str(value if value is not None else "")
    return text if len(text) <= limit else text[:limit] + "…"


def _amount(value):
    if value is None or value == "":
        return None
    try:
        amount = Decimal(str(value))
        if amount.is_finite() and abs(amount) < Decimal("1e15"):
            return amount.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        pass
    return None


def _money(value):
    amount = _amount(value)
    return str(amount) if amount is not None else None


def _api_data(view, *args):
    response = make_response(view(*args))
    if response.status_code != 200:
        return None
    return response.get_json()


def _summary(order, stores):
    from routes.orders import order_store_id

    store_id = order_store_id(order)
    audit_state = order.get("audit_state") or 0
    return {
        "id": order["id"],
        "orderNumber": _text(order.get("order_number")),
        "date": _text(order.get("date"), 32),
        "customerName": _text(order.get("order_client")),
        "storeId": store_id,
        "storeName": _text(stores.get(store_id, "")),
        "status": order.get("status"),
        "statusLabel": STATUS_LABELS.get(order.get("status"), "未知"),
        "auditState": audit_state,
        "goods": _text(order.get("goods_name"), 240),
        "receivableAmount": _money(order.get("should_receive")),
    }


def _validate_arguments(name, arguments):
    if not isinstance(arguments, dict):
        raise ValueError("工具参数必须是 JSON 对象")
    properties = QUERY_PROPERTIES if name == "query_orders" else TOOLS[1]["function"]["parameters"]["properties"]
    if arguments.keys() - properties.keys():
        raise ValueError("包含不支持的查询参数")
    for key, value in arguments.items():
        rule = properties[key]
        if rule["type"] == "string":
            if not isinstance(value, str) or not value.strip() or len(value) > 160:
                raise ValueError(f"{key} 必须是 1 至 160 个字符的文字")
            arguments[key] = value = value.strip()
        elif type(value) is not int or not rule.get("minimum", 0) <= value <= rule.get("maximum", 2147483647):
            raise ValueError(f"{key} 必须是允许范围内的整数")
        if "enum" in rule and value not in rule["enum"]:
            raise ValueError(f"{key} 不在允许的选项内")
        if key in ("startDate", "endDate"):
            if date.fromisoformat(value).isoformat() != value:
                raise ValueError("日期须为 YYYY-MM-DD")
    if name == "get_order_detail" and "orderId" not in arguments:
        raise ValueError("必须提供订单 ID")
    if arguments.get("startDate", "") > arguments.get("endDate", "9999-12-31"):
        raise ValueError("起始日期不能晚于结束日期")


def _query_orders(arguments):
    from routes.orders import get_orders, order_store_id

    orders = _api_data(get_orders)
    if not isinstance(orders, list):
        return {"success": False, "code": "permission_denied", "message": "当前账号无法读取订单"}
    stores = {store["id"]: store.get("name", "") for store in read_stores()}
    matches = []
    for order in orders:
        if "orderNumber" in arguments and str(order.get("order_number") or "").casefold() != arguments["orderNumber"].casefold():
            continue
        if "customerName" in arguments and arguments["customerName"].casefold() not in str(order.get("order_client") or "").casefold():
            continue
        if "storeId" in arguments and order_store_id(order) != arguments["storeId"]:
            continue
        if "storeName" in arguments and arguments["storeName"].casefold() not in stores.get(order_store_id(order), "").casefold():
            continue
        if "status" in arguments and order.get("status") != arguments["status"]:
            continue
        if "auditState" in arguments and int(order.get("audit_state") or 0) != arguments["auditState"]:
            continue
        order_date = str(order.get("date") or "")[:10]
        if "startDate" in arguments and order_date < arguments["startDate"]:
            continue
        if "endDate" in arguments and (not order_date or order_date > arguments["endDate"]):
            continue
        if "keyword" in arguments:
            fields = (
                "id", "order_number", "order_client", "goods_name", "contact_person",
                "receiver_name", "contact_phone", "receiver_phone", "contact_address",
                "receiver_address", "project_name", "logistics_no",
            )
            values = [str(order.get(field) or "") for field in fields]
            goods = order.get("order_goods")
            if isinstance(goods, list):
                values.extend(str(item.get("goods_name") or "") for item in goods if isinstance(item, dict))
            if not any(arguments["keyword"].casefold() in value.casefold() for value in values):
                continue
        matches.append(order)
    matches.sort(key=lambda order: (str(order.get("date") or ""), order["id"]), reverse=True)
    offset, limit = arguments.get("offset", 0), arguments.get("limit", 10)
    page = matches[offset:offset + limit]
    amounts = [_amount(order.get("should_receive")) for order in matches]
    known_amounts = [amount for amount in amounts if amount is not None]
    return {
        "success": True,
        "queriedAt": datetime.now().isoformat(timespec="seconds"),
        "filters": arguments,
        "total": len(matches),
        "offset": offset,
        "returned": len(page),
        "hasMore": offset + len(page) < len(matches),
        "summary": {
            "statusCounts": {status: sum(order.get("status") == status for order in matches) for status in STATUS_LABELS},
            "receivableTotal": str(sum(known_amounts, Decimal("0.00"))) if known_amounts or not matches else None,
            "receivableOrderCount": len(known_amounts),
            "amountNote": "全部匹配订单中已有本单应收字段的合计；不是已收款或客户实时应收余额。",
        },
        "orders": [_summary(order, stores) for order in page],
    }


def _get_order_detail(arguments):
    from routes.orders import get_order

    order = _api_data(get_order, arguments["orderId"])
    if not isinstance(order, dict):
        return {"success": False, "code": "order_not_found", "message": "订单不存在或不在当前账号可见范围内"}
    stores = {store["id"]: store.get("name", "") for store in read_stores()}
    detail = _summary(order, stores)
    for field in ("completed_date", "shipped_date", "contact_person", "contact_phone", "contact_address",
                  "receiver_name", "receiver_phone", "receiver_address", "project_name", "sales_person",
                  "creator", "logistics_no", "shipping_method", "shipping_custom", "remark"):
        detail[field] = _text(order.get(field))
    for field in ("subtotal_amount", "tax_amount", "total_amount", "discount_amount",
                  "other_fees", "current_payment", "balance_applied", "current_debt"):
        detail[field] = _money(order.get(field))
    goods = order.get("order_goods")
    goods = [item for item in goods if isinstance(item, dict)] if isinstance(goods, list) else []
    fields = ("goods_name", "spec", "unit", "quantity", "packages", "price", "amount", "total_amount")
    detail["items"] = [{field: _text(item.get(field), 120) for field in fields} for item in goods[:MAX_DETAIL_ITEMS]]
    detail["itemCount"] = len(goods)
    detail["itemsTruncated"] = len(goods) > MAX_DETAIL_ITEMS
    detail["amountNote"] = "金额是订单自身保存的快照，不代表客户实时应收或后续全部收款。"
    return {"success": True, "queriedAt": datetime.now().isoformat(timespec="seconds"), "order": detail}


def execute_tool(name, raw_arguments):
    if name not in ("query_orders", "get_order_detail"):
        return {"success": False, "code": "unknown_tool", "message": "仅支持订单列表和详情查询"}
    if not can_query_orders():
        return {"success": False, "code": "permission_denied", "message": "当前账号没有订单读取权限"}
    try:
        if not isinstance(raw_arguments, str) or len(raw_arguments) > 4096:
            raise ValueError("查询参数格式不正确或过长")
        arguments = json.loads(raw_arguments)
        _validate_arguments(name, arguments)
        return _query_orders(arguments) if name == "query_orders" else _get_order_detail(arguments)
    except (ValueError, TypeError, OverflowError):
        return {"success": False, "code": "invalid_tool_arguments", "message": "查询条件不合法，请检查字段、日期和分页范围"}
    except sqlite3.Error:
        current_app.logger.exception("GuGu order query failed")
        return {"success": False, "code": "query_failed", "message": "订单查询暂时不可用，请稍后重试"}
