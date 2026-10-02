"""Material outbound drafts created by the employee touch terminal."""

import json
import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, Response, jsonify, request, stream_with_context
from queue import Empty, Queue

from utils.auth import (
    current_identity,
    require_admin_access,
    require_admin_permission,
    require_any_permission,
    require_permission,
)
from utils.db import get_db
from utils.notifications import create_audit_notifications, complete_audit_notifications
from utils.permission_catalog import ADMIN_AUDIT_NOTIFICATION_PERMISSIONS


material_outbounds_bp = Blueprint(
    "material_outbounds",
    __name__,
    url_prefix="/api",
)

_write_lock = threading.Lock()
_QUANTITY_EPSILON = 0.0000001
material_outbound_event_subscribers = set()
material_outbound_event_subscribers_lock = threading.Lock()


def broadcast_material_outbound_event(action, outbound=None, outbound_id=None):
    """向已连接的触屏页面推送原材料出库记录变更事件。"""
    payload = {
        "action": action,
        "outbound": outbound,
        "outboundId": outbound_id if outbound_id is not None else (outbound or {}).get("id"),
    }
    with material_outbound_event_subscribers_lock:
        subscribers = list(material_outbound_event_subscribers)
    for subscriber in subscribers:
        subscriber.put(payload)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def _text(value, max_length=None):
    result = "" if value is None else str(value).strip()
    return result[:max_length] if max_length else result


def _positive_number(value, label, allow_zero=False):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{label}必须是有效数字")
    if allow_zero:
        if number < 0:
            raise ValueError(f"{label}不能小于 0")
    elif number <= 0:
        raise ValueError(f"{label}必须大于 0")
    return float(number)


def _optional_int(value, label):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label}无效")


def _decode_ids(value):
    if isinstance(value, list):
        source = value
    else:
        try:
            source = json.loads(value or "[]")
        except (TypeError, ValueError):
            source = []
    result = []
    for item in source:
        try:
            item_id = int(item)
        except (TypeError, ValueError):
            continue
        if item_id not in result:
            result.append(item_id)
    return result


def _operator(conn, default="系统用户"):
    return current_identity(default)[:80]


def _settings_row(conn):
    return conn.execute(
        "SELECT * FROM material_outbound_settings WHERE id = 1"
    ).fetchone()


def _product_row(conn, product_id):
    return conn.execute(
        """
        SELECT product.*, unit.name AS unit_name
        FROM raw_material_products AS product
        LEFT JOIN units AS unit ON unit.id = product.unit_id
        WHERE product.id = ? AND COALESCE(product.enabled, 1) = 1
        """,
        (product_id,),
    ).fetchone()


def _finished_product_row(conn, product_id):
    return conn.execute(
        """
        SELECT product.*, unit.name AS unit_name
        FROM products AS product
        LEFT JOIN units AS unit ON unit.id = product.unit_id
        WHERE product.id = ? AND COALESCE(product.enabled, 1) = 1
        """,
        (product_id,),
    ).fetchone()


def _warehouse_row(conn, warehouse_id):
    return conn.execute(
        """
        SELECT id, name, store_id, status
        FROM warehouses
        WHERE id = ?
        """,
        (warehouse_id,),
    ).fetchone()


def _present_value(data, keys, fallback=None):
    for key in keys:
        if key in data:
            return data[key]
    return fallback


def _resolve_finished_audit_values(conn, document, data):
    document_values = dict(document)
    store_id = int(document_values["store_id"])
    warehouse_id = _optional_int(
        _present_value(
            data,
            ("finishedWarehouseId", "finished_warehouse_id"),
            document_values.get("finished_warehouse_id"),
        ),
        "成品入库仓库",
    )
    product_id = _optional_int(
        _present_value(
            data,
            ("finishedProductId", "finished_product_id"),
            document_values.get("finished_product_id"),
        ),
        "成品商品",
    )
    quantity_value = _present_value(
        data,
        ("finishedQuantity", "producedQuantity", "finished_quantity"),
        document_values.get("produced_quantity"),
    )
    remark = _text(
        _present_value(
            data,
            ("finishedRemark", "finished_remark"),
            document_values.get("finished_remark") or document_values.get("remark"),
        ),
        200,
    )

    if not warehouse_id:
        raise ValueError("请选择成品入库仓库")
    if not product_id:
        raise ValueError("请选择成品商品")
    quantity = _positive_number(quantity_value, "成品入库数量")

    warehouse = _warehouse_row(conn, warehouse_id)
    if not warehouse or (warehouse["status"] or "active") != "active":
        raise ValueError("成品入库仓库不存在或已停用")
    if int(warehouse["store_id"] or 0) not in (0, store_id):
        raise ValueError("成品入库仓库不属于当前门店")

    product = _finished_product_row(conn, product_id)
    if not product:
        raise ValueError("成品商品不存在或已停用")

    product_warehouse_id = product["warehouse_id"]
    if product_warehouse_id not in (None, "") and int(product_warehouse_id) != warehouse_id:
        raise ValueError("成品商品不属于所选成品仓库")

    product_store_ids = _decode_ids(product["store_ids"])
    if product_store_ids and store_id not in product_store_ids:
        raise ValueError("成品商品不属于当前门店")

    return {
        "warehouse_id": warehouse_id,
        "warehouse_name": warehouse["name"] or "",
        "product_id": product_id,
        "product_code": product["code"] or "",
        "product_name": product["name"] or "",
        "product_specification": product["specification"] or "",
        "product_unit": product["unit_name"] or "",
        "quantity": quantity,
        "remark": remark,
    }


