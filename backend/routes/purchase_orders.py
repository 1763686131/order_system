"""Purchase order master/detail and approval workflow APIs."""

import threading
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.notifications import create_audit_notifications, complete_audit_notifications
from utils.permission_catalog import ADMIN_PURCHASE_ORDER_PERMISSIONS
from utils.supplier_ledger import (
    FinanceError, balance, business_date, cents, check_scope, check_version, idempotent_result, save_operation, scope_sql, source_summary,
)


purchase_orders_bp = Blueprint("purchase_orders", __name__, url_prefix="/api")
_write_lock = threading.Lock()
_MONEY_QUANT = Decimal("0.01")
_STATUSES = {"draft", "pending", "approved", "partial", "completed", "cancelled", "rejected"}
_PAYMENT_METHODS = {"cash", "wechat", "acceptance", "bank_transfer", "other"}


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _text(value, limit=None):
    value = "" if value is None else str(value).strip()
    return value[:limit] if limit else value


def _number(value, default=Decimal("0")):
    if value in (None, ""):
        return default
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("数值格式不正确")
    if not number.is_finite():
        raise ValueError("数值必须是有限数字")
    return number


def _optional_int(value, field):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field}必须是整数")


def _required_int(value, field):
    parsed = _optional_int(value, field)
    if parsed is None:
        raise ValueError(f"请选择{field}")
    return parsed


def _status(value):
    value = _text(value or "draft").lower()
    if value not in _STATUSES:
        raise ValueError("采购订单状态无效")
    return value


def _product_table(product_type):
    if product_type == "finished-product":
        return "products"
    if product_type == "raw-material":
        return "raw_material_products"
    raise ValueError("商品分类无效")


def _product_exists(conn, product_type, product_id):
    return conn.execute(
        f"SELECT 1 FROM {_product_table(product_type)} WHERE id = ?", (product_id,)
    ).fetchone() is not None


def _normalize_items(conn, raw_items, existing_items=None, store_id=None):
    if raw_items is None:
        raw_items = existing_items or []
    if not isinstance(raw_items, list):
        raise ValueError("采购订单明细必须是数组")

    existing_by_id = {
        int(item["id"]): item
        for item in (existing_items or [])
        if item.get("id") is not None
    }
    normalized = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        existing_id = _optional_int(raw.get("id", raw.get("orderItemId")), "明细ID")
        existing = existing_by_id.get(existing_id or -1)
        product_type = _text(
            raw.get("productType", raw.get("product_type", existing.get("product_type") if existing else "raw-material"))
        ) or "raw-material"
        _product_table(product_type)
        product_id = _optional_int(raw.get("productId", raw.get("product_id", existing.get("product_id") if existing else None)), "商品ID")
        product_name = _text(
            raw.get("productName", raw.get("name", raw.get("product_name"))), 160
        )
        if product_id is None and not product_name:
            continue
        if product_id is not None:
            if not _product_exists(conn, product_type, product_id):
                raise ValueError(f"商品 ID {product_id} 不存在")
            product = conn.execute(
                f"""
                SELECT product.code, product.name, product.specification,
                       unit.name AS unit_name
                FROM {_product_table(product_type)} AS product
                LEFT JOIN units AS unit ON unit.id = product.unit_id
                WHERE product.id = ?
                """,
                (product_id,),
            ).fetchone()
            if product:
                product_name = product_name or product["name"] or ""
                product_code = _text(raw.get("productCode", raw.get("code")), 80) or (product["code"] or "")
                specification = _text(raw.get("specification", raw.get("spec")), 180) or (product["specification"] or "")
                unit = _text(raw.get("unit", raw.get("unitName")), 40) or (product["unit_name"] or "")
            else:
                product_code = _text(raw.get("productCode", raw.get("code")), 80)
                specification = _text(raw.get("specification", raw.get("spec")), 180)
                unit = _text(raw.get("unit", raw.get("unitName")), 40)
        else:
            product_code = _text(raw.get("productCode", raw.get("code")), 80)
            specification = _text(raw.get("specification", raw.get("spec")), 180)
            unit = _text(raw.get("unit", raw.get("unitName")), 40)

        ordered = _number(raw.get("orderedQty", raw.get("quantity", raw.get("qty"))))
        if ordered <= 0:
            raise ValueError("采购数量必须大于 0")
        price_value = raw.get("unitPrice", raw.get("price"))
        unit_price = None if price_value in (None, "") else _number(price_value)
        if unit_price is not None and unit_price < 0:
            raise ValueError("采购单价不能为负数")
        amount_value = raw.get("amount", raw.get("totalAmount"))
        amount = (
            _number(amount_value)
            if amount_value not in (None, "")
            else (ordered * unit_price).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
            if unit_price is not None
            else None
        )
        if amount is not None and amount < 0:
            raise ValueError("采购金额不能为负数")
        warehouse_value = raw.get(
            "warehouseId",
            raw.get("warehouse_id", existing.get("warehouse_id") if existing else None),
        )
        warehouse_id = _optional_int(warehouse_value, "明细仓库ID")
        if warehouse_id is not None:
            warehouse = conn.execute(
                "SELECT store_id FROM warehouses WHERE id = ?", (warehouse_id,)
            ).fetchone()
            if warehouse is None:
                raise ValueError("明细仓库不存在")
            if store_id is not None and warehouse["store_id"] != store_id:
                raise ValueError("明细仓库必须属于申请门店")
        category_id = _optional_int(
            raw.get("categoryId", raw.get("category_id", existing.get("category_id") if existing else None)),
            "分类ID",
        )
        category_name = _text(
            raw.get("categoryName", raw.get("category_name", existing.get("category_name") if existing else "")), 120
        )
        if category_id is not None:
            if warehouse_id is None:
                raise ValueError("选择分类前请先选择仓库")
            warehouse_row = conn.execute(
                "SELECT categories FROM warehouses WHERE id = ?", (warehouse_id,)
            ).fetchone()
            try:
                categories = json.loads(warehouse_row["categories"] or "[]") if warehouse_row else []
            except (TypeError, ValueError):
                categories = []
            category = next((entry for entry in categories if str(entry.get("id")) == str(category_id)), None)
            if not category:
                raise ValueError("明细分类必须属于所选仓库")
            category_name = category_name or _text(category.get("name"), 120)
        supplier_value = raw.get(
            "supplierId",
            raw.get("supplier_id", existing.get("supplier_id") if existing else None),
        )
        supplier_id = _optional_int(supplier_value, "明细供应商ID")
        if supplier_id is not None and not conn.execute(
            "SELECT 1 FROM suppliers WHERE id = ? AND status = 'active'", (supplier_id,)
        ).fetchone():
            raise ValueError("明细供应商不存在或已停用")
        received = _number(existing.get("received_qty", 0) if existing else 0)
        supplied_received = raw.get("receivedQty", raw.get("received_qty"))
        if supplied_received not in (None, "") and _number(supplied_received) != received:
            raise ValueError("已入库数量只能由入库审核更新")
        normalized.append(
            {
                "id": existing_id,
                "line_no": len(normalized) + 1,
                "product_type": product_type,
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "category_id": category_id,
                "category_name": category_name,
                "supplier_id": supplier_id,
                "product_code": product_code,
                "product_name": product_name,
                "specification": specification,
                "unit": unit,
                "ordered_qty": float(ordered),
                "received_qty": float(received),
                "unit_price": float(unit_price) if unit_price is not None else None,
                "amount": float(amount) if amount is not None else None,
                "remark": _text(raw.get("remark"), 500),
            }
        )
    if not normalized:
        raise ValueError("至少添加一条采购明细")
    return normalized


