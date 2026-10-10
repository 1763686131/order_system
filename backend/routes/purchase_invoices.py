"""Purchase invoice registration and allocation APIs."""

import json

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.supplier_ledger import (
    FinanceError, amount, business_date, cents, check_scope, effective_sql,
    idempotent_result, now, save_operation, scope_sql,
)
from utils.supplier_settlement import (
    attachments_value, load_payable, positive_id, quantity, supplier_store, text,
    refresh_invoice, required_version, proportional_tax, invoice_allocation_suggestion,
)
from routes.supplier_finance import finance_errors
from utils.purchase_invoice_orders import (
    load_order_source, order_capacity, order_source_options, order_usage, sync_order_invoices,
)


purchase_invoices_bp = Blueprint("purchase_invoices", __name__, url_prefix="/api")


def invoice_row(conn, invoice_id):
    row = conn.execute("SELECT * FROM purchase_invoices WHERE id = ?", (invoice_id,)).fetchone()
    if not row:
        raise FinanceError("采购发票不存在", 404)
    check_scope(row["store_id"])
    return row


def serialize_invoice(conn, row):
    supplier = conn.execute("SELECT supplier_name FROM suppliers WHERE id = ?", (row["supplier_id"],)).fetchone()
    store = conn.execute("SELECT name FROM stores WHERE id = ?", (row["store_id"],)).fetchone()
    allocations = []
    for item in conn.execute(
        """SELECT a.*, t.source_document_no, t.product_name, t.business_date, t.invoice_status,
                  t.amount_including_tax_cents payable_cents,
                  t.purchase_order_id, t.purchase_order_item_id, t.source_type, t.source_id
           FROM purchase_invoice_allocations a
           JOIN supplier_account_transactions t ON t.id = a.payable_transaction_id
           WHERE a.invoice_id = ? ORDER BY a.id""", (row["id"],)
    ):
        allocations.append({
            "id": item["id"], "payableTransactionId": item["payable_transaction_id"],
            "documentNo": item["source_document_no"], "productName": item["product_name"],
            "businessDate": item["business_date"], "invoiceStatus": item["invoice_status"],
            "amountExcludingTax": amount(item["amount_excluding_tax_cents"]),
            "taxAmount": amount(item["tax_amount_cents"]),
            "amountIncludingTax": amount(item["amount_including_tax_cents"]),
            "quantity": item["quantity"], "payableAmount": amount(item["payable_cents"]),
            "purchaseOrderId": item["purchase_order_id"],
            "purchaseOrderItemId": item["purchase_order_item_id"],
            "sourceType": item["source_type"], "sourceId": item["source_id"],
        })
    pending = 0
    for item in conn.execute(
        """SELECT a.*, COALESCE((SELECT SUM(m.amount_including_tax_cents)
           FROM purchase_invoice_order_matches m WHERE m.order_allocation_id = a.id), 0) matched
           FROM purchase_invoice_order_allocations a WHERE a.invoice_id = ? ORDER BY a.id""", (row["id"],),
    ):
        remaining = item["amount_including_tax_cents"] - item["matched"]
        pending += remaining
        allocations.append({
            "id": f"order-allocation-{item['id']}", "payableTransactionId": None,
            "purchaseOrderId": item["purchase_order_id"], "purchaseOrderItemId": item["purchase_order_item_id"],
            "sourceType": "purchase_order", "sourceId": item["purchase_order_id"],
            "documentNo": item["document_no"], "productName": item["product_name"],
            "businessDate": item["business_date"], "payableAmount": amount(item["source_amount_cents"]),
            "amountExcludingTax": amount(item["amount_excluding_tax_cents"]), "taxAmount": amount(item["tax_amount_cents"]),
            "amountIncludingTax": amount(item["amount_including_tax_cents"]), "quantity": item["quantity"],
            "matchedAmount": amount(item["matched"]),
            "pendingInboundAmount": amount(remaining) if row["status"] == "confirmed" else 0,
            "invoiceStatus": "unbilled" if row["status"] != "confirmed" else "difference" if row["has_difference"] else "billed",
        })
    return {
        "id": row["id"], "supplierId": row["supplier_id"], "supplierName": supplier["supplier_name"],
        "storeName": store["name"],
        "storeId": row["store_id"], "invoiceNo": row["invoice_no"], "invoiceDate": row["invoice_date"],
        "businessDate": row["business_date"], "invoiceType": row["invoice_type"],
        "amountExcludingTax": amount(row["amount_excluding_tax_cents"]),
        "taxAmount": amount(row["tax_amount_cents"]),
        "amountIncludingTax": amount(row["amount_including_tax_cents"]),
        "differenceReason": row["difference_reason"], "hasDifference": bool(row["has_difference"]),
        "attachments": json.loads(row["attachments"]), "remark": row["remark"],
        "status": row["status"], "version": row["version"], "createdBy": row["created_by"],
        "createdAt": row["created_at"], "updatedAt": row["updated_at"],
        "confirmedBy": row["confirmed_by"], "confirmedAt": row["confirmed_at"],
        "reversedAt": row["reversed_at"], "lockedAt": row["locked_at"], "allocations": allocations,
        "pendingInboundAmount": amount(pending) if row["status"] == "confirmed" else 0,
    }


