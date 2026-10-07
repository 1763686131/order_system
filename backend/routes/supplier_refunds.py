"""Supplier credit refunds and bank-account receipts."""

import json

from flask import Blueprint, jsonify, request

from routes.supplier_finance import finance_errors
from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.supplier_ledger import (
    FinanceError, amount, business_date, cents, check_scope, effective_sql,
    idempotent_result, now, save_operation, scope_sql,
)
from utils.supplier_settlement import (
    add_ledger, balance_available, positive_id, required_version, supplier_store, text,
)


supplier_refunds_bp = Blueprint("supplier_refunds", __name__, url_prefix="/api")
READ = "admin.route.finance.supplier_refunds"


def refund_row(conn, refund_id):
    row = conn.execute("SELECT * FROM supplier_refunds WHERE id=?", (refund_id,)).fetchone()
    if not row:
        raise FinanceError("供应商退款单不存在", 404)
    check_scope(row["store_id"])
    return row


def refund_values(conn, data):
    supplier_id, store_id = supplier_store(conn, data.get("supplierId"), data.get("storeId"))
    account_id = positive_id(data.get("bankAccountId"))
    account = conn.execute(
        "SELECT * FROM bank_accounts WHERE id=? AND store_id=?", (account_id, store_id)
    ).fetchone()
    if not account:
        raise FinanceError("请选择该门店的银行账户")
    date = business_date(data.get("businessDate"))
    refund_date = business_date(data.get("refundDate") or date)
    refund_cents = cents(data.get("refundAmount"))
    if refund_cents <= 0:
        raise FinanceError("退款金额必须大于零")
    entries = data.get("allocations")
    if not isinstance(entries, list) or not entries or len(entries) > 100:
        raise FinanceError("退款贷项分配必须包含 1 至 100 项")
    allocations, seen = [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise FinanceError("退款贷项分配格式错误")
        transaction_id = positive_id(entry.get("creditTransactionId"))
        if transaction_id in seen:
            raise FinanceError("同一贷项不能重复分配")
        seen.add(transaction_id)
        credit = conn.execute(
            f"SELECT * FROM supplier_account_transactions t WHERE t.id=? AND {effective_sql()}",
            (transaction_id,),
        ).fetchone()
        if (
            not credit or credit["supplier_id"] != supplier_id or credit["store_id"] != store_id
            or credit["source_type"] != "purchase_return"
            or credit["transaction_type"] != "PURCHASE_RETURN"
            or credit["credit_delta_cents"] <= 0
        ):
            raise FinanceError("退款只能关联该供应商本门店的有效采购退货贷项", 409)
        check_scope(store_id)
        if credit["locked_at"]:
            raise FinanceError("贷项已被正式对账锁定，不能退款", 409)
        value = cents(entry.get("amount"))
        if value <= 0 or value > balance_available(conn, credit, "credit"):
            raise FinanceError("退款金额超过该贷项可用余额", 409)
        if date < credit["business_date"] or refund_date < credit["business_date"]:
            raise FinanceError("退款日期不能早于贷项日期")
        allocations.append((credit, value))
    if sum(value for _, value in allocations) != refund_cents:
        raise FinanceError("退款金额必须等于关联贷项分配合计")
    from utils.supplier_periods import ensure_period_open
    ensure_period_open(conn, supplier_id, store_id, date)
    ensure_period_open(conn, supplier_id, store_id, refund_date)
    return {
        "supplier_id": supplier_id, "store_id": store_id, "business_date": date,
        "refund_date": refund_date, "bank_account_id": account_id,
        "account_name": account["account_name"], "refund_cents": refund_cents,
        "remark": text(data.get("remark")), "allocations": allocations,
    }


def serialize_refund(conn, row):
    supplier = conn.execute("SELECT supplier_name FROM suppliers WHERE id=?", (row["supplier_id"],)).fetchone()
    store = conn.execute("SELECT name FROM stores WHERE id=?", (row["store_id"],)).fetchone()
    allocations = []
    for item in conn.execute(
        """SELECT credit_transaction_id,amount_cents,active FROM supplier_refund_allocations
           WHERE refund_id=? AND active=1 ORDER BY id""", (row["id"],)
    ):
        source = conn.execute(
            "SELECT source_document_no,business_date,credit_delta_cents FROM supplier_account_transactions WHERE id=?",
            (item["credit_transaction_id"],),
        ).fetchone()
        allocations.append({
            "creditTransactionId": item["credit_transaction_id"],
            "documentNo": source["source_document_no"], "businessDate": source["business_date"],
            "creditAmount": amount(source["credit_delta_cents"]),
            "amount": amount(item["amount_cents"]), "active": bool(item["active"]),
        })
    if not allocations:
        allocations = json.loads(row["credits_json"])
    banks = [
        {"id": item["id"], "businessDate": item["business_date"], "change": amount(item["delta_cents"]),
         "balanceAfter": amount(item["balance_after_cents"]), "reversalOfId": item["reversal_of_id"]}
        for item in conn.execute(
            "SELECT * FROM bank_account_transactions WHERE source_type='supplier_refund' AND source_id=? ORDER BY id",
            (row["id"],),
        )
    ]
    return {
        "id": row["id"], "documentNo": row["document_no"], "supplierId": row["supplier_id"],
        "supplierName": supplier["supplier_name"], "storeId": row["store_id"], "storeName": store["name"],
        "businessDate": row["business_date"], "refundDate": row["refund_date"],
        "bankAccountId": row["bank_account_id"], "accountName": row["account_name"],
        "refundAmount": amount(row["refund_cents"]), "remark": row["remark"], "status": row["status"],
        "version": row["version"], "createdBy": row["created_by"], "createdAt": row["created_at"],
        "auditedBy": row["audited_by"], "auditedAt": row["audited_at"],
        "reversedAt": row["reversed_at"], "lockedAt": row["locked_at"],
        "allocations": allocations, "bankTransactions": banks,
    }


def next_number(conn, date):
    prefix = "TK" + date.replace("-", "")
    values = [row["document_no"][len(prefix):] for row in conn.execute(
        "SELECT document_no FROM supplier_refunds WHERE document_no LIKE ?", (prefix + "%",)
    )]
    suffixes = [int(value) for value in values if value.isdigit()]
    return prefix + f"{max(suffixes or [0]) + 1:03d}"


def post_refund_bank(conn, document, reverse=False):
    account = conn.execute("SELECT * FROM bank_accounts WHERE id=?", (document["bank_account_id"],)).fetchone()
    if not account or account["store_id"] != document["store_id"]:
        raise FinanceError("退款银行账户不存在或门店不一致", 409)
    delta = -document["refund_cents"] if reverse else document["refund_cents"]
    current = cents(account["balance"], nonnegative=False)
    if current + delta < 0:
        raise FinanceError("银行账户余额不足，不能反审核退款", 409)
    original = None
    if reverse:
        original = conn.execute(
            """SELECT t.* FROM bank_account_transactions t
               WHERE source_type='supplier_refund' AND source_id=? AND reversal_of_id IS NULL
                 AND NOT EXISTS (SELECT 1 FROM bank_account_transactions r WHERE r.reversal_of_id=t.id)
               ORDER BY id DESC LIMIT 1""", (document["id"],)
        ).fetchone()
        if not original:
            raise FinanceError("找不到有效的供应商退款银行流水", 409)
    else:
        active = conn.execute(
            """SELECT 1 FROM bank_account_transactions t
               WHERE source_type='supplier_refund' AND source_id=? AND reversal_of_id IS NULL
                 AND NOT EXISTS (SELECT 1 FROM bank_account_transactions r WHERE r.reversal_of_id=t.id)""",
            (document["id"],),
        ).fetchone()
        if active:
            raise FinanceError("该退款单已有有效银行流水", 409)
    conn.execute(
        """INSERT INTO bank_account_transactions (
            bank_account_id,store_id,business_date,source_type,source_id,document_no,
            document_version,delta_cents,balance_after_cents,created_by,created_at,reversal_of_id
        ) VALUES (?,?,?,'supplier_refund',?,?,?,?,?,?,?,?)""",
        (account["id"], document["store_id"],
         max(now()[:10], original["business_date"]) if original else document["refund_date"],
         document["id"], document["document_no"],
         original["document_version"] if original else document["version"],
         delta, current + delta, current_identity(), now(), original["id"] if original else None),
    )
    conn.execute("UPDATE bank_accounts SET balance=?,updated_at=? WHERE id=?",
                 (amount(current + delta), now(), account["id"]))


@supplier_refunds_bp.route("/supplier-refunds/options")
@require_admin_permission(READ)
@finance_errors
def refund_options():
    with get_db() as conn:
        scoped, params = scope_sql(alias="s")
        stores = [dict(row) for row in conn.execute(
            f"SELECT s.id,s.name FROM stores s WHERE s.status='active' {scoped} ORDER BY s.name", params
        )]
        store_ids = {row["id"] for row in stores}
        suppliers = [
            {"id": row["id"], "supplierName": row["supplier_name"], "storeId": row["store_id"]}
            for row in conn.execute("SELECT id,supplier_name,store_id FROM suppliers WHERE status='active'")
            if row["store_id"] is None or row["store_id"] in store_ids
        ]
        scoped, params = scope_sql(alias="b")
        banks = [dict(row) for row in conn.execute(
            f"SELECT b.id,b.store_id,b.account_name,b.bank_name,b.balance FROM bank_accounts b WHERE 1=1 {scoped}",
            params,
        )]
        return jsonify({"stores": stores, "suppliers": suppliers, "bankAccounts": banks})


@supplier_refunds_bp.route("/suppliers/<int:supplier_id>/supplier-refund-credits")
@require_admin_permission(READ)
@finance_errors
def refund_credits(supplier_id):
    store_id = positive_id(request.args.get("storeId"))
    with get_db() as conn:
        supplier_store(conn, supplier_id, store_id)
        rows = conn.execute(
            f"""SELECT t.* FROM supplier_account_transactions t
                WHERE t.supplier_id=? AND t.store_id=? AND t.source_type='purchase_return'
                  AND t.transaction_type='PURCHASE_RETURN' AND t.credit_delta_cents>0
                  AND {effective_sql()} ORDER BY t.business_date,t.id""",
            (supplier_id, store_id),
        ).fetchall()
        items = []
        for row in rows:
            available = balance_available(conn, row, "credit")
            if available > 0 and not row["locked_at"]:
                items.append({
                    "creditTransactionId": row["id"], "documentNo": row["source_document_no"],
                    "businessDate": row["business_date"], "creditAmount": amount(row["credit_delta_cents"]),
                    "availableAmount": amount(available), "productName": row["product_name"],
                })
        return jsonify({"items": items})


@supplier_refunds_bp.route("/supplier-refunds/next-number")
@require_admin_permission(READ)
@finance_errors
def refund_next_number():
    with get_db() as conn:
        return jsonify({"documentNo": next_number(conn, business_date(request.args.get("date") or now()[:10]))})


@supplier_refunds_bp.route("/supplier-refunds")
@require_admin_permission(READ)
@finance_errors
def list_refunds():
    with get_db() as conn:
        scoped, params = scope_sql(alias="r", store_id=request.args.get("storeId", type=int))
        sql = f"SELECT r.* FROM supplier_refunds r WHERE 1=1 {scoped}"
        for column, key in (("supplier_id", "supplierId"), ("status", "status")):
            if request.args.get(key):
                sql += f" AND r.{column}=?"
                params.append(positive_id(request.args[key]) if key == "supplierId" else request.args[key])
        for column, key, operator in (("business_date", "startDate", ">="), ("business_date", "endDate", "<=")):
            if request.args.get(key):
                sql += f" AND r.{column}{operator}?"
                params.append(business_date(request.args[key]))
        items = [serialize_refund(conn, row) for row in conn.execute(
            sql + " ORDER BY r.business_date DESC,r.id DESC", params
        )]
        keyword = text(request.args.get("keyword")).lower()
        items = [row for row in items if not keyword or keyword in
                 (row["documentNo"] + row["supplierName"] + row["remark"]).lower()]
        return jsonify({"items": items, "total": len(items)})


@supplier_refunds_bp.route("/supplier-refunds/<int:refund_id>")
@require_admin_permission(READ)
@finance_errors
def get_refund(refund_id):
    with get_db() as conn:
        return jsonify(serialize_refund(conn, refund_row(conn, refund_id)))


@supplier_refunds_bp.route("/supplier-refunds", methods=["POST"])
@require_admin_permission("admin.finance.supplier_refund.create")
@finance_errors
def create_refund():
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        supplier_store(conn, data.get("supplierId"), data.get("storeId"))
        replay, token = idempotent_result(conn, "supplier-refund:create", data)
        if replay:
            return jsonify(replay)
        values = refund_values(conn, data)
        cursor = conn.execute(
            """INSERT INTO supplier_refunds (
                document_no,supplier_id,store_id,business_date,refund_date,bank_account_id,
                account_name,refund_cents,credits_json,remark,created_by,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (next_number(conn, values["business_date"]), values["supplier_id"], values["store_id"],
             values["business_date"], values["refund_date"], values["bank_account_id"],
             values["account_name"], values["refund_cents"],
             json.dumps([{"creditTransactionId": row["id"], "amount": amount(value)}
                         for row, value in values["allocations"]]),
             values["remark"], current_identity(), now(), now()),
        )
        return jsonify(save_operation(conn, token, {
            "success": True, "refund": serialize_refund(conn, refund_row(conn, cursor.lastrowid))
        })), 201


@supplier_refunds_bp.route("/supplier-refunds/<int:refund_id>", methods=["PUT"])
@require_admin_permission("admin.finance.supplier_refund.edit")
@finance_errors
def edit_refund(refund_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = refund_row(conn, refund_id)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("只有未审核退款草稿可以修改", 409)
        required_version(data, row)
        values = refund_values(conn, data)
        if values["supplier_id"] != row["supplier_id"] or values["store_id"] != row["store_id"]:
            raise FinanceError("退款供应商和门店不能修改", 409)
        conn.execute(
            """UPDATE supplier_refunds SET business_date=?,refund_date=?,bank_account_id=?,account_name=?,
               refund_cents=?,credits_json=?,remark=?,status='draft',version=version+1,updated_at=? WHERE id=?""",
            (values["business_date"], values["refund_date"], values["bank_account_id"], values["account_name"],
             values["refund_cents"], json.dumps([{"creditTransactionId": source["id"], "amount": amount(value)}
                                                 for source, value in values["allocations"]]),
             values["remark"], now(), refund_id),
        )
        return jsonify({"success": True, "refund": serialize_refund(conn, refund_row(conn, refund_id))})


@supplier_refunds_bp.route("/supplier-refunds/<int:refund_id>", methods=["DELETE"])
@require_admin_permission("admin.finance.supplier_refund.delete")
@finance_errors
def delete_refund(refund_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = refund_row(conn, refund_id)
        required_version(data, row)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("只有未审核退款草稿可以删除", 409)
        if row["audited_at"]:
            conn.execute("UPDATE supplier_refunds SET status='cancelled',version=version+1,updated_at=? WHERE id=?",
                         (now(), refund_id))
        else:
            conn.execute("DELETE FROM supplier_refunds WHERE id=?", (refund_id,))
        return jsonify({"success": True, "deleted": True})


@supplier_refunds_bp.route("/supplier-refunds/<int:refund_id>/audit", methods=["POST"])
@require_admin_permission("admin.finance.supplier_refund.audit")
@finance_errors
def audit_refund(refund_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = refund_row(conn, refund_id)
        replay, token = idempotent_result(conn, f"supplier-refund:{refund_id}:audit", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "audited":
            return jsonify(save_operation(conn, token, {"success": True, "refund": serialize_refund(conn, row)}))
        required_version(data, row)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("退款单状态不允许审核", 409)
        values = refund_values(conn, {
            "supplierId": row["supplier_id"], "storeId": row["store_id"],
            "businessDate": row["business_date"], "refundDate": row["refund_date"],
            "bankAccountId": row["bank_account_id"], "refundAmount": amount(row["refund_cents"]),
            "allocations": json.loads(row["credits_json"]), "remark": row["remark"],
        })
        document = dict(row)
        document["version"] += 1
        post_refund_bank(conn, document)
        for credit, value in values["allocations"]:
            add_ledger(
                conn, document, "supplier_refund", refund_id, credit["id"],
                "SUPPLIER_REFUND", credit=-value, target=dict(credit),
            )
            conn.execute(
                """INSERT INTO supplier_refund_allocations(refund_id,credit_transaction_id,amount_cents,active)
                   VALUES(?,?,?,1)
                   ON CONFLICT(refund_id,credit_transaction_id) DO UPDATE SET
                     amount_cents=excluded.amount_cents,active=1""",
                (refund_id, credit["id"], value),
            )
        conn.execute(
            """UPDATE supplier_refunds SET status='audited',version=version+1,audited_by=?,audited_at=?,
               reversed_at=NULL,updated_at=? WHERE id=?""", (current_identity(), now(), now(), refund_id)
        )
        return jsonify(save_operation(conn, token, {
            "success": True, "refund": serialize_refund(conn, refund_row(conn, refund_id))
        }))


@supplier_refunds_bp.route("/supplier-refunds/<int:refund_id>/reverse-audit", methods=["POST"])
@require_admin_permission("admin.finance.supplier_refund.reverse_audit")
@finance_errors
def reverse_refund(refund_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = refund_row(conn, refund_id)
        replay, token = idempotent_result(conn, f"supplier-refund:{refund_id}:reverse", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "reversed":
            return jsonify(save_operation(conn, token, {"success": True, "refund": serialize_refund(conn, row)}))
        required_version(data, row)
        if row["status"] != "audited" or row["locked_at"]:
            raise FinanceError("只有未锁定的已审核退款可以反审核", 409)
        from utils.supplier_settlement import reverse_ledger
        reverse_ledger(conn, "supplier_refund", refund_id)
        post_refund_bank(conn, row, reverse=True)
        conn.execute(
            "UPDATE supplier_refunds SET status='reversed',version=version+1,reversed_at=?,updated_at=? WHERE id=?",
            (now(), now(), refund_id),
        )
        return jsonify(save_operation(conn, token, {
            "success": True, "refund": serialize_refund(conn, refund_row(conn, refund_id))
        }))