def _order_values(conn, data, existing=None):
    existing = existing or {}
    order_date = business_date(data.get("orderDate", data.get("order_date", existing.get("order_date"))))
    supplier_value = data.get("supplierId", data.get("supplier_id", existing.get("supplier_id")))
    supplier_id = _optional_int(supplier_value, "供应商ID")
    if supplier_id is not None and not conn.execute(
        "SELECT 1 FROM suppliers WHERE id = ? AND status = 'active'", (supplier_id,)
    ).fetchone():
        raise ValueError("供应商不存在或已停用")
    requested_status = _status(data.get("status", existing.get("status", "draft")))
    if requested_status not in ("draft", "pending"):
        raise ValueError("新建或编辑采购订单只能保存为草稿或待审核")
    store_id = _optional_int(data.get("storeId", data.get("store_id", existing.get("store_id"))), "门店ID")
    if store_id is None or not conn.execute('SELECT 1 FROM stores WHERE id = ?', (store_id,)).fetchone():
        raise ValueError("请选择有效申请门店")
    check_scope(store_id)
    items = _normalize_items(conn, data.get("items"), existing.get("_items"), store_id)
    # Keep existing callers that submit one master supplier compatible.
    if supplier_id is not None:
        for item in items:
            if item["supplier_id"] is None:
                item["supplier_id"] = supplier_id
    item_suppliers = {item["supplier_id"] for item in items if item["supplier_id"] is not None}
    supplier_id = (
        next(iter(item_suppliers))
        if len(item_suppliers) == 1 and all(item["supplier_id"] is not None for item in items)
        else None
    )
    total_quantity = sum(Decimal(str(item["ordered_qty"])) for item in items)
    total_amount = sum(
        (Decimal(str(item["amount"])) for item in items if item["amount"] is not None),
        Decimal("0"),
    ).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    payment_value = data.get("paymentAmount", data.get("payment_amount", existing.get("payment_amount")))
    payment_amount = total_amount if payment_value in (None, "") else _number(payment_value).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    other_fees = _number(data.get("otherFees", data.get("other_fees", existing.get("other_fees", 0)))).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    current_payment = _number(
        data.get("currentPayment", data.get("current_payment", existing.get("current_payment", 0)))
    ).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    invoice_required = data.get("invoiceRequired", existing.get("invoice_required", False))
    if not isinstance(invoice_required, (bool, int)) or invoice_required not in (True, False, 0, 1):
        raise ValueError("需发票必须是布尔值")
    payment_method = _text(data.get("paymentMethod", existing.get("payment_method", ""))).lower()
    if payment_method and payment_method not in _PAYMENT_METHODS:
        raise ValueError("付款方式无效")
    payment_account_id = _optional_int(
        data.get("paymentAccountId", existing.get("payment_account_id")),
        "对公账户ID",
    )
    if payment_amount is not None and payment_amount < 0:
        raise ValueError("折后金额不能为负数")
    if other_fees < 0:
        raise ValueError("其它费用不能为负数")
    if current_payment < 0:
        raise ValueError("已付金额不能为负数")
    payable = (payment_amount if payment_amount is not None else total_amount) + other_fees
    if current_payment > payable:
        raise ValueError("已付金额不能大于折后金额与其它费用合计")
    if current_payment > 0 and not payment_method:
        raise ValueError("填写已付金额时请选择付款方式")
    settlement_account = _text(
        data.get("settlementAccount", data.get("settlement_account", existing.get("settlement_account"))),
        160,
    )
    if payment_method == "bank_transfer":
        if current_payment > 0 and payment_account_id is None:
            raise ValueError("请选择对公付款账户")
        if payment_account_id is not None:
            account = conn.execute(
                "SELECT account_name FROM bank_accounts WHERE id = ? AND store_id = ?",
                (payment_account_id, store_id),
            ).fetchone()
            if not account:
                raise ValueError("对公付款账户不存在或不属于申请门店")
            settlement_account = account["account_name"]
    else:
        payment_account_id = None
    if payment_method == "other" and current_payment > 0 and not settlement_account:
        raise ValueError("请填写其它付款方式说明")
    return {
        "order_no": _text(data.get("orderNo", data.get("order_no", existing.get("order_no"))), 80),
        "order_date": order_date,
        "expected_date": _text(data.get("expectedDate", data.get("expected_date", existing.get("expected_date"))), 20),
        "store_id": store_id,
        "supplier_id": supplier_id,
        "remark": _text(data.get("remark", existing.get("remark")), 500),
        "purchaser": _text(data.get("purchaser", existing.get("purchaser")), 80),
        "creator": _text(data.get("creator", existing.get("creator")), 80),
        "payment_amount": float(payment_amount) if payment_amount is not None else None,
        "other_fees": float(other_fees),
        "settlement_account": settlement_account,
        "current_payment": float(current_payment),
        "invoice_required": int(bool(invoice_required)),
        "payment_method": payment_method,
        "payment_account_id": payment_account_id,
        "status": requested_status,
        "items": items,
        "total_quantity": float(total_quantity),
        "total_amount": float(total_amount),
    }


