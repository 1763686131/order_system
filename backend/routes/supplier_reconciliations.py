"""Formal supplier statement snapshots and accounting-period locks."""

import json

from flask import Blueprint, jsonify, request

from routes.supplier_finance import finance_errors, serialize_transaction, supplier_row
from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.supplier_ledger import (
    FinanceError, amount, business_date, cents, check_scope, idempotent_result, now, save_operation, scope_sql,
)
from utils.supplier_settlement import positive_id, required_version, supplier_store, text


supplier_reconciliations_bp = Blueprint("supplier_reconciliations", __name__, url_prefix="/api")
READ = "admin.route.finance.supplier_reconciliations"


def reconciliation_row(conn, reconciliation_id):
    row = conn.execute("SELECT * FROM supplier_reconciliations WHERE id=?", (reconciliation_id,)).fetchone()
    if not row:
        raise FinanceError("正式对账单不存在", 404)
    check_scope(row["store_id"])
    return row


def build_snapshot(conn, supplier_id, store_id, start, end):
    rows = conn.execute(
        """SELECT t.* FROM supplier_account_transactions t
           WHERE supplier_id=? AND store_id=? AND business_date<=?
           ORDER BY business_date,id""", (supplier_id, store_id, end)
    ).fetchall()
    running = {"payable": 0, "prepayment": 0, "credit": 0}
    opening = dict(running)
    changes = dict(running)
    period_rows = []
    reversed_ids = {row["reversal_of_id"] for row in rows if row["reversal_of_id"]}
    for row in rows:
        deltas = {key: row[f"{key}_delta_cents"] for key in running}
        if row["business_date"] < start:
            for key, value in deltas.items():
                running[key] += value
            opening = dict(running)
            continue
        for key, value in deltas.items():
            running[key] += value
            changes[key] += value
        item = serialize_transaction(row)
        item["status"] = "reversal" if row["reversal_of_id"] else (
            "reversed" if row["id"] in reversed_ids else "audited"
        )
        item["balances"] = {key: amount(value) for key, value in running.items()}
        period_rows.append(item)
    return {
        "supplierId": supplier_id, "storeId": store_id, "periodStart": start, "periodEnd": end,
        "opening": {key: amount(value) for key, value in opening.items()},
        "changes": {key: amount(value) for key, value in changes.items()},
        "closing": {key: amount(value) for key, value in running.items()},
        "items": period_rows,
    }


def serialize_reconciliation(conn, row):
    supplier = conn.execute("SELECT supplier_name FROM suppliers WHERE id=?", (row["supplier_id"],)).fetchone()
    store = conn.execute("SELECT name FROM stores WHERE id=?", (row["store_id"],)).fetchone()
    return {
        "id": row["id"], "documentNo": row["document_no"], "supplierId": row["supplier_id"],
        "supplierName": supplier["supplier_name"], "storeId": row["store_id"], "storeName": store["name"],
        "periodStart": row["period_start"], "periodEnd": row["period_end"],
        "snapshot": json.loads(row["snapshot_json"]),
        "supplierBalances": json.loads(row["supplier_balances_json"]) if row["supplier_balances_json"] else None,
        "differenceReason": row["difference_reason"], "confirmationNote": row["confirmation_note"],
        "status": row["status"], "version": row["version"], "createdBy": row["created_by"],
        "createdAt": row["created_at"], "confirmedBy": row["confirmed_by"],
        "confirmedAt": row["confirmed_at"], "lockedAt": row["locked_at"],
    }


def ensure_no_overlap(conn, supplier_id, store_id, start, end, exclude_id=None):
    sql = """SELECT document_no FROM supplier_reconciliations
             WHERE supplier_id=? AND store_id=? AND status IN ('draft','confirmed')
               AND period_start<=? AND period_end>=?"""
    params = [supplier_id, store_id, end, start]
    if exclude_id:
        sql += " AND id<>?"
        params.append(exclude_id)
    if conn.execute(sql + " LIMIT 1", params).fetchone():
        raise FinanceError("该供应商门店已有重叠的正式对账期间", 409)


