"""Supplier payment drafts, audited bank postings and independent balance allocations."""

import json
import os
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from utils.auth import current_identity, require_admin_permission, require_any_admin_permission
from utils.db import get_db
from utils.supplier_ledger import (
    FinanceError, amount, balance, business_date, cents, check_scope, effective_sql,
    idempotent_result, now, save_operation, scope_sql,
)
from utils.supplier_settlement import (
    INVOICE_RULE_KEY, PAYABLE_TYPES, add_ledger, allocation_values, apply_allocations,
    attachments_value, balance_available, invoice_payment_check, positive_id, post_bank,
    payable_available_cents, require_invoice, required_version, reverse_ledger, supplier_store, text,
)
from routes.supplier_finance import finance_errors, serialize_transaction, supplier_row


supplier_payments_bp = Blueprint("supplier_payments", __name__, url_prefix="/api")
READ = "admin.route.finance.supplier_payments"


def payment_row(conn, payment_id):
    row = conn.execute("SELECT * FROM supplier_payments WHERE id = ?", (payment_id,)).fetchone()
    if not row:
        raise FinanceError("付款单不存在", 404)
    check_scope(row["store_id"])
    return row


def serialize_payment(conn, row):
    supplier = conn.execute("SELECT supplier_name FROM suppliers WHERE id = ?", (row["supplier_id"],)).fetchone()
    store = conn.execute("SELECT name FROM stores WHERE id = ?", (row["store_id"],)).fetchone()
    result = {"id": row["id"], "status": row["status"], "version": row["version"],
              "supplierName": supplier["supplier_name"], "storeName": store["name"],
              "invoiceOverride": bool(row["invoice_override"])}
    for source, target in {
        "document_no": "documentNo", "supplier_id": "supplierId", "store_id": "storeId",
        "business_date": "businessDate", "payment_date": "paymentDate", "bank_account_id": "bankAccountId",
        "account_name": "accountName", "payment_method": "paymentMethod", "unbilled_reason": "unbilledReason",
        "created_by": "createdBy", "created_at": "createdAt", "updated_at": "updatedAt",
        "audited_by": "auditedBy", "audited_at": "auditedAt", "reversed_at": "reversedAt", "remark": "remark",
    }.items():
        result[target] = row[source]
    result.update({"paymentAmount": amount(row["payment_cents"]), "advanceAmount": amount(row["advance_cents"]),
                   "allocatedAmount": amount(row["payment_cents"] - row["advance_cents"]),
                   "attachments": json.loads(row["attachments"])})
    result["allocations"] = [
        {"payableTransactionId": item["payable_transaction_id"], "amount": amount(item["amount_cents"]),
         "documentNo": item["source_document_no"], "productName": item["product_name"],
         "businessDate": item["business_date"], "invoiceStatus": item["invoice_status"],
         "payableAmount": amount(item["payable_cents"])}
        for item in conn.execute(
            """SELECT a.*, t.source_document_no, t.product_name, t.business_date, t.invoice_status,
                      t.amount_including_tax_cents payable_cents FROM supplier_payment_allocations a
               JOIN supplier_account_transactions t ON t.id = a.payable_transaction_id
               WHERE a.payment_id = ? ORDER BY a.id""", (row["id"],)
        )
    ]
    result["bankTransactions"] = [
        {"id": item["id"], "bankAccountId": item["bank_account_id"], "businessDate": item["business_date"],
         "change": amount(item["delta_cents"]), "balanceAfter": amount(item["balance_after_cents"]),
         "createdBy": item["created_by"], "createdAt": item["created_at"], "reversalOfId": item["reversal_of_id"]}
        for item in conn.execute(
            "SELECT * FROM bank_account_transactions WHERE source_type='supplier_payment' AND source_id=? ORDER BY id",
            (row["id"],),
        )
    ]
    return result