def _supplier_payable(conn, supplier_ids):
    supplier_ids = sorted({int(supplier_id) for supplier_id in supplier_ids if supplier_id is not None})
    if not supplier_ids:
        return 0.0
    return sum(balance(conn, supplier_id)["payableBalance"] for supplier_id in supplier_ids)


def _serialize_item(row):
    item = dict(row)
    ordered = float(item.pop("ordered_qty", 0) or 0)
    received = float(item.pop("received_qty", 0) or 0)
    amount = item.pop("amount", None)
    item["orderItemId"] = item.pop("id", None)
    item["productId"] = item.pop("product_id", None)
    item["warehouseId"] = item.pop("warehouse_id", None)
    item["warehouseName"] = ""
    supplier_id = item.pop("supplier_id", None)
    item["productType"] = item.pop("product_type", "raw-material")
    item["categoryId"] = item.pop("category_id", None)
    item["categoryName"] = item.pop("category_name", "") or ""
    item["productCode"] = item.pop("product_code", "") or ""
    item["productName"] = item.pop("product_name", "") or ""
    item["specification"] = item.pop("specification", "") or ""
    item["unit"] = item.pop("unit", "") or ""
    item["orderedQty"] = ordered
    item["receivedQty"] = received
    item["remainingQty"] = max(0, ordered - received)
    item["overReceivedQty"] = max(0, received - ordered)
    item["fulfillmentProgress"] = min(100, round(received / ordered * 100, 2)) if ordered else 0
    item["unitPrice"] = item.pop("unit_price", None)
    item["amount"] = amount
    item["supplierId"] = supplier_id
    item["supplierName"] = ""
    return item