def _location_rows(conn):
    stores = [
        dict(row)
        for row in conn.execute(
            """
            SELECT id, code, name, status
            FROM stores
            WHERE COALESCE(status, 'active') = 'active'
            ORDER BY id
            """
        ).fetchall()
    ]
    warehouses = []
    for row in conn.execute(
        """
        SELECT id, code, name, store_id, status
        FROM warehouses
        WHERE COALESCE(status, 'active') = 'active'
        ORDER BY id
        """
    ).fetchall():
        item = dict(row)
        item["storeId"] = item.pop("store_id", None)
        warehouses.append(item)
    return stores, warehouses


def _product_options(conn, store_id=None, warehouse_id=None):
    params = []
    stock_join = ""
    if store_id is not None and warehouse_id is not None:
        stock_join = """
            LEFT JOIN (
                SELECT product_id, SUM(quantity) AS current_stock
                FROM stock_balances
                WHERE product_type = 'raw-material'
                  AND store_id = ? AND warehouse_id = ?
                GROUP BY product_id
            ) AS balance ON balance.product_id = product.id
        """
        params.extend([store_id, warehouse_id])
    else:
        stock_join = """
            LEFT JOIN (
                SELECT product_id, SUM(quantity) AS current_stock
                FROM stock_balances
                WHERE product_type = 'raw-material'
                GROUP BY product_id
            ) AS balance ON balance.product_id = product.id
        """

    rows = conn.execute(
        f"""
        SELECT product.id, product.code, product.name, product.specification,
               product.warehouse_id, product.store_ids,
               unit.name AS unit_name,
               COALESCE(balance.current_stock, 0) AS current_stock
        FROM raw_material_products AS product
        LEFT JOIN units AS unit ON unit.id = product.unit_id
        {stock_join}
        WHERE COALESCE(product.enabled, 1) = 1
        ORDER BY product.name, product.id
        """,
        params,
    ).fetchall()

    products = []
    for row in rows:
        item = dict(row)
        item["warehouseId"] = item.pop("warehouse_id", None)
        item["storeIds"] = _decode_ids(item.pop("store_ids", "[]"))
        item["unit"] = item.pop("unit_name", "") or ""
        item["currentStock"] = float(item.pop("current_stock", 0) or 0)
        products.append(item)
    return products


def _remark_tags(conn):
    return [
        row["tag"]
        for row in conn.execute(
            """
            SELECT tag FROM material_remark_tags
            ORDER BY use_count DESC, COALESCE(updated_at, created_at) DESC, id DESC
            LIMIT 40
            """
        ).fetchall()
    ]


def _serialize_settings(conn):
    row = _settings_row(conn)
    data = dict(row) if row else {}
    store_id = data.get("default_store_id")
    warehouse_id = data.get("default_warehouse_id")
    default_product_id = data.get("default_product_id")
    allowed_ids = _decode_ids(data.get("allowed_product_ids"))
    stores, warehouses = _location_rows(conn)
    products = _product_options(conn, store_id, warehouse_id)
    product_map = {item["id"]: item for item in products}
    allowed_products = [
        product_map[product_id]
        for product_id in allowed_ids
        if product_id in product_map
    ]
    default_product = product_map.get(default_product_id)

    configured = bool(
        store_id
        and warehouse_id
        and default_product
        and default_product_id in allowed_ids
    )
    return {
        "defaultStoreId": store_id,
        "defaultWarehouseId": warehouse_id,
        "defaultProductId": default_product_id,
        "allowedProductIds": allowed_ids,
        "deductionStrategy": data.get("deduction_strategy") or "fifo",
        "allowInsufficientDraft": bool(data.get("allow_insufficient_draft", 1)),
        "showCurrentStock": bool(data.get("show_current_stock", 1)),
        "updatedBy": data.get("updated_by") or "",
        "updatedAt": data.get("updated_at"),
        "configured": configured,
        "defaultProduct": default_product,
        "allowedProducts": allowed_products,
        "stores": stores,
        "warehouses": warehouses,
        "products": products,
        "remarkTags": _remark_tags(conn),
    }


def _serialize_item(row):
    item = dict(row)
    item["outboundId"] = item.pop("outbound_id", None)
    item["lineNo"] = item.pop("line_no", 1)
    item["productId"] = item.pop("product_id", None)
    item["productCode"] = item.pop("product_code", "") or ""
    item["productName"] = item.pop("product_name", "") or ""
    return item