def next_number(conn, date):
    prefix = "FK" + date.replace("-", "")
    rows = conn.execute("SELECT document_no FROM supplier_payments WHERE document_no LIKE ?", (prefix + "%",))
    suffixes = [str(row["document_no"])[len(prefix):] for row in rows]
    return prefix + f"{max([int(value) for value in suffixes if value.isdigit()] or [0]) + 1:03d}"


def payment_values(conn, data):
    supplier_id, store_id = supplier_store(conn, data.get("supplierId"), data.get("storeId"))
    bank_id = positive_id(data.get("bankAccountId"))
    bank = conn.execute("SELECT * FROM bank_accounts WHERE id = ? AND store_id = ?", (bank_id, store_id)).fetchone()
    if not bank:
        raise FinanceError("请选择该门店的银行账户")
    paid = cents(data.get("paymentAmount"))
    if paid <= 0:
        raise FinanceError("本次实际付款必须大于零；使用历史余额请走余额核销")
    entries = allocation_values(conn, data, supplier_id, store_id)
    date = business_date(data.get("businessDate"))
    if any(row["business_date"] > date for row, _ in entries):
        raise FinanceError("付款业务日期不能早于来源应付日期")
    allocated = sum(value for _, value in entries)
    if allocated > paid:
        raise FinanceError("应付核销合计不能超过本次实际付款")
    if not text(data.get("paymentMethod"), 80):
        raise FinanceError("请选择付款方式")
    if "invoiceOverride" in data and not isinstance(data["invoiceOverride"], bool):
        raise FinanceError("财务豁免必须是布尔值")
    return (supplier_id, store_id, date,
            business_date(data.get("paymentDate")), bank_id, bank["account_name"],
            text(data.get("paymentMethod"), 80), paid, paid - allocated,
            text(data.get("unbilledReason")), int(data.get("invoiceOverride", False)),
            attachments_value(conn, data.get("attachments", []), store_id), text(data.get("remark"))), entries


def replace_payment_allocations(conn, payment_id, entries):
    conn.execute("DELETE FROM supplier_payment_allocations WHERE payment_id = ?", (payment_id,))
    conn.executemany(
        "INSERT INTO supplier_payment_allocations (payment_id, payable_transaction_id, amount_cents) VALUES (?, ?, ?)",
        [(payment_id, row["id"], value) for row, value in entries],
    )


def serialize_balance_allocation(conn, row):
    source = conn.execute("SELECT source_document_no FROM supplier_account_transactions WHERE id=?",
                          (row["source_transaction_id"],)).fetchone()
    return {
        "id": row["id"], "supplierId": row["supplier_id"], "storeId": row["store_id"],
        "sourceTransactionId": row["source_transaction_id"], "sourceDocumentNo": source["source_document_no"],
        "kind": row["kind"], "businessDate": row["business_date"], "amount": amount(row["amount_cents"]),
        "documentNo": f"HX{row['id']:06d}", "unbilledReason": row["unbilled_reason"],
        "invoiceOverride": bool(row["invoice_override"]), "remark": row["remark"],
        "status": row["status"], "version": row["version"], "createdBy": row["created_by"],
        "auditedAt": row["audited_at"], "reversedAt": row["reversed_at"],
        "allocations": [
            {"payableTransactionId": entry["payable_transaction_id"], "documentNo": entry["source_document_no"],
             "productName": entry["product_name"], "businessDate": entry["business_date"],
             "payableAmount": amount(entry["amount_including_tax_cents"]), "invoiceStatus": entry["invoice_status"],
             "amount": amount(entry["amount_cents"])}
            for entry in conn.execute(
                """SELECT a.amount_cents,a.payable_transaction_id,t.* FROM supplier_settlement_allocations a
                   JOIN supplier_account_transactions t ON t.id=a.payable_transaction_id
                   WHERE a.source_type='supplier_balance' AND a.source_id=? ORDER BY a.id""", (row["id"],)
            )
        ],
    }