def _serialize_order(conn, row, include_items=True):
    order = dict(row)
    supplier = conn.execute(
        "SELECT supplier_name FROM suppliers WHERE id = ?", (row["supplier_id"],)
    ).fetchone()
    order["orderId"] = order.pop("id", None)
    order["orderNo"] = order.pop("order_no", "")
    order["orderDate"] = order.pop("order_date", "")
    order["expectedDate"] = order.pop("expected_date", "") or ""
    order["storeId"] = order.pop("store_id", None)
    order["supplierId"] = order.pop("supplier_id", None)
    order["supplierName"] = supplier["supplier_name"] if supplier else ""
    order["purchaser"] = order.pop("purchaser", "") or ""
    order["creator"] = order.pop("creator", "") or ""
    order["paymentAmount"] = order.pop("payment_amount", None)
    order["otherFees"] = order.pop("other_fees", 0) or 0
    order["settlementAccount"] = order.pop("settlement_account", "") or ""
    order["currentPayment"] = order.pop("current_payment", 0) or 0
    order["paidAmount"] = order["currentPayment"]
    order["invoiceRequired"] = bool(order.pop("invoice_required", 0))
    order["paymentMethod"] = order.pop("payment_method", "") or ""
    order["paymentAccountId"] = order.pop("payment_account_id", None)
    order["totalQuantity"] = order.pop("total_quantity", 0) or 0
    order["totalAmount"] = order.pop("total_amount", 0) or 0
    order["auditedBy"] = order.pop("audited_by", "") or ""
    order["auditedAt"] = order.pop("audited_at", None)
    order["createdBy"] = order.pop("created_by", "") or ""
    order["createdAt"] = order.pop("created_at", "") or ""
    order["updatedAt"] = order.pop("updated_at", "") or ""
    order["inboundDeletedAt"] = order.pop("inbound_deleted_at", None)
    if include_items:
        items = conn.execute(
            "SELECT * FROM purchase_order_items WHERE order_id = ? ORDER BY line_no, id",
            (row["id"],),
        ).fetchall()
        order["items"] = [_serialize_item(item) for item in items]
        supplier_ids = [item["supplierId"] for item in order["items"] if item["supplierId"] is not None]
        supplier_rows = {}
        if supplier_ids:
            placeholders = ",".join("?" for _ in set(supplier_ids))
            supplier_rows = {
                row["id"]: row["supplier_name"]
                for row in conn.execute(
                    f"SELECT id, supplier_name FROM suppliers WHERE id IN ({placeholders})",
                    tuple(sorted(set(supplier_ids))),
                ).fetchall()
            }
        for item in order["items"]:
            item["supplierName"] = supplier_rows.get(item["supplierId"], "")
        warehouse_ids = {item["warehouseId"] for item in order["items"] if item["warehouseId"] is not None}
        warehouse_rows = {}
        if warehouse_ids:
            placeholders = ",".join("?" for _ in warehouse_ids)
            warehouse_rows = {
                warehouse["id"]: warehouse["name"]
                for warehouse in conn.execute(
                    f"SELECT id, name FROM warehouses WHERE id IN ({placeholders})",
                    tuple(sorted(warehouse_ids)),
                ).fetchall()
            }
        for item in order["items"]:
            item["warehouseName"] = warehouse_rows.get(item["warehouseId"], "")
        if not order["supplierName"]:
            order["supplierName"] = "、".join(dict.fromkeys(
                item["supplierName"] for item in order["items"] if item["supplierName"]
            ))
        order["orderItems"] = order["items"]
    selected_supplier_ids = [
        item["supplierId"] for item in order.get("items", [])
        if item.get("supplierId") is not None
    ]
    order_payable_base = (
        float(order["paymentAmount"])
        if order["paymentAmount"] is not None
        else float(order["totalAmount"] or 0)
    )
    order["estimatedAmount"] = max(0.0, order_payable_base + float(order["otherFees"] or 0))
    order.update(source_summary(conn, "purchase_order_id", row["id"]))
    order["orderPayable"] = order["confirmedPayable"]
    order["currentPayable"] = (
        order["unpaidAmount"] if order["payableCount"] else
        max(0.0, round(order["estimatedAmount"] - float(order["currentPayment"]), 2))
    )
    order["unpaidAmount"] = order["currentPayable"]
    if not order["payableCount"]:
        order["invoiceStatus"] = "unbilled" if order["invoiceRequired"] else "not_required"
        order["paymentStatus"] = (
            "paid" if order["currentPayable"] <= 0 else
            "partial" if order["currentPayment"] > 0 else "unpaid"
        )
    order["supplierPayable"] = _supplier_payable(conn, selected_supplier_ids)
    items = order.get("items", [])
    units = {item["unit"] for item in items}
    order["progressBasis"] = "quantity" if len(units) == 1 else "lines"
    order["completedLineCount"] = sum(item["remainingQty"] <= 0.0000001 for item in items)
    order["totalLineCount"] = len(items)
    order["receivedQuantity"] = sum(item["receivedQty"] for item in items)
    order["inboundCount"] = conn.execute(
        "SELECT COUNT(*) AS count FROM stock_inbounds WHERE purchase_order_id = ?",
        (row["id"],),
    ).fetchone()["count"]
    order["hasInbound"] = order["inboundCount"] > 0
    order["fulfillmentProgress"] = min(100, round(
        (order["receivedQuantity"] / order["totalQuantity"] if order["progressBasis"] == "quantity" and order["totalQuantity"]
         else order["completedLineCount"] / len(items) if items else 0) * 100, 2))
    return order