def reconcile_values(conn, data):
    supplier_id, store_id = supplier_store(conn, data.get("supplierId"), data.get("storeId"))
    start = business_date(data.get("periodStart"))
    end = business_date(data.get("periodEnd"))
    if start > end:
        raise FinanceError("对账开始日期不能晚于结束日期")
    ensure_no_overlap(conn, supplier_id, store_id, start, end)
    return supplier_id, store_id, start, end


def next_number(conn, date):
    prefix = "DZ" + date.replace("-", "")
    suffixes = [row["document_no"][len(prefix):] for row in conn.execute(
        "SELECT document_no FROM supplier_reconciliations WHERE document_no LIKE ?", (prefix + "%",)
    )]
    numeric = [int(value) for value in suffixes if value.isdigit()]
    return prefix + f"{max(numeric or [0]) + 1:03d}"


@supplier_reconciliations_bp.route("/supplier-reconciliations/options")
@require_admin_permission(READ)
@finance_errors
def reconciliation_options():
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
        return jsonify({"stores": stores, "suppliers": suppliers})


@supplier_reconciliations_bp.route("/supplier-reconciliations")
@require_admin_permission(READ)
@finance_errors
def list_reconciliations():
    with get_db() as conn:
        scoped, params = scope_sql(alias="r", store_id=request.args.get("storeId", type=int))
        sql = f"SELECT r.* FROM supplier_reconciliations r WHERE 1=1 {scoped}"
        for column, key in (("supplier_id", "supplierId"), ("status", "status")):
            if request.args.get(key):
                sql += f" AND r.{column}=?"
                params.append(positive_id(request.args[key]) if key == "supplierId" else request.args[key])
        if request.args.get("periodStart"):
            sql += " AND r.period_start>=?"
            params.append(business_date(request.args["periodStart"]))
        if request.args.get("periodEnd"):
            sql += " AND r.period_end<=?"
            params.append(business_date(request.args["periodEnd"]))
        rows = conn.execute(sql + " ORDER BY r.period_end DESC,r.id DESC", params).fetchall()
        items = [serialize_reconciliation(conn, row) for row in rows]
        keyword = text(request.args.get("keyword")).lower()
        items = [row for row in items if not keyword or keyword in
                 (row["documentNo"] + row["supplierName"] + row["confirmationNote"]).lower()]
        return jsonify({"items": items, "total": len(items)})


@supplier_reconciliations_bp.route("/supplier-reconciliations/<int:reconciliation_id>")
@require_admin_permission(READ)
@finance_errors
def get_reconciliation(reconciliation_id):
    with get_db() as conn:
        return jsonify(serialize_reconciliation(conn, reconciliation_row(conn, reconciliation_id)))


@supplier_reconciliations_bp.route("/supplier-reconciliations", methods=["POST"])
@require_admin_permission("admin.finance.supplier_reconciliation.create")
@finance_errors
def create_reconciliation():
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        supplier_store(conn, data.get("supplierId"), data.get("storeId"))
        replay, token = idempotent_result(conn, "supplier-reconciliation:create", data)
        if replay:
            return jsonify(replay)
        supplier_id, store_id, start, end = reconcile_values(conn, data)
        snapshot = build_snapshot(conn, supplier_id, store_id, start, end)
        cursor = conn.execute(
            """INSERT INTO supplier_reconciliations (
                document_no,supplier_id,store_id,period_start,period_end,snapshot_json,created_by,created_at
            ) VALUES (?,?,?,?,?,?,?,?)""",
            (next_number(conn, end), supplier_id, store_id, start, end,
             json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), current_identity(), now()),
        )
        return jsonify(save_operation(conn, token, {
            "success": True, "reconciliation": serialize_reconciliation(
                conn, reconciliation_row(conn, cursor.lastrowid)
            )
        })), 201


@supplier_reconciliations_bp.route("/supplier-reconciliations/<int:reconciliation_id>/refresh", methods=["POST"])
@require_admin_permission("admin.finance.supplier_reconciliation.create")
@finance_errors
def refresh_reconciliation(reconciliation_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = reconciliation_row(conn, reconciliation_id)
        if row["status"] != "draft" or row["locked_at"]:
            raise FinanceError("只有未确认的对账草稿可以刷新快照", 409)
        required_version(data, row)
        ensure_no_overlap(conn, row["supplier_id"], row["store_id"], row["period_start"],
                          row["period_end"], row["id"])
        snapshot = build_snapshot(conn, row["supplier_id"], row["store_id"],
                                  row["period_start"], row["period_end"])
        conn.execute("UPDATE supplier_reconciliations SET snapshot_json=?,version=version+1 WHERE id=?",
                     (json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), reconciliation_id))
        return jsonify({"success": True, "reconciliation": serialize_reconciliation(
            conn, reconciliation_row(conn, reconciliation_id)
        )})