@supplier_payments_bp.route("/supplier-finance/options")
@require_any_admin_permission(READ, "admin.route.purchase.invoices", "admin.route.finance.payables")
@finance_errors
def finance_options():
    with get_db() as conn:
        scoped, params = scope_sql(alias="s")
        stores = [dict(row) for row in conn.execute(
            f"""SELECT s.id, s.name FROM (SELECT id, name, id store_id FROM stores WHERE status='active') s
                WHERE 1=1 {scoped}""", params,
        )]
        allowed = {row["id"] for row in stores}
        suppliers = [
            {"id": row["id"], "supplierName": row["supplier_name"], "storeId": row["store_id"]}
            for row in conn.execute("SELECT * FROM suppliers WHERE status = 'active'")
            if row["store_id"] is None or row["store_id"] in allowed
        ]
        scoped_bank, bank_params = scope_sql(alias="b")
        banks = [
            {"id": row["id"], "storeId": row["store_id"], "accountName": row["account_name"],
             "bankName": row["bank_name"], "balance": row["balance"]}
            for row in conn.execute(f"SELECT b.* FROM bank_accounts b WHERE 1=1 {scoped_bank}", bank_params)
        ]
        return jsonify({"stores": stores, "suppliers": suppliers, "bankAccounts": banks,
                        "paymentRequireInvoice": require_invoice(conn)})


@supplier_payments_bp.route("/supplier-finance/rules", methods=["GET", "PUT"])
@require_admin_permission(READ)
@finance_errors
def finance_rules():
    with get_db() as conn:
        if request.method == "PUT":
            from utils.auth import admin_permission_granted
            if not admin_permission_granted("admin.finance.supplier_payment.rules"):
                raise FinanceError("无权修改付款规则", 403)
            value = (request.get_json(silent=True) or {}).get("paymentRequireInvoice")
            if not isinstance(value, bool):
                raise FinanceError("见票付款开关必须是布尔值")
            conn.execute(
                """INSERT INTO system_settings (setting_key, setting_value, updated_at) VALUES (?, ?, ?)
                   ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value, updated_at = excluded.updated_at""",
                (INVOICE_RULE_KEY, "true" if value else "false", now()),
            )
        return jsonify({"paymentRequireInvoice": require_invoice(conn)})


@supplier_payments_bp.route("/suppliers/<int:supplier_id>/<kind>/allocatable")
@require_any_admin_permission(READ, "admin.route.purchase.invoices", "admin.route.finance.payables")
@finance_errors
def allocatable(supplier_id, kind):
    if kind not in ("payables", "prepayments", "credits", "invoice-payables"):
        raise FinanceError("来源类型不存在", 404)
    with get_db() as conn:
        supplier_row(conn, supplier_id)
        scoped, params = scope_sql(store_id=request.args.get("storeId", type=int))
        rows = conn.execute(
            f"SELECT * FROM supplier_account_transactions t WHERE supplier_id = ? AND {effective_sql()} {scoped}",
            (supplier_id, *params),
        ).fetchall()
        result = []
        for row in rows:
            if row["locked_at"]:
                continue
            if kind in ("payables", "invoice-payables"):
                if row["transaction_type"] not in PAYABLE_TYPES:
                    continue
                if kind == "invoice-payables" and row["source_type"] != "stock_inbound":
                    continue
                available = (row["amount_including_tax_cents"] - row["billed_cents"]
                             if kind == "invoice-payables" else payable_available_cents(conn, row))
            else:
                available = balance_available(conn, row, "prepayment" if kind == "prepayments" else "credit")
            if available > 0:
                entry = serialize_transaction(row)
                entry["availableAmount"] = amount(available)
                result.append(entry)
        return jsonify({"items": result, "balance": balance(conn, supplier_id, request.args.get("storeId", type=int))})


@supplier_payments_bp.route("/supplier-payments/next-number")
@require_admin_permission(READ)
@finance_errors
def next_payment_number():
    with get_db() as conn:
        return jsonify({"documentNo": next_number(conn, business_date(request.args.get("date") or now()[:10]))})