def _existing_values(conn, order_id):
    row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        return None, None
    values = dict(row)
    values["_items"] = [
        dict(item)
        for item in conn.execute(
            "SELECT * FROM purchase_order_items WHERE order_id = ? ORDER BY line_no, id", (order_id,)
        ).fetchall()
    ]
    return row, values


def _insert_items(conn, order_id, items):
    for item in items:
        cursor = conn.execute(
            """
            INSERT INTO purchase_order_items (
                order_id, line_no, product_type, product_id, product_code, product_name,
                supplier_id, warehouse_id, category_id, category_name, specification, unit,
                ordered_qty, received_qty, unit_price, amount, remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id, item["line_no"], item["product_type"], item["product_id"],
                item["product_code"], item["product_name"], item["supplier_id"], item["warehouse_id"],
                item["category_id"], item["category_name"], item["specification"], item["unit"],
                item["ordered_qty"], item["received_qty"], item["unit_price"], item["amount"], item["remark"],
            ),
        )
        item["id"] = cursor.lastrowid


def _validate_audit_items(conn, items, store_id):
    if not items:
        raise ValueError("采购订单没有有效明细")
    if any(float(item.get("ordered_qty") or 0) <= 0 for item in items):
        raise ValueError("采购数量必须大于 0")
    if any(item.get("supplier_id") is None for item in items):
        raise ValueError("审核前请为每项物料补充采购供应商")
    if any(item.get("unit_price") is None for item in items):
        raise ValueError("审核前请为每项物料补充采购单价")
    supplier_ids = {int(item["supplier_id"]) for item in items}
    placeholders = ",".join("?" for _ in supplier_ids)
    active_supplier_count = conn.execute(
        f"SELECT COUNT(*) AS count FROM suppliers WHERE status = 'active' AND id IN ({placeholders}) "
        "AND (store_id IS NULL OR store_id = ?)",
        (*sorted(supplier_ids), store_id),
    ).fetchone()["count"]
    if active_supplier_count != len(supplier_ids):
        raise ValueError("采购明细中存在不存在或已停用的供应商")
    return next(iter(supplier_ids)) if len(supplier_ids) == 1 else None


def _make_order_no(order_date, order_id):
    return f"CG{str(order_date).replace('-', '')[:8]}{int(order_id):04d}"


def _reverse_order_bank_payment(conn, order_id):
    original = conn.execute(
        """SELECT t.* FROM bank_account_transactions t
           WHERE t.source_type = 'purchase_order_payment' AND t.source_id = ?
             AND t.reversal_of_id IS NULL
             AND NOT EXISTS (
                 SELECT 1 FROM bank_account_transactions r WHERE r.reversal_of_id = t.id
             )
           ORDER BY t.id DESC LIMIT 1""",
        (order_id,),
    ).fetchone()
    if not original:
        return
    account = conn.execute(
        "SELECT * FROM bank_accounts WHERE id = ? AND store_id = ?",
        (original["bank_account_id"], original["store_id"]),
    ).fetchone()
    if not account:
        raise FinanceError("原对公账户不存在，无法冲销付款", 409)
    balance_cents = cents(account["balance"], nonnegative=False)
    restored_cents = balance_cents - original["delta_cents"]
    reversal_date = max(_now()[:10], original["business_date"])
    conn.execute(
        """INSERT INTO bank_account_transactions (
            bank_account_id, store_id, business_date, source_type, source_id, document_no,
            document_version, delta_cents, balance_after_cents, created_by, created_at, reversal_of_id
        ) VALUES (?, ?, ?, 'purchase_order_payment', ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            account["id"], original["store_id"], reversal_date, order_id, original["document_no"],
            original["document_version"], -original["delta_cents"], restored_cents,
            current_identity(), _now(), original["id"],
        ),
    )
    conn.execute(
        "UPDATE bank_accounts SET balance = ?, updated_at = ? WHERE id = ?",
        (float(Decimal(restored_cents) / 100), _now(), account["id"]),
    )