def document_context(conn, required=False):
    order_id, inbound_id = request.args.get("purchaseOrderId"), request.args.get("inboundId")
    if order_id is not None and inbound_id is not None:
        raise FinanceError("采购订单和直接入库单筛选不能同时使用")
    if order_id is None and inbound_id is None:
        if required:
            raise FinanceError("请选择采购订单或直接入库单")
        return None
    document_id = positive_id(order_id if order_id is not None else inbound_id)
    table = "purchase_orders" if order_id is not None else "stock_inbounds"
    document = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (document_id,)).fetchone()
    if not document:
        raise FinanceError("来源单据不存在", 404)
    check_scope(document["store_id"])
    if inbound_id is not None and document["purchase_order_id"]:
        raise FinanceError("采购订单入库请使用采购订单筛选")
    return document, "purchase_order_id" if order_id is not None else "source_id", document_id


@purchase_invoices_bp.route("/purchase-invoices/context")
@require_admin_permission("admin.route.purchase.invoices")
@finance_errors
def invoice_context():
    with get_db() as conn:
        document, column, document_id = document_context(conn, required=True)
        store = conn.execute("SELECT name FROM stores WHERE id = ?", (document["store_id"],)).fetchone()
        if column == "purchase_order_id":
            sources = order_source_options(conn, document["store_id"], order_id=document_id)
            suppliers = {}
            for source in sources:
                supplier_id = source["supplierId"]
                if supplier_id not in suppliers:
                    name = conn.execute("SELECT supplier_name FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
                    suppliers[supplier_id] = {"id": supplier_id, "supplierName": name["supplier_name"], "availableAmount": 0}
                suppliers[supplier_id]["availableAmount"] += source["availableAmount"]
            return jsonify({
                "storeId": document["store_id"], "storeName": store["name"] if store else "",
                "suppliers": [{**row, "availableAmount": amount(cents(row["availableAmount"]))} for row in suppliers.values()],
                "availableAmount": amount(sum(cents(row["availableAmount"]) for row in suppliers.values())),
            })
        suppliers = conn.execute(
            f"""SELECT s.id, s.supplier_name,
                       SUM(CASE WHEN t.locked_at IS NULL THEN
                           MAX(0, t.amount_including_tax_cents - t.billed_cents) ELSE 0 END) available
                FROM supplier_account_transactions t JOIN suppliers s ON s.id = t.supplier_id
                WHERE t.{column} = ? AND t.store_id = ? AND t.source_type = 'stock_inbound'
                  AND t.transaction_type IN ('PURCHASE_INBOUND', 'INDEPENDENT_PURCHASE_INBOUND')
                  AND {effective_sql()}
                GROUP BY s.id, s.supplier_name ORDER BY s.id""",
            (document_id, document["store_id"]),
        ).fetchall()
        return jsonify({
            "storeId": document["store_id"], "storeName": store["name"] if store else "",
            "suppliers": [{"id": row["id"], "supplierName": row["supplier_name"],
                           "availableAmount": amount(row["available"])} for row in suppliers],
            "availableAmount": amount(sum(row["available"] for row in suppliers)),
        })


@purchase_invoices_bp.route("/purchase-invoices/sources")
@require_admin_permission("admin.route.purchase.invoices")
@finance_errors
def invoice_sources():
    supplier_id = positive_id(request.args.get("supplierId"))
    store_id = positive_id(request.args.get("storeId"))
    with get_db() as conn:
        supplier_store(conn, supplier_id, store_id)
        sources = order_source_options(conn, store_id, supplier_id=supplier_id)
        invoice_id = request.args.get("invoiceId")
        existing_ids = set()
        if invoice_id:
            invoice = invoice_row(conn, positive_id(invoice_id))
            if invoice["supplier_id"] != supplier_id or invoice["store_id"] != store_id:
                raise FinanceError("发票来源的供应商或门店不一致")
            existing_ids = {row[0] for row in conn.execute(
                "SELECT payable_transaction_id FROM purchase_invoice_allocations WHERE invoice_id = ?", (invoice["id"],),
            )}
        from routes.supplier_finance import serialize_transaction
        for row in conn.execute(
            f"""SELECT t.* FROM supplier_account_transactions t
                WHERE t.store_id = ? AND t.supplier_id = ? AND t.source_type = 'stock_inbound'
                  AND t.transaction_type IN ('PURCHASE_INBOUND', 'INDEPENDENT_PURCHASE_INBOUND')
                  AND t.locked_at IS NULL AND {effective_sql()}""", (store_id, supplier_id),
        ):
            available = row["amount_including_tax_cents"] - row["billed_cents"]
            if available > 0 and (not row["purchase_order_item_id"] or row["id"] in existing_ids):
                entries = conn.execute(
                    """SELECT a.tax_amount_cents, a.quantity FROM purchase_invoice_allocations a
                       JOIN purchase_invoices i ON i.id = a.invoice_id
                       WHERE a.payable_transaction_id = ? AND i.status = 'confirmed'
                       UNION ALL SELECT m.tax_amount_cents, m.quantity FROM purchase_invoice_order_matches m
                       JOIN purchase_invoice_order_allocations a ON a.id = m.order_allocation_id
                       JOIN purchase_invoices i ON i.id = a.invoice_id
                       WHERE m.payable_transaction_id = ? AND i.status = 'confirmed'""", (row["id"], row["id"]),
                ).fetchall()
                received = conn.execute(
                    "SELECT received_qty FROM stock_inbound_items WHERE id = ?", (row["source_item_id"],),
                ).fetchone()
                tax_known = not row["manual_billed_cents"]
                qty_known = tax_known and all(quantity(entry["quantity"]) > 0 for entry in entries)
                suggestion = invoice_allocation_suggestion(
                    row, available, received["received_qty"] if received else 0, used=row["billed_cents"],
                    used_tax=sum(entry["tax_amount_cents"] for entry in entries) if tax_known else None,
                    used_qty=sum((quantity(entry["quantity"]) for entry in entries), quantity(0)) if qty_known else None,
                )
                sources.append({**serialize_transaction(row), "availableAmount": amount(available),
                                "suggestedAllocation": suggestion})
        return jsonify({"items": sources})


def invoice_values(conn, data):
    supplier_id, store_id = supplier_store(conn, data.get("supplierId"), data.get("storeId"))
    invoice_no = text(data.get("invoiceNo"), 100)
    if not invoice_no:
        raise FinanceError("发票号码不能为空")
    invoice_type = text(data.get("invoiceType"), 40)
    if not invoice_type:
        raise FinanceError("请选择发票类型")
    base, tax = cents(data.get("amountExcludingTax")), cents(data.get("taxAmount"))
    inclusive = cents(data.get("amountIncludingTax", amount(base + tax)))
    if inclusive != base + tax:
        raise FinanceError("价税合计必须等于未税金额加税额")
    if inclusive <= 0:
        raise FinanceError("发票含税金额必须大于零")
    allocations = data.get("allocations", [])
    if not isinstance(allocations, list) or len(allocations) > 500:
        raise FinanceError("发票分配明细必须是最多 500 项的数组")
    if "hasDifference" in data and not isinstance(data["hasDifference"], bool):
        raise FinanceError("发票差异开关必须是布尔值")
    return {
        "supplier_id": supplier_id, "store_id": store_id, "invoice_no": invoice_no,
        "invoice_date": business_date(data.get("invoiceDate")),
        "business_date": business_date(data.get("businessDate") or data.get("invoiceDate")),
        "invoice_type": invoice_type, "base": base, "tax": tax, "inclusive": inclusive,
        "difference_reason": text(data.get("differenceReason")),
        "has_difference": int(bool(data.get("hasDifference"))),
        "attachments": attachments_value(conn, data.get("attachments", []), store_id),
        "remark": text(data.get("remark")),
        "allocations": allocations,
    }


def invoice_allocations(conn, values):
    results, seen = [], set()
    total_base = total_tax = total_inclusive = 0
    order_totals = {}
    for entry in values["allocations"]:
        if not isinstance(entry, dict):
            raise FinanceError("发票分配明细格式错误")
        is_order = entry.get("sourceType") == "purchase_order"
        if is_order and entry.get("payableTransactionId"):
            raise FinanceError("发票分配不能同时指定订单明细和应付来源")
        if is_order:
            row = load_order_source(conn, entry.get("purchaseOrderItemId"), values["supplier_id"], values["store_id"])
            key = ("order", row["id"])
            used, old_qty, actual = order_usage(conn, row["id"])
            existing = []
            old = used
            manual = 0
            capacity = order_capacity(conn, row, actual)
            row["source_amount_cents"] = max(row["amount_including_tax_cents"], actual)
            actual_qty = quantity(row["actual_purchase_qty"] if row["actual_purchase_qty"] is not None else row["ordered_qty"])
        else:
            row = load_payable(conn, entry.get("payableTransactionId"), values["supplier_id"], values["store_id"], invoice=True)
            key = ("payable", row["id"])
            existing = conn.execute(
                """SELECT a.amount_including_tax_cents, a.quantity
                   FROM purchase_invoice_allocations a JOIN purchase_invoices i ON i.id = a.invoice_id
                   WHERE a.payable_transaction_id = ? AND i.status = 'confirmed'
                   UNION ALL SELECT m.amount_including_tax_cents, m.quantity FROM purchase_invoice_order_matches m
                   JOIN purchase_invoice_order_allocations a ON a.id = m.order_allocation_id
                   JOIN purchase_invoices i ON i.id = a.invoice_id
                   WHERE m.payable_transaction_id = ? AND i.status = 'confirmed'""", (row["id"], row["id"]),
            ).fetchall()
            old = sum(item["amount_including_tax_cents"] for item in existing)
            old_qty = sum((quantity(item["quantity"]) for item in existing), quantity(0))
            manual, capacity = row["manual_billed_cents"], row["amount_including_tax_cents"]
            received = conn.execute("SELECT received_qty FROM stock_inbound_items WHERE id=?", (row["source_item_id"],)).fetchone()
            actual_qty = quantity(received["received_qty"]) if received else None
        if key in seen:
            raise FinanceError("同一开票来源不能重复分配")
        seen.add(key)
        base, tax = cents(entry.get("amountExcludingTax")), cents(entry.get("taxAmount"))
        inclusive = cents(entry.get("amountIncludingTax", amount(base + tax)))
        if inclusive != base + tax or inclusive <= 0:
            raise FinanceError("发票分配价税合计不正确")
        if old + manual + inclusive > capacity:
            raise FinanceError("发票分配超过来源可开票金额", 409)
        if abs(tax - proportional_tax(row, inclusive)) > 1:
            values["has_difference"] = 1
        qty = quantity(entry.get("quantity", 0))
        if actual_qty is not None and qty > 0:
            total_qty = qty + old_qty
            quantity_capacity = row["source_amount_cents"] if is_order else capacity
            if total_qty > actual_qty or (
                not manual and old + inclusive == quantity_capacity and total_qty != actual_qty
            ):
                values["has_difference"] = 1
        item_id = row["id"] if is_order else row["purchase_order_item_id"]
        if item_id:
            order_totals[item_id] = order_totals.get(item_id, 0) + inclusive
        results.append(({**dict(row), "invoice_source": "order" if is_order else "payable"}, base, tax, inclusive, qty))
        total_base += base
        total_tax += tax
        total_inclusive += inclusive
    if total_inclusive != values["inclusive"] or total_base != values["base"] or total_tax != values["tax"]:
        raise FinanceError("发票总额必须等于分配明细合计")
    for item_id, added in order_totals.items():
        source = load_order_source(conn, item_id, values["supplier_id"], values["store_id"])
        used, _, actual = order_usage(conn, item_id)
        if used + added > order_capacity(conn, source, actual):
            raise FinanceError("订单明细累计开票超过可开票金额", 409)
    if values["has_difference"] and not values["difference_reason"]:
        raise FinanceError("发票存在差异时必须填写差异原因")
    return results


def insert_allocations(conn, invoice_id, allocations):
    conn.executemany(
        """INSERT INTO purchase_invoice_allocations (
            invoice_id, payable_transaction_id, amount_excluding_tax_cents,
            tax_amount_cents, amount_including_tax_cents, quantity
        ) VALUES (?, ?, ?, ?, ?, ?)""",
        [(invoice_id, row["id"], base, tax, inclusive, str(qty))
         for row, base, tax, inclusive, qty in allocations if row["invoice_source"] == "payable"],
    )
    conn.executemany(
        """INSERT INTO purchase_invoice_order_allocations (
           invoice_id, purchase_order_id, purchase_order_item_id, document_no, product_name,
           business_date, source_amount_cents, amount_excluding_tax_cents, tax_amount_cents,
           amount_including_tax_cents, quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(invoice_id, row["order_id"], row["id"], row["order_no"], row["product_name"], row["order_date"],
          row["source_amount_cents"], base, tax, inclusive, str(qty))
         for row, base, tax, inclusive, qty in allocations if row["invoice_source"] == "order"],
    )


@purchase_invoices_bp.route("/purchase-invoices")
@require_admin_permission("admin.route.purchase.invoices")
@finance_errors
def list_invoices():
    with get_db() as conn:
        scoped, params = scope_sql(alias="i", store_id=request.args.get("storeId", type=int))
        sql = f"SELECT i.* FROM purchase_invoices i WHERE 1=1 {scoped}"
        context = document_context(conn)
        if context:
            document, column, document_id = context
            sql += f""" AND i.store_id = ? AND (EXISTS (
                SELECT 1 FROM purchase_invoice_allocations a
                JOIN supplier_account_transactions t ON t.id = a.payable_transaction_id
                WHERE a.invoice_id = i.id AND t.source_type = 'stock_inbound'
                  AND t.{column} = ?)"""
            params.extend((document["store_id"], document_id))
            if column == "purchase_order_id":
                sql += """ OR EXISTS (SELECT 1 FROM purchase_invoice_order_allocations a
                          WHERE a.invoice_id = i.id AND a.purchase_order_id = ?)"""
                params.append(document_id)
            sql += ")"
        for column, argument in (("supplier_id", "supplierId"), ("status", "status"), ("invoice_no", "invoiceNo")):
            if request.args.get(argument):
                sql += f" AND i.{column} = ?"
                params.append(request.args[argument])
        if request.args.get("hasDifference") in ("true", "false"):
            sql += " AND i.has_difference=?"
            params.append(int(request.args["hasDifference"] == "true"))
        for column, argument, operator in (("business_date", "startDate", ">="), ("business_date", "endDate", "<=")):
            if request.args.get(argument):
                sql += f" AND i.{column} {operator} ?"
                params.append(business_date(request.args[argument]))
        rows = conn.execute(sql + " ORDER BY i.business_date DESC, i.id DESC", params).fetchall()
        items = [serialize_invoice(conn, row) for row in rows]
        keyword = text(request.args.get("keyword")).lower()
        items = [item for item in items if not keyword or keyword in
                 (item["invoiceNo"] + item["supplierName"] + item["remark"]).lower()]
        return jsonify({"items": items, "total": len(items)})


@purchase_invoices_bp.route("/purchase-invoices/<int:invoice_id>")
@require_admin_permission("admin.route.purchase.invoices")
@finance_errors
def get_invoice(invoice_id):
    with get_db() as conn:
        return jsonify(serialize_invoice(conn, invoice_row(conn, invoice_id)))


@purchase_invoices_bp.route("/purchase-invoices", methods=["POST"])
@require_admin_permission("admin.purchase.invoice.create")
@finance_errors
def create_invoice():
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        values = invoice_values(conn, data)
        replay, token = idempotent_result(conn, "purchase-invoice:create", data)
        if replay:
            return jsonify(replay)
        if conn.execute(
            "SELECT 1 FROM purchase_invoices WHERE supplier_id=? AND invoice_no=?",
            (values["supplier_id"], values["invoice_no"]),
        ).fetchone():
            raise FinanceError("同一供应商下发票号码已存在", 409)
        allocations = invoice_allocations(conn, values)
        cursor = conn.execute(
            """INSERT INTO purchase_invoices (
                supplier_id, store_id, invoice_no, invoice_date, business_date, invoice_type,
                amount_excluding_tax_cents, tax_amount_cents, amount_including_tax_cents,
                difference_reason, has_difference, attachments, remark, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (values["supplier_id"], values["store_id"], values["invoice_no"], values["invoice_date"],
             values["business_date"], values["invoice_type"], values["base"], values["tax"],
             values["inclusive"], values["difference_reason"], values["has_difference"],
             values["attachments"], values["remark"], current_identity(), now(), now()),
        )
        insert_allocations(conn, cursor.lastrowid, allocations)
        return jsonify(save_operation(conn, token, {"success": True, "invoice": serialize_invoice(
            conn, invoice_row(conn, cursor.lastrowid))})), 201


@purchase_invoices_bp.route("/purchase-invoices/<int:invoice_id>", methods=["PUT"])
@require_admin_permission("admin.purchase.invoice.edit")
@finance_errors
def edit_invoice(invoice_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = invoice_row(conn, invoice_id)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("只有未确认发票可以修改", 409)
        required_version(data, row)
        values = invoice_values(conn, data)
        if values["supplier_id"] != row["supplier_id"] or values["store_id"] != row["store_id"]:
            raise FinanceError("发票供应商和门店不能修改", 409)
        if conn.execute(
            "SELECT 1 FROM purchase_invoices WHERE supplier_id=? AND invoice_no=? AND id<>?",
            (row["supplier_id"], values["invoice_no"], invoice_id),
        ).fetchone():
            raise FinanceError("同一供应商下发票号码已存在", 409)
        allocations = invoice_allocations(conn, values)
        conn.execute(
            """UPDATE purchase_invoices SET invoice_no=?, invoice_date=?, business_date=?, invoice_type=?,
               amount_excluding_tax_cents=?, tax_amount_cents=?, amount_including_tax_cents=?,
               difference_reason=?, has_difference=?, attachments=?, remark=?, status='draft',
               version=version+1, updated_at=?
               WHERE id=?""",
            (values["invoice_no"], values["invoice_date"], values["business_date"], values["invoice_type"],
             values["base"], values["tax"], values["inclusive"], values["difference_reason"],
             values["has_difference"], values["attachments"], values["remark"], now(), invoice_id),
        )
        conn.execute("DELETE FROM purchase_invoice_allocations WHERE invoice_id=?", (invoice_id,))
        conn.execute("DELETE FROM purchase_invoice_order_allocations WHERE invoice_id=?", (invoice_id,))
        insert_allocations(conn, invoice_id, allocations)
        return jsonify({"success": True, "invoice": serialize_invoice(conn, invoice_row(conn, invoice_id))})


@purchase_invoices_bp.route("/purchase-invoices/<int:invoice_id>", methods=["DELETE"])
@require_admin_permission("admin.purchase.invoice.delete")
@finance_errors
def delete_invoice(invoice_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = invoice_row(conn, invoice_id)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("已确认发票不能直接删除", 409)
        required_version(data, row)
        if row["confirmed_at"]:
            conn.execute(
                "UPDATE purchase_invoices SET status='cancelled', version=version+1, updated_at=? WHERE id=?",
                (now(), invoice_id),
            )
        else:
            conn.execute("DELETE FROM purchase_invoices WHERE id=?", (invoice_id,))
        return jsonify({"success": True, "deleted": True})


@purchase_invoices_bp.route("/purchase-invoices/<int:invoice_id>/confirm", methods=["POST"])
@require_admin_permission("admin.purchase.invoice.confirm")
@finance_errors
def confirm_invoice(invoice_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = invoice_row(conn, invoice_id)
        replay, token = idempotent_result(conn, f"purchase-invoice:{invoice_id}:confirm", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "confirmed":
            return jsonify(save_operation(conn, token, {"success": True, "invoice": serialize_invoice(conn, row)}))
        required_version(data, row)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("发票状态不允许确认", 409)
        from utils.supplier_periods import ensure_period_open
        ensure_period_open(conn, row["supplier_id"], row["store_id"], row["business_date"])
        serialized = serialize_invoice(conn, row)
        values = invoice_values(conn, serialized)
        allocations = invoice_allocations(conn, values)
        conn.execute(
            """UPDATE purchase_invoices SET status='confirmed', version=version+1, has_difference=?,
               confirmed_by=?, confirmed_at=?, reversed_at=NULL, updated_at=? WHERE id=?""",
            (values["has_difference"], current_identity(), now(), now(), invoice_id),
        )
        for source, *_ in allocations:
            if source["invoice_source"] == "order":
                sync_order_invoices(conn, source["id"])
            else:
                refresh_invoice(conn, source["id"])
        confirmed = serialize_invoice(conn, invoice_row(conn, invoice_id))
        conn.execute(
            """INSERT INTO purchase_invoice_events (invoice_id, document_version, action, created_by, created_at, allocations_json)
               VALUES (?, ?, 'confirm', ?, ?, ?)""",
            (invoice_id, row["version"] + 1, current_identity(), now(), json.dumps(confirmed["allocations"])),
        )
        return jsonify(save_operation(conn, token, {"success": True, "invoice": confirmed}))


@purchase_invoices_bp.route("/purchase-invoices/<int:invoice_id>/reverse-confirm", methods=["POST"])
@require_admin_permission("admin.purchase.invoice.reverse_confirm")
@finance_errors
def reverse_invoice(invoice_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = invoice_row(conn, invoice_id)
        replay, token = idempotent_result(conn, f"purchase-invoice:{invoice_id}:reverse", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "reversed":
            return jsonify(save_operation(conn, token, {"success": True, "invoice": serialize_invoice(conn, row)}))
        required_version(data, row)
        if row["status"] != "confirmed" or row["locked_at"]:
            raise FinanceError("只有未锁定已确认发票可以撤销", 409)
        allocations = list(conn.execute(
            """SELECT payable_transaction_id FROM purchase_invoice_allocations WHERE invoice_id=?
               UNION SELECT m.payable_transaction_id FROM purchase_invoice_order_matches m
               JOIN purchase_invoice_order_allocations a ON a.id = m.order_allocation_id WHERE a.invoice_id=?""",
            (invoice_id, invoice_id),
        ))
        order_item_ids = set()
        for source in allocations:
            payable = load_payable(conn, source["payable_transaction_id"], row["supplier_id"], row["store_id"], invoice=True)
            if payable["purchase_order_item_id"]:
                order_item_ids.add(payable["purchase_order_item_id"])
        conn.execute(
            "UPDATE purchase_invoices SET status='reversed', version=version+1, reversed_at=?, updated_at=? WHERE id=?",
            (now(), now(), invoice_id),
        )
        conn.execute(
            """DELETE FROM purchase_invoice_order_matches WHERE order_allocation_id IN
               (SELECT id FROM purchase_invoice_order_allocations WHERE invoice_id=?)""", (invoice_id,),
        )
        for source in allocations:
            refresh_invoice(conn, source["payable_transaction_id"])
        for item_id in order_item_ids:
            sync_order_invoices(conn, item_id)
        conn.execute(
            """INSERT INTO purchase_invoice_events (invoice_id, document_version, action, created_by, created_at, allocations_json)
               VALUES (?, ?, 'reverse', ?, ?, ?)""",
            (invoice_id, row["version"] + 1, current_identity(), now(), json.dumps([dict(item) for item in allocations])),
        )
        return jsonify(save_operation(conn, token, {"success": True, "invoice": serialize_invoice(
            conn, invoice_row(conn, invoice_id))}))