@supplier_reconciliations_bp.route("/supplier-reconciliations/<int:reconciliation_id>/confirm", methods=["POST"])
@require_admin_permission("admin.finance.supplier_reconciliation.confirm")
@finance_errors
def confirm_reconciliation(reconciliation_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = reconciliation_row(conn, reconciliation_id)
        replay, token = idempotent_result(conn, f"supplier-reconciliation:{reconciliation_id}:confirm", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "confirmed":
            return jsonify(save_operation(conn, token, {
                "success": True, "reconciliation": serialize_reconciliation(conn, row)
            }))
        required_version(data, row)
        if row["status"] != "draft" or row["locked_at"]:
            raise FinanceError("该对账单状态不允许确认", 409)
        ensure_no_overlap(conn, row["supplier_id"], row["store_id"], row["period_start"],
                          row["period_end"], row["id"])
        snapshot = build_snapshot(conn, row["supplier_id"], row["store_id"],
                                  row["period_start"], row["period_end"])
        if snapshot != json.loads(row["snapshot_json"]):
            raise FinanceError("生成快照后账务发生变化，请刷新快照后再确认", 409)
        balances = data.get("supplierBalances")
        if not isinstance(balances, dict):
            raise FinanceError("请填写供应商确认的应付、预付款和贷项余额")
        values = {key: cents(balances.get(source)) for key, source in (
            ("payable", "payableBalance"), ("prepayment", "prepaymentBalance"), ("credit", "creditBalance")
        )}
        difference = any(values[key] != cents(snapshot["closing"][key]) for key in values)
        reason = text(data.get("differenceReason"))
        if difference and not reason:
            raise FinanceError("供应商确认余额与系统快照不一致时必须填写差异原因")
        contact = text(data.get("supplierContact"), 120)
        note = text(data.get("confirmationNote"))
        if not contact or not note:
            raise FinanceError("请记录供应商确认人和确认方式或备注")
        confirmation = json.dumps({"supplierContact": contact, "note": note}, ensure_ascii=False)
        conn.execute(
            """UPDATE supplier_reconciliations SET status='confirmed',supplier_balances_json=?,
               difference_reason=?,confirmation_note=?,confirmed_by=?,confirmed_at=?,version=version+1
               WHERE id=?""",
            (json.dumps({key: amount(value) for key, value in values.items()}, ensure_ascii=False),
             reason, confirmation, current_identity(), now(), reconciliation_id),
        )
        from utils.supplier_periods import lock_period
        lock_period(conn, row["supplier_id"], row["store_id"], row["period_end"], reconciliation_id)
        return jsonify(save_operation(conn, token, {
            "success": True, "reconciliation": serialize_reconciliation(
                conn, reconciliation_row(conn, reconciliation_id)
            )
        }))


@supplier_reconciliations_bp.route("/supplier-reconciliations/<int:reconciliation_id>/cancel", methods=["POST"])
@require_admin_permission("admin.finance.supplier_reconciliation.cancel")
@finance_errors
def cancel_reconciliation(reconciliation_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = reconciliation_row(conn, reconciliation_id)
        replay, token = idempotent_result(conn, f"supplier-reconciliation:{reconciliation_id}:cancel", data)
        if replay:
            return jsonify(replay)
        required_version(data, row)
        if row["status"] != "draft" or row["locked_at"]:
            raise FinanceError("只有未确认、未锁期的对账草稿可以取消", 409)
        conn.execute("UPDATE supplier_reconciliations SET status='cancelled',version=version+1 WHERE id=?",
                     (reconciliation_id,))
        return jsonify(save_operation(conn, token, {
            "success": True, "reconciliation": serialize_reconciliation(
                conn, reconciliation_row(conn, reconciliation_id)
            )
        }))
