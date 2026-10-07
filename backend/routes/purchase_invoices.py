"""Purchase invoice registration and allocation APIs."""

import json

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.supplier_ledger import (
    FinanceError, amount, business_date, cents, check_scope,
    idempotent_result, now, save_operation, scope_sql,
)
from utils.supplier_settlement import (
    attachments_value, load_payable, positive_id, quantity, supplier_store, text,
    refresh_invoice, required_version, proportional_tax,
)
from routes.supplier_finance import finance_errors


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
                  t.amount_including_tax_cents payable_cents
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
        "reversedAt": row["reversed_at"], "allocations": allocations,
    }


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
    for entry in values["allocations"]:
        if not isinstance(entry, dict):
            raise FinanceError("发票分配明细格式错误")
        transaction_id = positive_id(entry.get("payableTransactionId"))
        if transaction_id in seen:
            raise FinanceError("同一应付不能重复分配")
        seen.add(transaction_id)
        row = load_payable(conn, transaction_id, values["supplier_id"], values["store_id"], invoice=True)
        base, tax = cents(entry.get("amountExcludingTax")), cents(entry.get("taxAmount"))
        inclusive = cents(entry.get("amountIncludingTax", amount(base + tax)))
        if inclusive != base + tax or inclusive <= 0:
            raise FinanceError("发票分配价税合计不正确")
        existing = conn.execute(
            """SELECT a.amount_including_tax_cents, a.quantity
               FROM purchase_invoice_allocations a JOIN purchase_invoices i ON i.id = a.invoice_id
               WHERE a.payable_transaction_id = ? AND i.status = 'confirmed'""", (transaction_id,),
        ).fetchall()
        old = sum(item["amount_including_tax_cents"] for item in existing)
        if old + row["manual_billed_cents"] + inclusive > row["amount_including_tax_cents"]:
            raise FinanceError("发票分配超过应付可开票金额", 409)
        if abs(tax - proportional_tax(row, inclusive)) > 1:
            values["has_difference"] = 1
        qty = quantity(entry.get("quantity", 0))
        received = conn.execute("SELECT received_qty FROM stock_inbound_items WHERE id=?", (row["source_item_id"],)).fetchone()
        if received and qty > 0:
            total_qty = qty + sum((quantity(item["quantity"]) for item in existing), quantity(0))
            actual_qty = quantity(received["received_qty"])
            if total_qty > actual_qty or (
                not row["manual_billed_cents"] and old + inclusive == row["amount_including_tax_cents"] and total_qty != actual_qty
            ):
                values["has_difference"] = 1
        results.append((row, base, tax, inclusive, qty))
        total_base += base
        total_tax += tax
        total_inclusive += inclusive
    if total_inclusive != values["inclusive"] or total_base != values["base"] or total_tax != values["tax"]:
        raise FinanceError("发票总额必须等于分配明细合计")
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
         for row, base, tax, inclusive, qty in allocations],
    )


@purchase_invoices_bp.route("/purchase-invoices")
@require_admin_permission("admin.route.purchase.invoices")
@finance_errors
def list_invoices():
    with get_db() as conn:
        scoped, params = scope_sql(alias="i", store_id=request.args.get("storeId", type=int))
        sql = f"SELECT i.* FROM purchase_invoices i WHERE 1=1 {scoped}"
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
            refresh_invoice(conn, source["id"])
        conn.execute(
            """INSERT INTO purchase_invoice_events (invoice_id, document_version, action, created_by, created_at, allocations_json)
               VALUES (?, ?, 'confirm', ?, ?, ?)""",
            (invoice_id, row["version"] + 1, current_identity(), now(), json.dumps(serialize_invoice(conn, row)["allocations"])),
        )
        return jsonify(save_operation(conn, token, {"success": True, "invoice": serialize_invoice(
            conn, invoice_row(conn, invoice_id))}))


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
            "SELECT payable_transaction_id FROM purchase_invoice_allocations WHERE invoice_id=?",
            (invoice_id,),
        ))
        for source in allocations:
            load_payable(conn, source["payable_transaction_id"], row["supplier_id"], row["store_id"], invoice=True)
        conn.execute(
            "UPDATE purchase_invoices SET status='reversed', version=version+1, reversed_at=?, updated_at=? WHERE id=?",
            (now(), now(), invoice_id),
        )
        for source in allocations:
            refresh_invoice(conn, source["payable_transaction_id"])
        conn.execute(
            """INSERT INTO purchase_invoice_events (invoice_id, document_version, action, created_by, created_at, allocations_json)
               VALUES (?, ?, 'reverse', ?, ?, ?)""",
            (invoice_id, row["version"] + 1, current_identity(), now(), json.dumps([dict(item) for item in allocations])),
        )
        return jsonify(save_operation(conn, token, {"success": True, "invoice": serialize_invoice(
            conn, invoice_row(conn, invoice_id))}))