def _serialize_document(conn, row, include_items=True):
    document = dict(row)
    document["documentNo"] = document.pop("document_no", "")
    document["documentDate"] = document.pop("document_date", "")
    document["storeId"] = document.pop("store_id", None)
    document["storeName"] = document.pop("store_name", "") or ""
    document["warehouseId"] = document.pop("warehouse_id", None)
    document["warehouseName"] = document.pop("warehouse_name", "") or ""
    document["totalQuantity"] = float(document.pop("total_quantity", 0) or 0)
    document["producedQuantity"] = float(document.pop("produced_quantity", 0) or 0)
    document["createdBy"] = document.pop("created_by", "") or ""
    document["createdAt"] = document.pop("created_at", "") or ""
    document["auditedBy"] = document.pop("audited_by", "") or ""
    document["auditedAt"] = document.pop("audited_at", None)
    document["finishedInboundId"] = document.pop("finished_inbound_id", None)
    document["finishedProductId"] = document.pop("finished_product_id", None)
    document["finishedProductCode"] = document.pop("finished_product_code", "") or ""
    document["finishedProductName"] = document.pop("finished_product_name", "") or ""
    document["finishedProductSpecification"] = (
        document.pop("finished_product_specification", "") or ""
    )
    document["finishedProductUnit"] = document.pop("finished_product_unit", "") or ""
    document["finishedWarehouseId"] = document.pop("finished_warehouse_id", None)
    document["finishedWarehouseName"] = document.pop("finished_warehouse_name", "") or ""
    document["finishedRemark"] = document.pop("finished_remark", "") or ""
    document["updatedAt"] = document.pop("updated_at", None)
    if include_items:
        items = conn.execute(
            """
            SELECT * FROM material_outbound_items
            WHERE outbound_id = ?
            ORDER BY line_no, id
            """,
            (row["id"],),
        ).fetchall()
        document["items"] = [_serialize_item(item) for item in items]
        document["primaryItem"] = document["items"][0] if document["items"] else None
    return document


def _resolve_draft_values(conn, data, existing=None):
    existing = existing or {}
    settings = _settings_row(conn)
    if not settings:
        raise ValueError("原材料出库设置尚未初始化")

    allowed_ids = _decode_ids(settings["allowed_product_ids"])
    store_id = _optional_int(
        data.get("storeId", existing.get("store_id", settings["default_store_id"])),
        "门店",
    )
    warehouse_id = _optional_int(
        data.get(
            "warehouseId",
            existing.get("warehouse_id", settings["default_warehouse_id"]),
        ),
        "仓库",
    )
    product_id = _optional_int(
        data.get(
            "productId",
            existing.get("product_id", settings["default_product_id"]),
        ),
        "原材料",
    )
    if not store_id or not warehouse_id or not product_id:
        raise ValueError("请先在后台配置默认门店、仓库和原材料")
    if product_id not in allowed_ids:
        raise ValueError("该原材料未包含在触屏端可操作范围内")

    store = conn.execute(
        "SELECT id, name FROM stores WHERE id = ?",
        (store_id,),
    ).fetchone()
    warehouse = conn.execute(
        "SELECT id, name, store_id FROM warehouses WHERE id = ?",
        (warehouse_id,),
    ).fetchone()
    product = _product_row(conn, product_id)
    if not store:
        raise ValueError("默认门店不存在")
    if not warehouse:
        raise ValueError("默认仓库不存在")
    if int(warehouse["store_id"] or 0) not in (0, store_id):
        raise ValueError("默认仓库不属于所选门店")
    if not product:
        raise ValueError("默认原材料不存在或已停用")

    quantity = _positive_number(
        data.get("quantity", data.get("used", existing.get("quantity"))),
        "原材料出库数量",
    )
    produced_value = data.get(
        "producedQuantity",
        data.get("produced", existing.get("produced_quantity")),
    )
    produced_quantity = (
        0
        if produced_value in (None, "")
        else _positive_number(produced_value, "成品数量", allow_zero=True)
    )
    available = conn.execute(
        """
        SELECT COALESCE(SUM(quantity), 0) AS quantity
        FROM stock_balances
        WHERE product_type = 'raw-material'
          AND product_id = ? AND warehouse_id = ? AND store_id = ?
        """,
        (product_id, warehouse_id, store_id),
    ).fetchone()["quantity"]
    if (
        not bool(settings["allow_insufficient_draft"])
        and float(available or 0) + _QUANTITY_EPSILON < quantity
    ):
        raise ValueError(f"当前库存不足，可用库存为 {float(available or 0):g}")

    return {
        "store_id": store_id,
        "store_name": store["name"] or "",
        "warehouse_id": warehouse_id,
        "warehouse_name": warehouse["name"] or "",
        "product_id": product_id,
        "product_code": product["code"] or "",
        "product_name": product["name"] or "",
        "specification": product["specification"] or "",
        "unit": product["unit_name"] or "",
        "quantity": quantity,
        "produced_quantity": produced_quantity,
        "remark": _text(data.get("remark", existing.get("remark", "")), 200),
        "available_stock": float(available or 0),
    }


def _save_remark_tag(conn, remark):
    if not remark:
        return
    now = _now()
    conn.execute(
        """
        INSERT INTO material_remark_tags (tag, use_count, created_at, updated_at)
        VALUES (?, 1, ?, ?)
        ON CONFLICT(tag) DO UPDATE SET
            use_count = material_remark_tags.use_count + 1,
            updated_at = excluded.updated_at
        """,
        (remark, now, now),
    )