def _post_order_bank_payment(conn, order):
    payment_cents = cents(order["current_payment"])
    if order["payment_method"] != "bank_transfer" or payment_cents <= 0:
        return
    account = conn.execute(
        "SELECT * FROM bank_accounts WHERE id = ? AND store_id = ?",
        (order["payment_account_id"], order["store_id"]),
    ).fetchone()
    if not account:
        raise FinanceError("对公付款账户不存在或不属于申请门店", 409)
    balance_cents = cents(account["balance"], nonnegative=False)
    if balance_cents < payment_cents:
        raise FinanceError("对公账户余额不足，无法入账", 409)
    balance_after = balance_cents - payment_cents
    business_date = order["order_date"]
    conn.execute(
        """INSERT INTO bank_account_transactions (
            bank_account_id, store_id, business_date, source_type, source_id, document_no,
            document_version, delta_cents, balance_after_cents, created_by, created_at
        ) VALUES (?, ?, ?, 'purchase_order_payment', ?, ?, ?, ?, ?, ?, ?)""",
        (
            account["id"], order["store_id"], business_date, order["id"], order["order_no"],
            order["version"], -payment_cents, balance_after, current_identity(), _now(),
        ),
    )
    conn.execute(
        "UPDATE bank_accounts SET balance = ?, updated_at = ? WHERE id = ?",
        (float(Decimal(balance_after) / 100), _now(), account["id"]),
    )


@purchase_orders_bp.route("/purchase-orders", methods=["GET"])
def list_purchase_orders():
    requested_status = _text(request.args.get("status"))
    try:
        if requested_status:
            requested_status = _status(requested_status)
        with get_db() as conn:
            sql = "SELECT * FROM purchase_orders WHERE 1 = 1"
            scoped, params = scope_sql(alias="purchase_orders")
            sql += scoped
            if requested_status:
                sql += " AND status = ?"
                params.append(requested_status)
            sql += " ORDER BY order_date DESC, id DESC"
            rows = conn.execute(sql, params).fetchall()
            return jsonify([_serialize_order(conn, row) for row in rows])
    except FinanceError as exc:
        return jsonify({"success": False, "message": str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@purchase_orders_bp.route("/purchase-orders/<int:order_id>", methods=["GET"])
def get_purchase_order(order_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "采购订单不存在"}), 404
        try:
            check_scope(row["store_id"])
        except FinanceError as exc:
            return jsonify({"success": False, "message": str(exc)}), exc.status
        return jsonify(_serialize_order(conn, row))


@purchase_orders_bp.route("/purchase-orders/<int:order_id>/available-inbound", methods=["GET"])
def get_available_inbound(order_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "采购订单不存在"}), 404
        if row["status"] not in ("approved", "partial"):
            return jsonify({"success": False, "message": "采购订单未审核或已完成入库，不能创建补充入库"}), 409
        try:
            check_scope(row["store_id"])
        except FinanceError as exc:
            return jsonify({"success": False, "message": str(exc)}), exc.status
        order = _serialize_order(conn, row)
        first_inbound = conn.execute(
            "SELECT document_no FROM stock_inbounds WHERE purchase_order_id = ? ORDER BY id LIMIT 1",
            (order_id,),
        ).fetchone()
        order["inboundDocumentNo"] = first_inbound["document_no"] if first_inbound else ""
        return jsonify(order)