@supplier_payments_bp.route("/supplier-payments")
@require_admin_permission(READ)
@finance_errors
def list_payments():
    with get_db() as conn:
        scoped, params = scope_sql(alias="p", store_id=request.args.get("storeId", type=int))
        sql = f"SELECT p.* FROM supplier_payments p WHERE 1=1 {scoped}"
        for column, argument in (("status", "status"), ("supplier_id", "supplierId")):
            if request.args.get(argument):
                sql += f" AND p.{column} = ?"
                params.append(request.args[argument])
        for column, operator, argument in (("business_date", ">=", "startDate"), ("business_date", "<=", "endDate")):
            if request.args.get(argument):
                sql += f" AND p.{column} {operator} ?"
                params.append(business_date(request.args[argument]))
        items = [serialize_payment(conn, row) for row in conn.execute(sql + " ORDER BY p.business_date DESC, p.id DESC", params)]
        keyword = text(request.args.get("keyword")).lower()
        items = [row for row in items if not keyword or keyword in (row["documentNo"] + row["supplierName"] + row["remark"]).lower()]
        return jsonify({"items": items, "total": len(items)})


@supplier_payments_bp.route("/supplier-payments/<int:payment_id>")
@require_admin_permission(READ)
@finance_errors
def get_payment(payment_id):
    with get_db() as conn:
        return jsonify(serialize_payment(conn, payment_row(conn, payment_id)))