def _insert_draft(conn, values):
    now = _now()
    cursor = conn.execute(
        """
        INSERT INTO material_outbounds (
            document_no, document_date, store_id, store_name,
            warehouse_id, warehouse_name, status, total_quantity,
            produced_quantity, remark, source, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, 'touch', ?, ?, ?)
        """,
        (
            f"TEMP-{now.replace('-', '').replace(':', '').replace(' ', '')}-{threading.get_ident()}",
            _today(),
            values["store_id"],
            values["store_name"],
            values["warehouse_id"],
            values["warehouse_name"],
            values["quantity"],
            values["produced_quantity"],
            values["remark"],
            _operator(conn, "触屏员工"),
            now,
            now,
        ),
    )
    outbound_id = cursor.lastrowid
    document_no = f"YLCK{datetime.now().strftime('%Y%m%d')}{outbound_id:04d}"
    conn.execute(
        "UPDATE material_outbounds SET document_no = ? WHERE id = ?",
        (document_no, outbound_id),
    )
    item_cursor = conn.execute(
        """
        INSERT INTO material_outbound_items (
            outbound_id, line_no, product_id, product_code, product_name,
            specification, unit, quantity, remark
        ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            outbound_id,
            values["product_id"],
            values["product_code"],
            values["product_name"],
            values["specification"],
            values["unit"],
            values["quantity"],
            values["remark"],
        ),
    )
    _save_remark_tag(conn, values["remark"])
    return outbound_id, item_cursor.lastrowid


def _post_inventory(conn, document, item):
    quantity_needed = float(item["quantity"] or 0)
    balances = conn.execute(
        """
        SELECT balance.*,
               COALESCE(MIN(movement.created_at), balance.updated_at, '') AS first_in_at
        FROM stock_balances AS balance
        LEFT JOIN stock_movements AS movement
          ON movement.movement_type = 'in'
         AND movement.product_type = balance.product_type
         AND movement.product_id = balance.product_id
         AND movement.warehouse_id = balance.warehouse_id
         AND movement.store_id = balance.store_id
         AND movement.bin_code = balance.bin_code
         AND movement.batch_no = balance.batch_no
        WHERE balance.product_type = 'raw-material'
          AND balance.product_id = ?
          AND balance.warehouse_id = ?
          AND balance.store_id = ?
          AND balance.quantity > 0
        GROUP BY balance.id
        ORDER BY first_in_at ASC, balance.id ASC
        """,
        (
            item["product_id"],
            document["warehouse_id"],
            document["store_id"],
        ),
    ).fetchall()
    available = sum(float(balance["quantity"] or 0) for balance in balances)
    if available + _QUANTITY_EPSILON < quantity_needed:
        raise ValueError(
            f'{item["product_name"]}库存不足，需要 {quantity_needed:g}，'
            f"当前可用 {available:g}"
        )

    now = _now()
    remaining = quantity_needed
    for balance in balances:
        if remaining <= _QUANTITY_EPSILON:
            break
        balance_quantity = float(balance["quantity"] or 0)
        deducted = min(balance_quantity, remaining)
        conn.execute(
            """
            UPDATE stock_balances
            SET quantity = quantity - ?, updated_at = ?
            WHERE id = ?
            """,
            (deducted, now, balance["id"]),
        )
        conn.execute(
            """
            INSERT INTO stock_movements (
                movement_type, receipt_type, source_document_id,
                source_document_no, source_item_id, product_type,
                product_id, warehouse_id, store_id, bin_code, batch_no,
                quantity, unit_price, tax_rate, total_amount, created_at
            ) VALUES (
                'out', 'raw-material', ?, ?, ?, 'raw-material',
                ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?
            )
            """,
            (
                document["id"],
                document["document_no"],
                item["id"],
                item["product_id"],
                document["warehouse_id"],
                document["store_id"],
                balance["bin_code"] or "",
                balance["batch_no"] or "",
                deducted,
                now,
            ),
        )
        remaining -= deducted
    conn.execute("DELETE FROM stock_balances WHERE ABS(quantity) < 0.0000001")


def _reverse_inventory(conn, document):
    movements = conn.execute(
        """
        SELECT * FROM stock_movements
        WHERE movement_type = 'out'
          AND receipt_type = 'raw-material'
          AND source_document_id = ?
          AND source_document_no = ?
        ORDER BY id
        """,
        (document["id"], document["document_no"]),
    ).fetchall()
    if not movements:
        raise ValueError("该出库单没有对应的库存流水，无法反审核")

    now = _now()
    for movement in movements:
        conn.execute(
            """
            INSERT INTO stock_balances (
                product_type, product_id, warehouse_id, store_id,
                bin_code, batch_no, quantity, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_type, product_id, warehouse_id, store_id, bin_code, batch_no)
            DO UPDATE SET quantity = stock_balances.quantity + excluded.quantity,
                          updated_at = excluded.updated_at
            """,
            (
                movement["product_type"],
                movement["product_id"],
                movement["warehouse_id"],
                movement["store_id"],
                movement["bin_code"] or "",
                movement["batch_no"] or "",
                float(movement["quantity"] or 0),
                now,
            ),
        )
    conn.execute(
        """
        DELETE FROM stock_movements
        WHERE movement_type = 'out'
          AND receipt_type = 'raw-material'
          AND source_document_id = ?
          AND source_document_no = ?
        """,
        (document["id"], document["document_no"]),
    )


def _post_finished_inventory(conn, inbound, item, quantity, store_id, warehouse_id):
    now = _now()
    conn.execute(
        """
        INSERT INTO stock_balances (
            product_type, product_id, warehouse_id, store_id,
            bin_code, batch_no, quantity, updated_at
        ) VALUES ('finished-product', ?, ?, ?, '', '', ?, ?)
        ON CONFLICT(product_type, product_id, warehouse_id, store_id, bin_code, batch_no)
        DO UPDATE SET quantity = stock_balances.quantity + excluded.quantity,
                      updated_at = excluded.updated_at
        """,
        (item["product_id"], warehouse_id, store_id, quantity, now),
    )
    conn.execute(
        """
        INSERT INTO stock_movements (
            movement_type, receipt_type, source_document_id,
            source_document_no, source_item_id, product_type,
            product_id, warehouse_id, store_id, bin_code, batch_no,
            quantity, unit_price, tax_rate, total_amount, created_at
        ) VALUES (
            'in', 'finished-product', ?, ?, ?, 'finished-product',
            ?, ?, ?, '', '', ?, NULL, 0, 0, ?
        )
        """,
        (
            inbound["id"],
            inbound["document_no"],
            item["id"],
            item["product_id"],
            warehouse_id,
            store_id,
            quantity,
            now,
        ),
    )
    conn.execute(
        """
        INSERT INTO inventory (product_id, stock, min_stock, max_stock, updated_at)
        VALUES (?, ?, 0, 0, ?)
        ON CONFLICT(product_id) DO UPDATE SET
            stock = COALESCE(inventory.stock, 0) + excluded.stock,
            updated_at = excluded.updated_at
        """,
        (item["product_id"], quantity, now),
    )


def _create_finished_inbound(conn, document, values):
    now = _now()
    temporary_no = (
        f"TEMP-FINISHED-{document['id']}-"
        f"{now.replace('-', '').replace(':', '').replace(' ', '')}"
    )
    cursor = conn.execute(
        """
        INSERT INTO stock_inbounds (
            document_no, document_date, receipt_type, store_id, warehouse_id,
            supplier_id, workshop, inspector, quality_no, remark, attachments,
            status, total_quantity, total_tax, total_amount, posted_at,
            created_at, updated_at
        ) VALUES (?, ?, 'finished-product', ?, ?, NULL, '', ?, '', ?, '[]',
                  'reviewed', ?, 0, 0, ?, ?, ?)
        """,
        (
            temporary_no,
            document["document_date"],
            document["store_id"],
            values["warehouse_id"],
            _operator(conn),
            values["remark"],
            values["quantity"],
            now,
            now,
            now,
        ),
    )
    inbound_id = cursor.lastrowid
    document_no = (
        f"SCRK{str(document['document_date']).replace('-', '')[:8]}"
        f"{inbound_id:04d}"
    )
    conn.execute(
        "UPDATE stock_inbounds SET document_no = ? WHERE id = ?",
        (document_no, inbound_id),
    )
    item_cursor = conn.execute(
        """
        INSERT INTO stock_inbound_items (
            inbound_id, line_no, product_type, product_id, warehouse_id,
            product_code, product_name, specification, unit, expected_qty,
            received_qty, bin_code, batch_no, unit_price, tax_rate,
            tax_amount, total_amount, remark
        ) VALUES (?, 1, 'finished-product', ?, ?, ?, ?, ?, ?, NULL, ?,
                   '', '', NULL, 0, 0, 0, ?)
        """,
        (
            inbound_id,
            values["product_id"],
            values["warehouse_id"],
            values["product_code"],
            values["product_name"],
            values["product_specification"],
            values["product_unit"],
            values["quantity"],
            values["remark"],
        ),
    )
    inbound = conn.execute(
        "SELECT * FROM stock_inbounds WHERE id = ?",
        (inbound_id,),
    ).fetchone()
    item = conn.execute(
        "SELECT * FROM stock_inbound_items WHERE id = ?",
        (item_cursor.lastrowid,),
    ).fetchone()
    _post_finished_inventory(
        conn,
        inbound,
        item,
        values["quantity"],
        document["store_id"],
        values["warehouse_id"],
    )
    return inbound


def _reverse_finished_inbound(conn, document):
    inbound_id = document["finished_inbound_id"]
    if not inbound_id:
        return

    inbound = conn.execute(
        "SELECT * FROM stock_inbounds WHERE id = ?",
        (inbound_id,),
    ).fetchone()
    if not inbound:
        raise ValueError("关联的成品入库单不存在")

    movements = conn.execute(
        """
        SELECT * FROM stock_movements
        WHERE movement_type = 'in'
          AND receipt_type = 'finished-product'
          AND source_document_id = ?
        ORDER BY id
        """,
        (inbound_id,),
    ).fetchall()
    if not movements:
        raise ValueError("关联的成品入库单没有库存流水")

    now = _now()
    for movement in movements:
        quantity = float(movement["quantity"] or 0)
        balance = conn.execute(
            """
            SELECT quantity FROM stock_balances
            WHERE product_type = ? AND product_id = ? AND warehouse_id = ?
              AND store_id = ? AND bin_code = ? AND batch_no = ?
            """,
            (
                movement["product_type"],
                movement["product_id"],
                movement["warehouse_id"],
                movement["store_id"],
                movement["bin_code"] or "",
                movement["batch_no"] or "",
            ),
        ).fetchone()
        if not balance or float(balance["quantity"] or 0) + _QUANTITY_EPSILON < quantity:
            raise ValueError("当前成品库存不足，无法反审核")
        conn.execute(
            """
            UPDATE stock_balances
            SET quantity = quantity - ?, updated_at = ?
            WHERE product_type = ? AND product_id = ? AND warehouse_id = ?
              AND store_id = ? AND bin_code = ? AND batch_no = ?
            """,
            (
                quantity,
                now,
                movement["product_type"],
                movement["product_id"],
                movement["warehouse_id"],
                movement["store_id"],
                movement["bin_code"] or "",
                movement["batch_no"] or "",
            ),
        )
        conn.execute(
            """
            UPDATE inventory
            SET stock = COALESCE(stock, 0) - ?, updated_at = ?
            WHERE product_id = ?
            """,
            (quantity, now, movement["product_id"]),
        )

    conn.execute(
        """
        DELETE FROM stock_movements
        WHERE movement_type = 'in'
          AND receipt_type = 'finished-product'
          AND source_document_id = ?
        """,
        (inbound_id,),
    )
    conn.execute("DELETE FROM stock_balances WHERE ABS(quantity) < 0.0000001")
    conn.execute(
        """
        UPDATE stock_inbounds
        SET status = 'cancelled', posted_at = NULL, updated_at = ?
        WHERE id = ?
        """,
        (now, inbound_id),
    )


@material_outbounds_bp.route("/material-outbound-settings", methods=["GET"])
@require_permission("touch.material.read")
def get_material_outbound_settings():
    with get_db() as conn:
        return jsonify(_serialize_settings(conn))


@material_outbounds_bp.route("/material-outbound-settings", methods=["PUT"])
@require_admin_access
def update_material_outbound_settings():
    data = request.get_json(silent=True) or {}
    try:
        store_id = _optional_int(data.get("defaultStoreId"), "默认门店")
        warehouse_id = _optional_int(data.get("defaultWarehouseId"), "默认仓库")
        default_product_id = _optional_int(data.get("defaultProductId"), "默认原材料")
        allowed_ids = _decode_ids(data.get("allowedProductIds"))
        if not store_id or not warehouse_id or not default_product_id:
            raise ValueError("默认门店、仓库和原材料不能为空")
        if default_product_id not in allowed_ids:
            raise ValueError("默认原材料必须包含在可操作原材料中")

        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                store = conn.execute(
                    "SELECT 1 FROM stores WHERE id = ?",
                    (store_id,),
                ).fetchone()
                warehouse = conn.execute(
                    "SELECT store_id FROM warehouses WHERE id = ?",
                    (warehouse_id,),
                ).fetchone()
                if not store:
                    raise ValueError("默认门店不存在")
                if not warehouse:
                    raise ValueError("默认仓库不存在")
                if int(warehouse["store_id"] or 0) not in (0, store_id):
                    raise ValueError("默认仓库不属于所选门店")
                for product_id in allowed_ids:
                    if not _product_row(conn, product_id):
                        raise ValueError(f"原材料 ID {product_id} 不存在或已停用")

                now = _now()
                conn.execute(
                    """
                    UPDATE material_outbound_settings SET
                        default_store_id = ?, default_warehouse_id = ?,
                        default_product_id = ?, allowed_product_ids = ?,
                        deduction_strategy = 'fifo',
                        allow_insufficient_draft = ?,
                        show_current_stock = ?, updated_by = ?, updated_at = ?
                    WHERE id = 1
                    """,
                    (
                        store_id,
                        warehouse_id,
                        default_product_id,
                        json.dumps(allowed_ids, ensure_ascii=False),
                        int(bool(data.get("allowInsufficientDraft", True))),
                        int(bool(data.get("showCurrentStock", True))),
                        _operator(conn),
                        now,
                    ),
                )
                return jsonify(
                    {
                        "success": True,
                        "message": "触屏端原材料出库设置已保存",
                        "settings": _serialize_settings(conn),
                    }
                )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify(
            {"success": False, "message": "保存设置失败", "detail": str(exc)}
        ), 500


@material_outbounds_bp.route("/material-outbounds/events", methods=["GET"])
@require_permission("touch.material.read")
def material_outbound_events():
    """通过 SSE 推送原材料出库记录变化。"""
    subscriber = Queue()
    with material_outbound_event_subscribers_lock:
        material_outbound_event_subscribers.add(subscriber)

    def event_stream():
        yield "retry: 3000\nevent: connected\ndata: {}\n\n"
        try:
            while True:
                try:
                    payload = subscriber.get(timeout=20)
                    data = json.dumps(payload, ensure_ascii=False)
                    yield f"event: material-outbound-change\ndata: {data}\n\n"
                except Empty:
                    yield ": keep-alive\n\n"
        finally:
            with material_outbound_event_subscribers_lock:
                material_outbound_event_subscribers.discard(subscriber)

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@material_outbounds_bp.route("/material-outbounds", methods=["GET"])
@require_permission("touch.material.read")
def list_material_outbounds():
    status = _text(request.args.get("status"), 20)
    start_date = _text(request.args.get("startDate"), 10)
    end_date = _text(request.args.get("endDate"), 10)
    limit = request.args.get("limit", default=200, type=int)
    limit = min(max(limit or 200, 1), 1000)

    with get_db() as conn:
        sql = "SELECT * FROM material_outbounds WHERE 1 = 1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if start_date:
            sql += " AND document_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND document_date <= ?"
            params.append(end_date)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return jsonify([_serialize_document(conn, row) for row in rows])


@material_outbounds_bp.route("/material-outbounds/<int:outbound_id>", methods=["GET"])
@require_permission("touch.material.read")
def get_material_outbound(outbound_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM material_outbounds WHERE id = ?",
            (outbound_id,),
        ).fetchone()
        if not row:
            return jsonify({"success": False, "message": "原材料出库单不存在"}), 404
        return jsonify(_serialize_document(conn, row))


@material_outbounds_bp.route("/material-outbounds", methods=["POST"])
@require_permission("touch.material.create")
def create_material_outbound():
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                values = _resolve_draft_values(conn, data)
                outbound_id, _item_id = _insert_draft(conn, values)
                row = conn.execute(
                    "SELECT * FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                ).fetchone()
                material_outbound = _serialize_document(conn, row)
                create_audit_notifications(
                    conn,
                    "material_outbound",
                    outbound_id,
                    row["document_no"],
                    f"原材料出库单 {row['document_no']} 已提交，请及时审核。",
                )
                conn.commit()
                broadcast_material_outbound_event(
                    "created",
                    outbound=material_outbound,
                )
                return jsonify(
                    {
                        "success": True,
                        "message": "原材料出库草稿已提交，等待管理员审核",
                        "materialOutbound": material_outbound,
                    }
                ), 201
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify(
            {"success": False, "message": "提交原材料出库草稿失败", "detail": str(exc)}
        ), 500


@material_outbounds_bp.route("/material-outbounds/<int:outbound_id>", methods=["PUT"])
@require_admin_access
def update_material_outbound(outbound_id):
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    "SELECT * FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                ).fetchone()
                if not row:
                    return jsonify(
                        {"success": False, "message": "原材料出库单不存在"}
                    ), 404
                if row["status"] != "draft":
                    return jsonify(
                        {"success": False, "message": "只有草稿状态可以修改"}
                    ), 409
                old_item = conn.execute(
                    """
                    SELECT * FROM material_outbound_items
                    WHERE outbound_id = ?
                    ORDER BY line_no, id LIMIT 1
                    """,
                    (outbound_id,),
                ).fetchone()
                existing = dict(row)
                if old_item:
                    existing.update(dict(old_item))
                values = _resolve_draft_values(conn, data, existing=existing)
                now = _now()
                conn.execute(
                    """
                    UPDATE material_outbounds SET
                        store_id = ?, store_name = ?, warehouse_id = ?,
                        warehouse_name = ?, total_quantity = ?,
                        produced_quantity = ?, remark = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        values["store_id"],
                        values["store_name"],
                        values["warehouse_id"],
                        values["warehouse_name"],
                        values["quantity"],
                        values["produced_quantity"],
                        values["remark"],
                        now,
                        outbound_id,
                    ),
                )
                conn.execute(
                    "DELETE FROM material_outbound_items WHERE outbound_id = ?",
                    (outbound_id,),
                )
                conn.execute(
                    """
                    INSERT INTO material_outbound_items (
                        outbound_id, line_no, product_id, product_code,
                        product_name, specification, unit, quantity, remark
                    ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        outbound_id,
                        values["product_id"],
                        values["product_code"],
                        values["product_name"],
                        values["specification"],
                        values["unit"],
                        values["quantity"],
                        values["remark"],
                    ),
                )
                _save_remark_tag(conn, values["remark"])
                updated = conn.execute(
                    "SELECT * FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                ).fetchone()
                material_outbound = _serialize_document(conn, updated)
                conn.commit()
                broadcast_material_outbound_event(
                    "updated",
                    outbound=material_outbound,
                )
                return jsonify(
                    {
                        "success": True,
                        "message": "原材料出库草稿已更新",
                        "materialOutbound": material_outbound,
                    }
                )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    except Exception as exc:
        return jsonify(
            {"success": False, "message": "更新原材料出库草稿失败", "detail": str(exc)}
        ), 500


@material_outbounds_bp.route(
    "/material-outbounds/<int:outbound_id>/audit",
    methods=["POST"],
)
@require_any_permission(
    "touch.material.audit",
    ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["material_outbound"],
)
def audit_material_outbound(outbound_id):
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                document = conn.execute(
                    "SELECT * FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                ).fetchone()
                if not document:
                    return jsonify(
                        {"success": False, "message": "原材料出库单不存在"}
                    ), 404
                if document["status"] != "draft":
                    return jsonify(
                        {"success": False, "message": "只有草稿状态可以审核"}
                    ), 409
                movement_exists = conn.execute(
                    """
                    SELECT 1 FROM stock_movements
                    WHERE movement_type = 'out'
                      AND receipt_type = 'raw-material'
                      AND source_document_id = ?
                      AND source_document_no = ?
                    LIMIT 1
                    """,
                    (outbound_id, document["document_no"]),
                ).fetchone()
                if movement_exists:
                    return jsonify(
                        {"success": False, "message": "该单据已存在库存流水"}
                    ), 409
                items = conn.execute(
                    """
                    SELECT * FROM material_outbound_items
                    WHERE outbound_id = ?
                    ORDER BY line_no, id
                    """,
                    (outbound_id,),
                ).fetchall()
                if not items:
                    raise ValueError("出库单没有原材料明细")
                finished_values = _resolve_finished_audit_values(conn, document, data)
                for item in items:
                    _post_inventory(conn, document, item)
                finished_inbound = _create_finished_inbound(
                    conn,
                    document,
                    finished_values,
                )
                now = _now()
                conn.execute(
                    """
                    UPDATE material_outbounds SET
                        status = 'reviewed', audited_by = ?,
                        audited_at = ?, produced_quantity = ?,
                        finished_inbound_id = ?, finished_product_id = ?,
                        finished_product_code = ?, finished_product_name = ?,
                        finished_product_specification = ?, finished_product_unit = ?,
                        finished_warehouse_id = ?, finished_warehouse_name = ?,
                        finished_remark = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        _operator(conn),
                        now,
                        finished_values["quantity"],
                        finished_inbound["id"],
                        finished_values["product_id"],
                        finished_values["product_code"],
                        finished_values["product_name"],
                        finished_values["product_specification"],
                        finished_values["product_unit"],
                        finished_values["warehouse_id"],
                        finished_values["warehouse_name"],
                        finished_values["remark"],
                        now,
                        outbound_id,
                    ),
                )
                updated = conn.execute(
                    "SELECT * FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                ).fetchone()
                complete_audit_notifications(conn, "material_outbound", outbound_id)
                material_outbound = _serialize_document(conn, updated)
                conn.commit()
                broadcast_material_outbound_event(
                    "reviewed",
                    outbound=material_outbound,
                )
                return jsonify(
                    {
                        "success": True,
                        "message": "审核成功，原材料已出库，成品已入库",
                        "materialOutbound": material_outbound,
                        "finishedInboundId": finished_inbound["id"],
                        "finishedInboundNo": finished_inbound["document_no"],
                    }
                )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 409
    except Exception as exc:
        return jsonify(
            {"success": False, "message": "原材料出库审核失败", "detail": str(exc)}
        ), 500


@material_outbounds_bp.route(
    "/material-outbounds/<int:outbound_id>/audit",
    methods=["DELETE"],
)
@require_admin_permission(ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["material_outbound"])
def reverse_audit_material_outbound(outbound_id):
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                document = conn.execute(
                    "SELECT * FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                ).fetchone()
                if not document:
                    return jsonify(
                        {"success": False, "message": "原材料出库单不存在"}
                    ), 404
                if document["status"] != "reviewed":
                    return jsonify(
                        {"success": False, "message": "当前单据未审核"}
                    ), 409
                _reverse_finished_inbound(conn, document)
                _reverse_inventory(conn, document)
                now = _now()
                conn.execute(
                    """
                    UPDATE material_outbounds SET
                        status = 'draft', audited_by = NULL,
                        audited_at = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (now, outbound_id),
                )
                updated = conn.execute(
                    "SELECT * FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                ).fetchone()
                create_audit_notifications(
                    conn,
                    "material_outbound",
                    outbound_id,
                    updated["document_no"],
                    f"原材料出库单 {updated['document_no']} 已反审核，请重新审核。",
                    event_version=f"reverse:{now}",
                )
                material_outbound = _serialize_document(conn, updated)
                conn.commit()
                broadcast_material_outbound_event(
                    "reversed",
                    outbound=material_outbound,
                )
                return jsonify(
                    {
                        "success": True,
                        "message": "反审核成功，原材料库存已回补",
                        "materialOutbound": material_outbound,
                    }
                )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 409
    except Exception as exc:
        return jsonify(
            {"success": False, "message": "原材料出库反审核失败", "detail": str(exc)}
        ), 500


@material_outbounds_bp.route(
    "/material-outbounds/<int:outbound_id>",
    methods=["DELETE"],
)
@require_admin_access
def cancel_material_outbound(outbound_id):
    with _write_lock:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            document = conn.execute(
                "SELECT * FROM material_outbounds WHERE id = ?",
                (outbound_id,),
            ).fetchone()
            if not document:
                return jsonify(
                    {"success": False, "message": "原材料出库单不存在"}
                ), 404
            if document["status"] == "reviewed":
                return jsonify(
                    {"success": False, "message": "已审核单据请先反审核"}
                ), 409
            if document["status"] == "cancelled":
                complete_audit_notifications(conn, "material_outbound", outbound_id)
                conn.execute(
                    "DELETE FROM material_outbound_items WHERE outbound_id = ?",
                    (outbound_id,),
                )
                conn.execute(
                    "DELETE FROM material_outbounds WHERE id = ?",
                    (outbound_id,),
                )
                conn.commit()
                broadcast_material_outbound_event(
                    "deleted",
                    outbound_id=outbound_id,
                )
                return jsonify({"success": True, "message": "已作废单据已删除"})
            conn.execute(
                """
                UPDATE material_outbounds
                SET status = 'cancelled', updated_at = ?
                WHERE id = ?
                """,
                (_now(), outbound_id),
            )
            complete_audit_notifications(conn, "material_outbound", outbound_id)
            updated = conn.execute(
                "SELECT * FROM material_outbounds WHERE id = ?",
                (outbound_id,),
            ).fetchone()
            material_outbound = _serialize_document(conn, updated)
            conn.commit()
            broadcast_material_outbound_event(
                "cancelled",
                outbound=material_outbound,
            )
            return jsonify({"success": True, "message": "原材料出库草稿已作废"})


@material_outbounds_bp.route(
    "/material-outbounds/<int:outbound_id>/restart",
    methods=["POST"],
)
@require_admin_access
def restart_material_outbound(outbound_id):
    with _write_lock:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            document = conn.execute(
                "SELECT * FROM material_outbounds WHERE id = ?",
                (outbound_id,),
            ).fetchone()
            if not document:
                return jsonify(
                    {"success": False, "message": "原材料出库单不存在"}
                ), 404
            if document["status"] != "cancelled":
                return jsonify(
                    {"success": False, "message": "只有已作废单据可以重新启用"}
                ), 409
            now = _now()
            conn.execute(
                """
                UPDATE material_outbounds
                SET status = 'draft', updated_at = ?
                WHERE id = ?
                """,
                (now, outbound_id),
            )
            updated = conn.execute(
                "SELECT * FROM material_outbounds WHERE id = ?",
                (outbound_id,),
            ).fetchone()
            create_audit_notifications(
                conn,
                "material_outbound",
                outbound_id,
                updated["document_no"],
                f"原材料出库单 {updated['document_no']} 已重新提交，请及时审核。",
                event_version=f"restart:{now}",
            )
            material_outbound = _serialize_document(conn, updated)
            conn.commit()
            broadcast_material_outbound_event(
                "restarted",
                outbound=material_outbound,
            )
            return jsonify(
                {
                    "success": True,
                    "message": "原材料出库单已重新启用",
                    "materialOutbound": material_outbound,
                }
            )