@purchase_orders_bp.route("/purchase-orders", methods=["POST"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["create"])
def create_purchase_order():
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                values = _order_values(conn, data)
                now = _now()
                cursor = conn.execute(
                    """
                    INSERT INTO purchase_orders (
                        order_no, order_date, expected_date, store_id, supplier_id, remark,
                        purchaser, creator, payment_amount, other_fees, settlement_account,
                        current_payment, invoice_required, payment_method, payment_account_id,
                        status, total_quantity, total_amount, created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        values["order_no"] or f"TEMP-{now.replace(' ', '').replace(':', '').replace('-', '')}",
                        values["order_date"], values["expected_date"], values["store_id"], values["supplier_id"],
                        values["remark"], values["purchaser"], values["creator"], values["payment_amount"],
                        values["other_fees"], values["settlement_account"], values["current_payment"],
                        values["invoice_required"], values["payment_method"], values["payment_account_id"],
                        values["status"], values["total_quantity"], values["total_amount"],
                        current_identity(), now, now,
                    ),
                )
                order_id = cursor.lastrowid
                if not values["order_no"]:
                    conn.execute(
                        "UPDATE purchase_orders SET order_no = ? WHERE id = ?",
                        (_make_order_no(values["order_date"], order_id), order_id),
                    )
                _insert_items(conn, order_id, values["items"])
                row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
                _post_order_bank_payment(conn, row)
                if values["status"] == "pending":
                    create_audit_notifications(
                        conn, "purchase_order", order_id, row["order_no"],
                        f"采购订单 {row['order_no']} 已提交，请及时审核。",
                    )
                return jsonify({"success": True, "id": order_id, "purchaseOrder": _serialize_order(conn, row)}), 201
    except FinanceError as exc:
        return jsonify({"success": False, "message": str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        if "UNIQUE constraint failed: purchase_orders.order_no" in str(exc):
            return jsonify({"success": False, "message": "采购订单号已存在"}), 409
        return jsonify({"success": False, "message": "采购订单保存失败", "detail": str(exc)}), 500


@purchase_orders_bp.route("/purchase-orders/<int:order_id>", methods=["PUT"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["edit"])
def update_purchase_order(order_id):
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row, existing = _existing_values(conn, order_id)
                if not row:
                    return jsonify({"success": False, "message": "采购订单不存在"}), 404
                if row["status"] not in ("draft", "pending"):
                    return jsonify({"success": False, "message": "已审核或已入库的采购订单不能编辑"}), 409
                check_scope(row["store_id"])
                check_version(data, row)
                if conn.execute("SELECT 1 FROM purchase_expense_lines WHERE purchase_order_id = ?", (order_id,)).fetchone():
                    raise FinanceError("请先删除采购费用，再修改采购明细", 409)
                if any(float(item.get("received_qty") or 0) > 0 for item in existing["_items"]):
                    return jsonify({"success": False, "message": "已有入库数量的采购订单不能编辑"}), 409
                values = _order_values(conn, data, existing)
                now = _now()
                _reverse_order_bank_payment(conn, order_id)
                conn.execute(
                    """
                    UPDATE purchase_orders SET order_no = ?, order_date = ?, expected_date = ?, store_id = ?,
                        supplier_id = ?, remark = ?, purchaser = ?, creator = ?, payment_amount = ?,
                        other_fees = ?, settlement_account = ?, current_payment = ?, invoice_required = ?,
                        payment_method = ?, payment_account_id = ?, status = ?,
                        total_quantity = ?, total_amount = ?, updated_at = ?, version = version + 1
                    WHERE id = ?
                    """,
                    (
                        values["order_no"] or row["order_no"], values["order_date"], values["expected_date"],
                        values["store_id"], values["supplier_id"], values["remark"], values["purchaser"],
                        values["creator"], values["payment_amount"], values["other_fees"],
                        values["settlement_account"], values["current_payment"], values["invoice_required"],
                        values["payment_method"], values["payment_account_id"], values["status"],
                        values["total_quantity"], values["total_amount"], now, order_id,
                    ),
                )
                conn.execute("DELETE FROM purchase_order_items WHERE order_id = ?", (order_id,))
                _insert_items(conn, order_id, values["items"])
                updated = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
                _post_order_bank_payment(conn, updated)
                if row["status"] == "pending" and values["status"] != "pending":
                    complete_audit_notifications(conn, "purchase_order", order_id)
                if values["status"] == "pending":
                    create_audit_notifications(
                        conn, "purchase_order", order_id, updated["order_no"],
                        f"采购订单 {updated['order_no']} 已提交，请及时审核。",
                        event_version=f"submitted:{now}",
                    )
                return jsonify({"success": True, "purchaseOrder": _serialize_order(conn, updated)})
    except FinanceError as exc:
        return jsonify({"success": False, "message": str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        if "UNIQUE constraint failed: purchase_orders.order_no" in str(exc):
            return jsonify({"success": False, "message": "采购订单号已存在"}), 409
        return jsonify({"success": False, "message": "采购订单更新失败", "detail": str(exc)}), 500


@purchase_orders_bp.route("/purchase-orders/<int:order_id>", methods=["DELETE"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["delete"])
def delete_purchase_order(order_id):
    with _write_lock:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                return jsonify({"success": False, "message": "采购订单不存在"}), 404
            if row["status"] not in ("draft", "pending"):
                return jsonify({"success": False, "message": "已审核或已入库的采购订单不能删除"}), 409
            try:
                check_scope(row["store_id"])
                check_version(request.get_json(silent=True) or {}, row)
            except FinanceError as exc:
                return jsonify({"success": False, "message": str(exc)}), exc.status
            if conn.execute("SELECT 1 FROM stock_inbounds WHERE purchase_order_id = ?", (order_id,)).fetchone() or conn.execute(
                "SELECT 1 FROM purchase_expense_lines WHERE purchase_order_id = ?", (order_id,)
            ).fetchone():
                return jsonify({"success": False, "message": "订单已被入库或费用引用，不能删除"}), 409
            _reverse_order_bank_payment(conn, order_id)
            complete_audit_notifications(conn, "purchase_order", order_id)
            conn.execute("DELETE FROM purchase_order_items WHERE order_id = ?", (order_id,))
            conn.execute("DELETE FROM purchase_orders WHERE id = ?", (order_id,))
            return jsonify({"success": True, "deleted": True})


@purchase_orders_bp.route("/purchase-orders/<int:order_id>/audit", methods=["POST"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["audit"])
def audit_purchase_order(order_id):
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row, existing = _existing_values(conn, order_id)
                if not row:
                    return jsonify({"success": False, "message": "采购订单不存在"}), 404
                check_scope(row["store_id"])
                replay, token = idempotent_result(conn, f"purchase-order:{order_id}:audit", data)
                if replay:
                    return jsonify(replay)
                if row["status"] in ("approved", "partial", "completed"):
                    return jsonify(save_operation(conn, token, {
                        "success": True, "purchaseOrder": _serialize_order(conn, row),
                    }))
                if row["status"] != "pending":
                    return jsonify({"success": False, "message": "只有待审核采购订单可以审核"}), 409
                check_version(data, row)
                audit_items = existing["_items"]
                audit_values = None
                if data.get("items") is not None:
                    audit_values = _order_values(conn, {**data, "status": "pending"}, existing)
                    audit_items = audit_values["items"]
                master_supplier_id = _validate_audit_items(conn, audit_items, audit_values["store_id"] if audit_values else row["store_id"])
                if audit_values is not None:
                    now = _now()
                    _reverse_order_bank_payment(conn, order_id)
                    conn.execute(
                        """
                        UPDATE purchase_orders SET order_no = ?, order_date = ?, expected_date = ?,
                            store_id = ?, supplier_id = ?, remark = ?, purchaser = ?, creator = ?,
                            payment_amount = ?, other_fees = ?, settlement_account = ?, current_payment = ?,
                            invoice_required = ?, payment_method = ?, payment_account_id = ?,
                            status = ?, total_quantity = ?, total_amount = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            audit_values["order_no"] or row["order_no"], audit_values["order_date"],
                            audit_values["expected_date"], audit_values["store_id"], master_supplier_id,
                            audit_values["remark"], audit_values["purchaser"], audit_values["creator"],
                            audit_values["payment_amount"], audit_values["other_fees"],
                            audit_values["settlement_account"], audit_values["current_payment"],
                            audit_values["invoice_required"], audit_values["payment_method"],
                            audit_values["payment_account_id"],
                            "pending", audit_values["total_quantity"], audit_values["total_amount"], now, order_id,
                        ),
                    )
                    conn.execute("DELETE FROM purchase_order_items WHERE order_id = ?", (order_id,))
                    _insert_items(conn, order_id, audit_values["items"])
                now = _now()
                conn.execute(
                    "UPDATE purchase_orders SET status = 'approved', supplier_id = ?, audited_by = ?, audited_at = ?, updated_at = ?, version = version + 1 WHERE id = ?",
                    (master_supplier_id, current_identity(), now, now, order_id),
                )
                complete_audit_notifications(conn, "purchase_order", order_id)
                updated = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
                if audit_values is not None:
                    _post_order_bank_payment(conn, updated)
                return jsonify(save_operation(conn, token, {"success": True, "message": "采购订单审核成功", "purchaseOrder": _serialize_order(conn, updated)}))
    except FinanceError as exc:
        return jsonify({"success": False, "message": str(exc)}), exc.status
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "message": "采购订单审核失败", "detail": str(exc)}), 500


