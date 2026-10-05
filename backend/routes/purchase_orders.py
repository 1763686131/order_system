"""Purchase order master/detail and approval workflow APIs."""

import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.notifications import create_audit_notifications, complete_audit_notifications
from utils.permission_catalog import ADMIN_PURCHASE_ORDER_PERMISSIONS


purchase_orders_bp = Blueprint("purchase_orders", __name__, url_prefix="/api")
_write_lock = threading.Lock()
_MONEY_QUANT = Decimal("0.01")
_STATUSES = {"draft", "pending", "approved", "partial", "completed", "cancelled", "rejected"}


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


def _product_exists(conn, product_id):
    return conn.execute(
        "SELECT 1 FROM raw_material_products WHERE id = ?", (product_id,)
    ).fetchone() is not None


def _normalize_items(conn, raw_items, existing_items=None):
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
        product_id = _optional_int(raw.get("productId", raw.get("product_id")), "物料ID")
        product_name = _text(
            raw.get("productName", raw.get("name", raw.get("product_name"))), 160
        )
        if product_id is None and not product_name:
            continue
        if product_id is not None:
            if not _product_exists(conn, product_id):
                raise ValueError(f"原材料 ID {product_id} 不存在")
            product = conn.execute(
                """
                SELECT product.code, product.name, product.specification,
                       unit.name AS unit_name
                FROM raw_material_products AS product
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
        existing_id = _optional_int(raw.get("id", raw.get("orderItemId")), "明细ID")
        existing = existing_by_id.get(existing_id or -1)
        received = _number(
            raw.get("receivedQty", raw.get("received_qty", existing.get("received_qty", 0) if existing else 0))
        )
        if received < 0 or received > ordered:
            raise ValueError("已入库数量必须在 0 到采购数量之间")
        normalized.append(
            {
                "id": existing_id,
                "line_no": len(normalized) + 1,
                "product_type": "raw-material",
                "product_id": product_id,
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
    order_date = _text(data.get("orderDate", data.get("order_date", existing.get("order_date"))), 20)
    if not order_date:
        raise ValueError("请选择采购日期")
    supplier_id = _required_int(
        data.get("supplierId", data.get("supplier_id", existing.get("supplier_id"))), "供应商"
    )
    if not conn.execute(
        "SELECT 1 FROM suppliers WHERE id = ? AND status = 'active'", (supplier_id,)
    ).fetchone():
        raise ValueError("供应商不存在或已停用")
    requested_status = _status(data.get("status", existing.get("status", "draft")))
    if requested_status not in ("draft", "pending"):
        raise ValueError("新建或编辑采购订单只能保存为草稿或待审核")
    items = _normalize_items(conn, data.get("items"), existing.get("_items"))
    total_quantity = sum(Decimal(str(item["ordered_qty"])) for item in items)
    total_amount = sum(
        Decimal(str(item["amount"])) for item in items if item["amount"] is not None
    ).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
    return {
        "order_no": _text(data.get("orderNo", data.get("order_no", existing.get("order_no"))), 80),
        "order_date": order_date,
        "expected_date": _text(data.get("expectedDate", data.get("expected_date", existing.get("expected_date"))), 20),
        "store_id": _optional_int(data.get("storeId", data.get("store_id", existing.get("store_id"))), "门店ID"),
        "supplier_id": supplier_id,
        "remark": _text(data.get("remark", existing.get("remark")), 500),
        "status": requested_status,
        "items": items,
        "total_quantity": float(total_quantity),
        "total_amount": float(total_amount),
    }


def _serialize_item(row):
    item = dict(row)
    ordered = float(item.pop("ordered_qty", 0) or 0)
    received = float(item.pop("received_qty", 0) or 0)
    amount = item.pop("amount", None)
    item["orderItemId"] = item.pop("id", None)
    item["productId"] = item.pop("product_id", None)
    item["productType"] = item.pop("product_type", "raw-material")
    item["productCode"] = item.pop("product_code", "") or ""
    item["productName"] = item.pop("product_name", "") or ""
    item["specification"] = item.pop("specification", "") or ""
    item["unit"] = item.pop("unit", "") or ""
    item["orderedQty"] = ordered
    item["receivedQty"] = received
    item["remainingQty"] = max(0, ordered - received)
    item["unitPrice"] = item.pop("unit_price", None)
    item["amount"] = amount
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
    order["totalQuantity"] = order.pop("total_quantity", 0) or 0
    order["totalAmount"] = order.pop("total_amount", 0) or 0
    order["auditedBy"] = order.pop("audited_by", "") or ""
    order["auditedAt"] = order.pop("audited_at", None)
    order["createdBy"] = order.pop("created_by", "") or ""
    order["createdAt"] = order.pop("created_at", "") or ""
    order["updatedAt"] = order.pop("updated_at", "") or ""
    if include_items:
        items = conn.execute(
            "SELECT * FROM purchase_order_items WHERE order_id = ? ORDER BY line_no, id",
            (row["id"],),
        ).fetchall()
        order["items"] = [_serialize_item(item) for item in items]
        order["orderItems"] = order["items"]
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
                specification, unit, ordered_qty, received_qty, unit_price, amount, remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id, item["line_no"], item["product_type"], item["product_id"],
                item["product_code"], item["product_name"], item["specification"], item["unit"],
                item["ordered_qty"], item["received_qty"], item["unit_price"], item["amount"], item["remark"],
            ),
        )
        item["id"] = cursor.lastrowid


def _make_order_no(order_date, order_id):
    return f"CG{str(order_date).replace('-', '')[:8]}{int(order_id):04d}"


@purchase_orders_bp.route("/purchase-orders", methods=["GET"])
def list_purchase_orders():
    requested_status = _text(request.args.get("status"))
    try:
        if requested_status:
            requested_status = _status(requested_status)
        with get_db() as conn:
            sql = "SELECT * FROM purchase_orders WHERE 1 = 1"
            params = []
            if requested_status:
                sql += " AND status = ?"
                params.append(requested_status)
            sql += " ORDER BY order_date DESC, id DESC"
            rows = conn.execute(sql, params).fetchall()
            return jsonify([_serialize_order(conn, row) for row in rows])
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@purchase_orders_bp.route("/purchase-orders/<int:order_id>", methods=["GET"])
def get_purchase_order(order_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "采购订单不存在"}), 404
        return jsonify(_serialize_order(conn, row))


@purchase_orders_bp.route("/purchase-orders/<int:order_id>/available-inbound", methods=["GET"])
def get_available_inbound(order_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "采购订单不存在"}), 404
        if row["status"] not in ("approved", "partial"):
            return jsonify({"success": False, "message": "采购订单尚未审核，不能创建入库单"}), 409
        return jsonify(_serialize_order(conn, row))


@purchase_orders_bp.route("/purchase-orders", methods=["POST"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["create"])
def create_purchase_order():
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                values = _order_values(conn, data)
                now = _now()
                cursor = conn.execute(
                    """
                    INSERT INTO purchase_orders (
                        order_no, order_date, expected_date, store_id, supplier_id, remark,
                        status, total_quantity, total_amount, created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        values["order_no"] or f"TEMP-{now.replace(' ', '').replace(':', '').replace('-', '')}",
                        values["order_date"], values["expected_date"], values["store_id"], values["supplier_id"],
                        values["remark"], values["status"], values["total_quantity"], values["total_amount"],
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
                if values["status"] == "pending":
                    create_audit_notifications(
                        conn, "purchase_order", order_id, row["order_no"],
                        f"采购订单 {row['order_no']} 已提交，请及时审核。",
                    )
                return jsonify({"success": True, "id": order_id, "purchaseOrder": _serialize_order(conn, row)}), 201
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
                row, existing = _existing_values(conn, order_id)
                if not row:
                    return jsonify({"success": False, "message": "采购订单不存在"}), 404
                if row["status"] not in ("draft", "pending"):
                    return jsonify({"success": False, "message": "已审核或已入库的采购订单不能编辑"}), 409
                if any(float(item.get("received_qty") or 0) > 0 for item in existing["_items"]):
                    return jsonify({"success": False, "message": "已有入库数量的采购订单不能编辑"}), 409
                values = _order_values(conn, data, existing)
                now = _now()
                conn.execute(
                    """
                    UPDATE purchase_orders SET order_no = ?, order_date = ?, expected_date = ?, store_id = ?,
                        supplier_id = ?, remark = ?, status = ?, total_quantity = ?, total_amount = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        values["order_no"] or row["order_no"], values["order_date"], values["expected_date"],
                        values["store_id"], values["supplier_id"], values["remark"], values["status"],
                        values["total_quantity"], values["total_amount"], now, order_id,
                    ),
                )
                conn.execute("DELETE FROM purchase_order_items WHERE order_id = ?", (order_id,))
                _insert_items(conn, order_id, values["items"])
                updated = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
                if row["status"] == "pending" and values["status"] != "pending":
                    complete_audit_notifications(conn, "purchase_order", order_id)
                if values["status"] == "pending":
                    create_audit_notifications(
                        conn, "purchase_order", order_id, updated["order_no"],
                        f"采购订单 {updated['order_no']} 已提交，请及时审核。",
                        event_version=f"submitted:{now}",
                    )
                return jsonify({"success": True, "purchaseOrder": _serialize_order(conn, updated)})
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
            row = conn.execute("SELECT status FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                return jsonify({"success": False, "message": "采购订单不存在"}), 404
            if row["status"] not in ("draft", "pending"):
                return jsonify({"success": False, "message": "已审核或已入库的采购订单不能删除"}), 409
            complete_audit_notifications(conn, "purchase_order", order_id)
            conn.execute("DELETE FROM purchase_order_items WHERE order_id = ?", (order_id,))
            conn.execute("DELETE FROM purchase_orders WHERE id = ?", (order_id,))
            return jsonify({"success": True, "deleted": True})


@purchase_orders_bp.route("/purchase-orders/<int:order_id>/audit", methods=["POST"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["audit"])
def audit_purchase_order(order_id):
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row, existing = _existing_values(conn, order_id)
                if not row:
                    return jsonify({"success": False, "message": "采购订单不存在"}), 404
                if row["status"] != "pending":
                    return jsonify({"success": False, "message": "只有待审核采购订单可以审核"}), 409
                if not existing["_items"]:
                    return jsonify({"success": False, "message": "采购订单没有有效明细"}), 409
                if any(float(item.get("ordered_qty") or 0) <= 0 for item in existing["_items"]):
                    return jsonify({"success": False, "message": "采购数量必须大于 0"}), 409
                now = _now()
                conn.execute(
                    "UPDATE purchase_orders SET status = 'approved', audited_by = ?, audited_at = ?, updated_at = ? WHERE id = ?",
                    (current_identity(), now, now, order_id),
                )
                complete_audit_notifications(conn, "purchase_order", order_id)
                updated = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
                return jsonify({"success": True, "message": "采购订单审核成功", "purchaseOrder": _serialize_order(conn, updated)})
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify({"success": False, "message": "采购订单审核失败", "detail": str(exc)}), 500


@purchase_orders_bp.route("/purchase-orders/<int:order_id>/audit", methods=["DELETE"])
@require_admin_permission(ADMIN_PURCHASE_ORDER_PERMISSIONS["reverse_audit"])
def reverse_audit_purchase_order(order_id):
    with _write_lock:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                return jsonify({"success": False, "message": "采购订单不存在"}), 404
            if row["status"] not in ("approved",):
                return jsonify({"success": False, "message": "当前采购订单不能反审核"}), 409
            received = conn.execute(
                "SELECT COALESCE(SUM(received_qty), 0) AS quantity FROM purchase_order_items WHERE order_id = ?",
                (order_id,),
            ).fetchone()["quantity"]
            if float(received or 0) > 0:
                return jsonify({"success": False, "message": "采购订单已有入库数量，不能反审核"}), 409
            now = _now()
            conn.execute(
                "UPDATE purchase_orders SET status = 'pending', audited_by = NULL, audited_at = NULL, updated_at = ? WHERE id = ?",
                (now, order_id),
            )
            updated = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
            create_audit_notifications(
                conn, "purchase_order", order_id, updated["order_no"],
                f"采购订单 {updated['order_no']} 已反审核，请重新审核。",
                event_version=f"reverse:{now}",
            )
            return jsonify({"success": True, "message": "采购订单已反审核", "purchaseOrder": _serialize_order(conn, updated)})