@supplier_payments_bp.route("/supplier-payments", methods=["POST"])
@require_admin_permission("admin.finance.supplier_payment.create")
@finance_errors
def create_payment():
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        supplier_store(conn, data.get("supplierId"), data.get("storeId"))
        replay, token = idempotent_result(conn, "supplier-payment:create", data)
        if replay:
            return jsonify(replay)
        values, entries = payment_values(conn, data)
        document_no = next_number(conn, values[2])
        cursor = conn.execute(
            """INSERT INTO supplier_payments (
                document_no, supplier_id, store_id, business_date, payment_date, bank_account_id, account_name,
                payment_method, payment_cents, advance_cents, unbilled_reason, invoice_override,
                attachments, remark, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (document_no, *values, current_identity(), now(), now()),
        )
        replace_payment_allocations(conn, cursor.lastrowid, entries)
        return jsonify(save_operation(conn, token, {"success": True, "payment": serialize_payment(
            conn, payment_row(conn, cursor.lastrowid))})), 201


@supplier_payments_bp.route("/supplier-payments/<int:payment_id>", methods=["PUT"])
@require_admin_permission("admin.finance.supplier_payment.edit")
@finance_errors
def edit_payment(payment_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = payment_row(conn, payment_id)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("只有未审核付款单可以修改", 409)
        required_version(data, row)
        values, entries = payment_values(conn, data)
        if row["audited_at"] and (values[0] != row["supplier_id"] or values[1] != row["store_id"]):
            raise FinanceError("有审核历史的付款单不能修改供应商和门店", 409)
        conn.execute(
            """UPDATE supplier_payments SET supplier_id=?, store_id=?, business_date=?, payment_date=?,
               bank_account_id=?, account_name=?, payment_method=?, payment_cents=?, advance_cents=?,
               unbilled_reason=?, invoice_override=?, attachments=?, remark=?, status='draft',
               version=version+1, updated_at=? WHERE id=?""", (*values, now(), payment_id),
        )
        replace_payment_allocations(conn, payment_id, entries)
        return jsonify({"success": True, "payment": serialize_payment(conn, payment_row(conn, payment_id))})


@supplier_payments_bp.route("/supplier-payments/<int:payment_id>", methods=["DELETE"])
@require_admin_permission("admin.finance.supplier_payment.delete")
@finance_errors
def delete_payment(payment_id):
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = payment_row(conn, payment_id)
        required_version(request.get_json(silent=True) or {}, row)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("请先反审核付款单", 409)
        if row["audited_at"]:
            conn.execute("UPDATE supplier_payments SET status='cancelled', version=version+1, updated_at=? WHERE id=?", (now(), payment_id))
        else:
            conn.execute("DELETE FROM supplier_payments WHERE id=?", (payment_id,))
        return jsonify({"success": True, "deleted": True})


@supplier_payments_bp.route("/supplier-payments/<int:payment_id>/audit", methods=["POST"])
@require_admin_permission("admin.finance.supplier_payment.audit")
@finance_errors
def audit_payment(payment_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = payment_row(conn, payment_id)
        replay, token = idempotent_result(conn, f"supplier-payment:{payment_id}:audit", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "audited":
            return jsonify(save_operation(conn, token, {"success": True, "payment": serialize_payment(conn, row)}))
        required_version(data, row)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("付款单状态不允许审核", 409)
        from utils.supplier_periods import ensure_period_open
        ensure_period_open(conn, row["supplier_id"], row["store_id"], row["business_date"])
        payload = serialize_payment(conn, row)
        payload["allocations"] = [
            {"payableTransactionId": item["payableTransactionId"], "amount": item["amount"]}
            for item in payload["allocations"]
        ]
        _, entries = payment_values(conn, payload)
        invoice_payment_check(conn, entries, payload)
        document = dict(row)
        document["version"] += 1
        post_bank(conn, document)
        apply_allocations(conn, document, "supplier_payment", payment_id, entries)
        if row["advance_cents"]:
            add_ledger(conn, document, "supplier_payment", payment_id, 0, "ADVANCE_PAYMENT",
                       prepayment=row["advance_cents"])
        conn.execute(
            """UPDATE supplier_payments SET status='audited', version=version+1, audited_by=?,
               audited_at=?, reversed_at=NULL, updated_at=? WHERE id=?""",
            (current_identity(), now(), now(), payment_id),
        )
        return jsonify(save_operation(conn, token, {"success": True, "payment": serialize_payment(conn, payment_row(conn, payment_id))}))


@supplier_payments_bp.route("/supplier-payments/<int:payment_id>/reverse-audit", methods=["POST"])
@require_admin_permission("admin.finance.supplier_payment.reverse_audit")
@finance_errors
def reverse_payment(payment_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = payment_row(conn, payment_id)
        replay, token = idempotent_result(conn, f"supplier-payment:{payment_id}:reverse", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "reversed":
            return jsonify(save_operation(conn, token, {"success": True, "payment": serialize_payment(conn, row)}))
        required_version(data, row)
        if row["status"] != "audited" or row["locked_at"]:
            raise FinanceError("只有未锁定已审核付款可以反审核", 409)
        reverse_ledger(conn, "supplier_payment", payment_id)
        post_bank(conn, row, reverse=True)
        conn.execute(
            "UPDATE supplier_payments SET status='reversed', version=version+1, reversed_at=?, updated_at=? WHERE id=?",
            (now(), now(), payment_id),
        )
        return jsonify(save_operation(conn, token, {"success": True, "payment": serialize_payment(conn, payment_row(conn, payment_id))}))


@supplier_payments_bp.route("/supplier-finance/attachments", methods=["POST"])
@require_any_admin_permission("admin.finance.supplier_payment.create", "admin.finance.supplier_payment.edit",
                             "admin.purchase.invoice.create", "admin.purchase.invoice.edit")
@finance_errors
def upload_finance_attachment():
    store_id = positive_id(request.form.get("storeId"))
    check_scope(store_id)
    file = request.files.get("attachment")
    if not file or not file.filename:
        raise FinanceError("请选择附件")
    if request.content_length and request.content_length > 10 * 1024 * 1024 + 256 * 1024:
        raise FinanceError("附件不能超过 10MB", 413)
    extension = os.path.splitext(file.filename)[1].lower()
    mime = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp"}
    if extension not in mime or file.mimetype != mime[extension]:
        raise FinanceError("只支持 PDF、JPG、PNG、WEBP 附件")
    contents = file.read(10 * 1024 * 1024 + 1)
    if len(contents) > 10 * 1024 * 1024:
        raise FinanceError("附件不能超过 10MB", 413)
    valid = (
        contents.startswith(b"%PDF-") if extension == ".pdf" else
        contents.startswith(b"\xff\xd8\xff") if extension in (".jpg", ".jpeg") else
        contents.startswith(b"\x89PNG\r\n\x1a\n") if extension == ".png" else
        contents.startswith(b"RIFF") and contents[8:12] == b"WEBP"
    )
    if not valid:
        raise FinanceError("附件内容与文件类型不符")
    token = uuid.uuid4().hex
    filename = token + extension
    with get_db() as conn:
        if not conn.execute("SELECT 1 FROM stores WHERE id=?", (store_id,)).fetchone():
            raise FinanceError("门店不存在", 404)
        conn.execute(
            """INSERT INTO supplier_finance_attachments
               (token,store_id,filename,original_name,mimetype,created_by,created_at) VALUES (?,?,?,?,?,?,?)""",
            (token, store_id, filename, text(file.filename, 160), mime[extension], current_identity(), now()),
        )
        root = attachment_root()
        os.makedirs(root, exist_ok=True)
        file.stream.seek(0)
        file.save(os.path.join(root, filename))
    return jsonify({"name": text(file.filename, 160), "url": f"/api/supplier-finance/attachments/{token}"}), 201


def attachment_root():
    configured = current_app.config.get("SUPPLIER_FINANCE_UPLOAD_DIR")
    if configured:
        return configured
    root = "/app/uploads" if os.path.isdir("/app/uploads") else os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
    )
    return os.path.join(root, "supplier-finance")


@supplier_payments_bp.route("/supplier-finance/attachments/<token>")
@require_any_admin_permission(READ, "admin.route.purchase.invoices", "admin.route.finance.payables")
@finance_errors
def download_finance_attachment(token):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM supplier_finance_attachments WHERE token=?", (token,)).fetchone()
        if not row:
            raise FinanceError("附件不存在", 404)
        check_scope(row["store_id"])
        response = send_from_directory(attachment_root(), row["filename"], mimetype=row["mimetype"],
                                       as_attachment=True, download_name=row["original_name"])
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


@supplier_payments_bp.route("/suppliers/<int:supplier_id>/<kind>/<int:transaction_id>/allocate", methods=["POST"])
@require_admin_permission("admin.route.finance.payables")
@finance_errors
def allocate_balance(supplier_id, kind, transaction_id):
    from utils.auth import admin_permission_granted
    if kind not in ("prepayments", "credits"):
        raise FinanceError("余额类型无效")
    balance_kind = "prepayment" if kind == "prepayments" else "credit"
    if not admin_permission_granted(f"admin.finance.supplier_{balance_kind}.allocate"):
        raise FinanceError("没有该余额核销权限", 403)
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            f"SELECT * FROM supplier_account_transactions t WHERE id=? AND {effective_sql()}", (transaction_id,),
        ).fetchone()
        if not row or row["supplier_id"] != supplier_id or row[f"{balance_kind}_delta_cents"] <= 0:
            raise FinanceError("可核销余额来源不存在", 404)
        check_scope(row["store_id"])
        replay, token = idempotent_result(conn, f"supplier:{supplier_id}:{kind}:{transaction_id}:allocate", data)
        if replay:
            return jsonify(replay)
        required_version(data, row)
        if row["locked_at"]:
            raise FinanceError("余额已锁定", 409)
        entries = allocation_values(conn, data, supplier_id, row["store_id"])
        total = sum(value for _, value in entries)
        if total <= 0 or total > balance_available(conn, row, balance_kind):
            raise FinanceError("核销合计超过可用余额或为零", 409)
        invoice_payment_check(conn, entries, data)
        date = business_date(data.get("businessDate"))
        if date < row["business_date"] or any(source["business_date"] > date for source, _ in entries):
            raise FinanceError("核销业务日期不能早于余额或应付来源日期")
        from utils.supplier_periods import ensure_period_open
        ensure_period_open(conn, supplier_id, row["store_id"], date)
        if "invoiceOverride" in data and not isinstance(data["invoiceOverride"], bool):
            raise FinanceError("财务豁免必须是布尔值")
        cursor = conn.execute(
            """INSERT INTO supplier_balance_allocations (
                supplier_id, store_id, source_transaction_id, kind, business_date,
                amount_cents, unbilled_reason, invoice_override, remark, created_by, audited_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (supplier_id, row["store_id"], transaction_id, balance_kind, date, total,
             text(data.get("unbilledReason")), int(data.get("invoiceOverride", False)),
             text(data.get("remark")), current_identity(), now()),
        )
        allocation_id = cursor.lastrowid
        document = {"supplier_id": supplier_id, "store_id": row["store_id"], "business_date": date,
                    "document_no": f"HX{allocation_id:06d}", "version": 1, "remark": text(data.get("remark"))}
        apply_allocations(conn, document, "supplier_balance", allocation_id, entries, transaction_id, balance_kind)
        conn.execute("UPDATE supplier_account_transactions SET version=version+1 WHERE id=?", (transaction_id,))
        return jsonify(save_operation(conn, token, {"success": True, "allocation": {
            "id": allocation_id, "documentNo": document["document_no"], "status": "audited", "version": 1,
            "businessDate": date, "auditedAt": now(), "createdBy": current_identity(), "amount": amount(total),
            "sourceTransactionId": transaction_id, "kind": balance_kind,
            "unbilledReason": text(data.get("unbilledReason")), "invoiceOverride": bool(data.get("invoiceOverride")),
        }})), 201


@supplier_payments_bp.route("/supplier-balance-allocations")
@require_admin_permission("admin.route.finance.payables")
@finance_errors
def list_balance_allocations():
    with get_db() as conn:
        scoped, params = scope_sql(alias="a", store_id=request.args.get("storeId", type=int))
        sql = f"SELECT a.* FROM supplier_balance_allocations a WHERE 1=1 {scoped}"
        if request.args.get("supplierId"):
            sql += " AND supplier_id=?"
            params.append(positive_id(request.args["supplierId"]))
        items = [serialize_balance_allocation(conn, row)
                 for row in conn.execute(sql + " ORDER BY id DESC", params)]
        return jsonify({"items": items})


@supplier_payments_bp.route("/supplier-balance-allocations/<int:allocation_id>/reverse", methods=["POST"])
@require_admin_permission("admin.route.finance.payables")
@finance_errors
def reverse_balance_allocation(allocation_id):
    from utils.auth import admin_permission_granted
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM supplier_balance_allocations WHERE id=?", (allocation_id,)).fetchone()
        if not row:
            raise FinanceError("核销记录不存在", 404)
        check_scope(row["store_id"])
        if not admin_permission_granted(f"admin.finance.supplier_{row['kind']}.allocate"):
            raise FinanceError("无权撤销该余额核销", 403)
        replay, token = idempotent_result(conn, f"balance-allocation:{allocation_id}:reverse", data)
        if replay:
            return jsonify(replay)
        if row["status"] != "reversed":
            required_version(data, row)
            if row["locked_at"]:
                raise FinanceError("核销记录已锁定", 409)
            source = conn.execute("SELECT locked_at FROM supplier_account_transactions WHERE id=?",
                                  (row["source_transaction_id"],)).fetchone()
            if source and source["locked_at"]:
                raise FinanceError("余额来源已锁定", 409)
            reverse_ledger(conn, "supplier_balance", allocation_id)
            conn.execute("UPDATE supplier_balance_allocations SET status='reversed', version=version+1, reversed_at=? WHERE id=?",
                         (now(), allocation_id))
            conn.execute("UPDATE supplier_account_transactions SET version=version+1 WHERE id=?", (row["source_transaction_id"],))
        updated = conn.execute("SELECT * FROM supplier_balance_allocations WHERE id=?", (allocation_id,)).fetchone()
        return jsonify(save_operation(conn, token, {"success": True, "allocation": serialize_balance_allocation(conn, updated)}))