@purchase_orders_bp.route("/purchase-orders/<int:order_id>/audit", methods=["DELETE"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["reverse_audit"])
def reverse_audit_purchase_order(order_id):
    with _write_lock:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                return jsonify({"success": False, "message": "采购订单不存在"}), 404
            if row["status"] not in ("approved",):
                return jsonify({"success": False, "message": "当前采购订单不能反审核"}), 409
            try:
                check_scope(row["store_id"])
                check_version(request.get_json(silent=True) or {}, row)
            except FinanceError as exc:
                return jsonify({"success": False, "message": str(exc)}), exc.status
            if conn.execute("SELECT 1 FROM stock_inbounds WHERE purchase_order_id = ?", (order_id,)).fetchone() or conn.execute(
                "SELECT 1 FROM purchase_expense_lines WHERE purchase_order_id = ?", (order_id,)
            ).fetchone():
                return jsonify({"success": False, "message": "订单已被入库或费用引用，请先处理引用单据"}), 409
            received = conn.execute(
                "SELECT COALESCE(SUM(received_qty), 0) AS quantity FROM purchase_order_items WHERE order_id = ?",
                (order_id,),
            ).fetchone()["quantity"]
            if float(received or 0) > 0:
                return jsonify({"success": False, "message": "采购订单已有入库数量，不能反审核"}), 409
            now = _now()
            conn.execute(
                "UPDATE purchase_orders SET status = 'pending', audited_by = NULL, audited_at = NULL, updated_at = ?, version = version + 1 WHERE id = ?",
                (now, order_id),
            )
            updated = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
            create_audit_notifications(
                conn, "purchase_order", order_id, updated["order_no"],
                f"采购订单 {updated['order_no']} 已反审核，请重新审核。",
                event_version=f"reverse:{now}",
            )
            return jsonify({"success": True, "message": "采购订单已反审核", "purchaseOrder": _serialize_order(conn, updated)})
