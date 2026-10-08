"""Stage-one supplier payables, internal statements and inbound attribution."""

from functools import wraps

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.supplier_ledger import (
    FinanceError, amount, balance, business_date, cents, check_scope, check_version,
    effective_sql, idempotent_result, now, post_inbound_payables, returned_payable_cents,
    save_operation, scope_sql,
)


supplier_finance_bp = Blueprint("supplier_finance", __name__, url_prefix="/api")


def finance_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            if request.is_json and request.content_length and not isinstance(request.get_json(silent=True), dict):
                raise FinanceError("请求体必须是 JSON 对象")
            return view(*args, **kwargs)
        except FinanceError as exc:
            return jsonify({"success": False, "message": str(exc)}), exc.status
        except (ValueError, TypeError) as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
    return wrapped


def positive_id(value):
    if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
        raise FinanceError("ID 必须为正整数")
    return int(value)


def supplier_row(conn, supplier_id):
    row = conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    if not row:
        raise FinanceError("供应商不存在", 404)
    if row["store_id"] is not None:
        check_scope(row["store_id"])
    return row


def inbound_row(conn, inbound_id, require_pending=True):
    row = conn.execute("SELECT * FROM stock_inbounds WHERE id = ?", (inbound_id,)).fetchone()
    if not row:
        raise FinanceError("入库单不存在", 404)
    items = [dict(item) for item in conn.execute(
        "SELECT * FROM stock_inbound_items WHERE inbound_id = ? ORDER BY line_no, id", (inbound_id,)
    ).fetchall()]
    check_scope(row["store_id"], [item["warehouse_id"] or row["warehouse_id"] for item in items])
    if row["purchase_order_id"] or row["document_source"] != "other":
        raise FinanceError("仅独立采购入库可进行采购审核", 409)
    if require_pending and row["settlement_type"] != "pending_supplier":
        raise FinanceError("仅待补采购信息的入库可确认应付", 409)
    return row, items


def serialize_inbound(conn, row):
    from routes.stock_inbounds import _serialize_document
    return _serialize_document(conn, row)


@supplier_finance_bp.route("/stock-inbounds/<int:inbound_id>/settlement")
@require_admin_permission("admin.purchase.inbound.settlement.read")
@finance_errors
def get_settlement(inbound_id):
    with get_db() as conn:
        row, _ = inbound_row(conn, inbound_id, require_pending=False)
        return jsonify(serialize_inbound(conn, row))


def update_inbound_purchasing(conn, row, items, data):
    """Update procurement fields inside the caller's transaction."""
    from routes.stock_inbounds import _normalize_items
    from utils.supplier_periods import ensure_period_open

    inbound_id = row["id"]
    if row["status"] not in ("reviewed", "posted"):
        raise FinanceError("请先完成仓库入库，再补录采购信息", 409)
    settlement_type = data.get("settlementType", row["settlement_type"])
    if settlement_type not in ("none", "pending_supplier"):
        raise FinanceError("结算归属只能为无需结算或供应商结算")
    requested = data.get("items")
    if not isinstance(requested, list) or not requested:
        raise FinanceError("请提供需要补录的入库明细")
    by_id = {item["id"]: item for item in items}
    assignments, seen = [], set()
    for item in requested:
        if not isinstance(item, dict):
            raise FinanceError("明细格式不正确")
        item_id = positive_id(item.get("inboundItemId"))
        supplier_id = positive_id(item.get("supplierId")) if settlement_type == "pending_supplier" else None
        if item_id not in by_id:
            raise FinanceError("入库明细不属于当前单据", 404)
        if item_id in seen:
            raise FinanceError("同一入库明细不能重复归属")
        seen.add(item_id)
        source = by_id[item_id]
        if supplier_id:
            supplier = supplier_row(conn, supplier_id)
            if supplier["status"] != "active" or supplier["store_id"] not in (None, row["store_id"]):
                raise FinanceError("供应商已停用或不属于入库门店")
            ensure_period_open(conn, supplier_id, row["store_id"], row["document_date"])
        pricing = _normalize_items(
            conn, row["receipt_type"], [{
                **source,
                "unitPrice": item.get("unitPrice", source["unit_price"]),
                "taxRate": item.get("taxRate", source["tax_rate"]),
            }], default_warehouse_id=row["warehouse_id"],
        )[0]
        if settlement_type == "pending_supplier" and pricing["unit_price"] is None:
            raise FinanceError("请补齐每条入库明细的采购单价")
        changes = (
            source["supplier_id"] != supplier_id
            or source["unit_price"] != pricing["unit_price"]
            or source["tax_rate"] != pricing["tax_rate"]
            or row["settlement_type"] != settlement_type
        )
        if source["payable_transaction_id"] and changes:
            raise FinanceError("已确认应付的采购信息不能修改，请先反审核入库", 409)
        assignments.append((item_id, supplier_id, pricing, changes))
    if settlement_type != row["settlement_type"] and seen != set(by_id):
        raise FinanceError("变更结算归属必须提交全部入库明细")
    remark = str(data.get("settlementRemark", row["settlement_remark"]))[:500]
    unchanged = not any(entry[3] for entry in assignments) and remark == row["settlement_remark"]
    if not unchanged:
        check_version(data, row)
        if any(item["payable_transaction_id"] for item in items):
            raise FinanceError("已确认应付的采购信息不能修改，请先反审核入库", 409)
        for item_id, supplier_id, pricing, _ in assignments:
            conn.execute(
                """UPDATE stock_inbound_items SET supplier_id = ?, supplier_assignment_status = ?,
                   supplier_assigned_by = ?, supplier_assigned_at = ?, unit_price = ?, tax_rate = ?,
                   tax_amount = ?, total_amount = ? WHERE id = ?""",
                (supplier_id, "confirmed" if supplier_id else "not_required",
                 current_identity(), now(), pricing["unit_price"], pricing["tax_rate"],
                 pricing["tax_amount"], pricing["total_amount"], item_id),
            )
            expense_cost = conn.execute(
                """SELECT COALESCE(SUM(amount_excluding_tax_cents), 0) AS amount
                   FROM purchase_expense_lines WHERE inbound_item_id = ?
                   AND status = 'confirmed' AND include_in_inventory_cost = 1""", (item_id,),
            ).fetchone()["amount"] / 100
            # Revalue the original movement only; received stock is already posted.
            conn.execute(
                """UPDATE stock_movements SET unit_price = ?, tax_rate = ?, total_amount = ?
                   WHERE movement_type = 'in' AND source_document_id = ? AND source_item_id = ?""",
                (float(pricing["unit_price"] or 0) + expense_cost / pricing["received_qty"],
                 pricing["tax_rate"], pricing["total_amount"] + expense_cost, inbound_id, item_id),
            )
        totals = conn.execute(
            """SELECT COALESCE(SUM(tax_amount), 0) tax, COALESCE(SUM(total_amount), 0) amount
               FROM stock_inbound_items WHERE inbound_id = ?""", (inbound_id,),
        ).fetchone()
        conn.execute(
            """UPDATE stock_inbounds SET version = version + 1, settlement_type = ?,
               settlement_remark = ?, total_tax = ?, total_amount = ?, updated_at = ? WHERE id = ?""",
            (settlement_type, remark, amount(cents(totals["tax"])),
             amount(cents(totals["amount"])), now(), inbound_id),
        )
    return conn.execute("SELECT * FROM stock_inbounds WHERE id = ?", (inbound_id,)).fetchone()


@supplier_finance_bp.route("/stock-inbounds/<int:inbound_id>/assign-supplier", methods=["POST"])
@require_admin_permission("admin.purchase.inbound.assign_supplier")
@finance_errors
def assign_supplier(inbound_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row, items = inbound_row(conn, inbound_id, require_pending=False)
        replay, token = idempotent_result(conn, f"inbound:{inbound_id}:assign-supplier", data)
        if replay:
            return jsonify(replay)
        updated = update_inbound_purchasing(conn, row, items, data)
        return jsonify(save_operation(conn, token, {"success": True, "stockIn": serialize_inbound(conn, updated)}))


@supplier_finance_bp.route("/stock-inbounds/<int:inbound_id>/confirm-payable", methods=["POST"])
@require_admin_permission("admin.purchase.inbound.confirm_payable")
@finance_errors
def confirm_payable(inbound_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row, items = inbound_row(conn, inbound_id)
        replay, token = idempotent_result(conn, f"inbound:{inbound_id}:confirm-payable", data)
        if replay:
            return jsonify(replay)
        if row["status"] not in ("reviewed", "posted"):
            raise FinanceError("只有已审核入库可以确认应付", 409)
        if items and all(item["payable_transaction_id"] for item in items):
            return jsonify(save_operation(conn, token, {"success": True, "stockIn": serialize_inbound(conn, row)}))
        check_version(data, row)
        if not items or any(not item["supplier_id"] for item in items):
            raise FinanceError("请先补齐每条入库明细的供应商", 409)
        conn.execute("UPDATE stock_inbounds SET version = version + 1, updated_at = ? WHERE id = ?", (now(), inbound_id))
        updated = conn.execute("SELECT * FROM stock_inbounds WHERE id = ?", (inbound_id,)).fetchone()
        post_inbound_payables(conn, updated, items)
        return jsonify(save_operation(conn, token, {"success": True, "stockIn": serialize_inbound(conn, updated)}))


@supplier_finance_bp.route("/suppliers/<int:supplier_id>/balance")
@require_admin_permission("admin.route.finance.payables")
@finance_errors
def supplier_balance(supplier_id):
    with get_db() as conn:
        supplier_row(conn, supplier_id)
        return jsonify(balance(conn, supplier_id, request.args.get("storeId", type=int), request.args.get("asOf")))


@supplier_finance_bp.route("/suppliers/payables")
@require_admin_permission("admin.route.finance.payables")
@finance_errors
def list_payables():
    store_id = request.args.get("storeId", type=int)
    as_of = business_date(request.args["asOf"]) if request.args.get("asOf") else None
    keyword = request.args.get("keyword", "").strip().lower()
    aging = request.args.get("aging", "")
    if aging not in ("", "0-30", "31-60", "61-90", "90+"):
        raise FinanceError("账龄筛选无效")
    with get_db() as conn:
        scoped, params = scope_sql(store_id=store_id)
        date_clause = " AND t.business_date <= ?" if as_of else ""
        if as_of:
            params.append(as_of)
        ledger = conn.execute(
            f"SELECT t.* FROM supplier_account_transactions t WHERE 1 = 1 {scoped} {date_clause} "
            "ORDER BY business_date, id", params,
        ).fetchall()
        from datetime import datetime
        cutoff = datetime.strptime(as_of or now()[:10], "%Y-%m-%d").date()
        reversal_ids = {row["reversal_of_id"] for row in ledger if row["reversal_of_id"]}
        historical_allocated = {}
        historical_returned = {}
        for row in ledger:
            if row["source_type"] in ("supplier_payment", "supplier_balance") and row["source_item_id"]:
                target = row["source_item_id"]
                historical_allocated[target] = historical_allocated.get(target, 0) - row["payable_delta_cents"]
            if row["source_type"] == "purchase_return" and row["source_item_id"]:
                target = row["source_item_id"]
                historical_returned[target] = historical_returned.get(target, 0) - row["payable_delta_cents"]
        grouped = {}
        for row in ledger:
            result = grouped.setdefault(row["supplier_id"], {
                "payableCents": 0, "prepaymentCents": 0, "creditCents": 0,
                "confirmedCents": 0, "allocatedCents": 0, "billedCents": 0,
                "returnedCents": 0,
                "aging": {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0},
            })
            result["payableCents"] += row["payable_delta_cents"]
            result["prepaymentCents"] += row["prepayment_delta_cents"]
            result["creditCents"] += row["credit_delta_cents"]
            if (not row["reversal_of_id"] and row["id"] not in reversal_ids
                    and row["transaction_type"] in ("INITIAL", "PURCHASE_INBOUND", "INDEPENDENT_PURCHASE_INBOUND")):
                principal = row["amount_including_tax_cents"]
                allocated = historical_allocated.get(row["id"], 0) if as_of else row["allocated_cents"]
                returned = historical_returned.get(row["id"], 0) if as_of else returned_payable_cents(conn, row["id"])
                result["confirmedCents"] += principal if row["payable_delta_cents"] >= 0 else 0
                result["allocatedCents"] += allocated
                result["returnedCents"] += returned
                result["billedCents"] += row["billed_cents"]
                days = max(0, (cutoff - datetime.strptime(row["business_date"], "%Y-%m-%d").date()).days)
                bucket = "0-30" if days <= 30 else "31-60" if days <= 60 else "61-90" if days <= 90 else "90+"
                result["aging"][bucket] += max(0, row["payable_delta_cents"] - allocated - returned)
        results = []
        for supplier in conn.execute("SELECT id, supplier_name, supplier_code, store_id FROM suppliers ORDER BY supplier_name"):
            if supplier["store_id"] is not None:
                scoped_supplier, supplier_params = scope_sql(alias="s", store_id=store_id)
                if not conn.execute(f"SELECT 1 FROM suppliers s WHERE id = ? {scoped_supplier}", (supplier["id"], *supplier_params)).fetchone():
                    continue
            if keyword and keyword not in (supplier["supplier_name"] + (supplier["supplier_code"] or "")).lower():
                continue
            data = grouped.get(supplier["id"], {})
            buckets = data.get("aging", {})
            if aging and not buckets.get(aging):
                continue
            payable = data.get("payableCents", 0)
            prepayment, credit = data.get("prepaymentCents", 0), data.get("creditCents", 0)
            confirmed, allocated, billed = data.get("confirmedCents", 0), data.get("allocatedCents", 0), data.get("billedCents", 0)
            returned = data.get("returnedCents", 0)
            results.append({
                "supplierId": supplier["id"], "supplierName": supplier["supplier_name"],
                "supplierCode": supplier["supplier_code"] or "", "storeId": supplier["store_id"],
                "payableBalance": amount(payable), "prepaymentBalance": amount(prepayment),
                "creditBalance": amount(credit), "netSettlement": amount(payable - prepayment - credit),
                "confirmedPayable": amount(max(0, confirmed - returned)), "allocatedAmount": amount(allocated),
                "returnedAmount": amount(returned),
                "unpaidAmount": amount(max(0, confirmed - allocated - returned)),
                "billedAmount": amount(billed), "unbilledAmount": amount(max(0, confirmed - billed)),
                "aging": {key: amount(value) for key, value in buckets.items()},
                "paymentStatus": "not_confirmed" if not data else "paid" if payable == 0 and prepayment == 0 and credit == 0
                                 else "partial" if allocated > 0 else "unpaid",
                "hasAvailableBalance": prepayment > 0 or credit > 0,
            })
        return jsonify(results)


def serialize_transaction(row):
    return {
        "id": row["id"], "supplierId": row["supplier_id"], "storeId": row["store_id"],
        "businessDate": row["business_date"], "auditedAt": row["audited_at"],
        "createdBy": row["created_by"], "businessType": row["transaction_type"],
        "sourceType": row["source_type"], "sourceId": row["source_id"],
        "sourceItemId": row["source_item_id"], "documentNo": row["source_document_no"],
        "purchaseOrderId": row["purchase_order_id"], "productName": row["product_name"],
        "amountExcludingTax": amount(row["amount_excluding_tax_cents"]),
        "taxAmount": amount(row["tax_amount_cents"]), "amountIncludingTax": amount(row["amount_including_tax_cents"]),
        "payableChange": amount(row["payable_delta_cents"]),
        "prepaymentChange": amount(row["prepayment_delta_cents"]), "creditChange": amount(row["credit_delta_cents"]),
        "allocatedAmount": amount(row["allocated_cents"]), "billedAmount": amount(row["billed_cents"]),
        "unbilledAmount": amount(max(0, row["amount_including_tax_cents"] - row["billed_cents"])),
        "invoiceStatus": row["invoice_status"], "invoiceRemark": row["invoice_remark"],
        "invoiceManaged": bool(row["invoice_managed"]),
        "version": row["version"], "reversalOfId": row["reversal_of_id"], "remark": row["remark"],
    }


@supplier_finance_bp.route("/suppliers/<int:supplier_id>/debt-details")
@require_admin_permission("admin.finance.supplier_statement.read")
@finance_errors
def supplier_statement(supplier_id):
    start = business_date(request.args["startDate"]) if request.args.get("startDate") else None
    end = business_date(request.args["endDate"]) if request.args.get("endDate") else None
    if start and end and start > end:
        raise FinanceError("开始日期不能晚于结束日期")
    export = request.args.get("export") == "1"
    if export:
        from utils.auth import admin_permission_granted
        if not admin_permission_granted("admin.finance.supplier_statement.export"):
            raise FinanceError("无权导出供应商对账单", 403)
    with get_db() as conn:
        supplier = supplier_row(conn, supplier_id)
        scoped, params = scope_sql(store_id=request.args.get("storeId", type=int))
        rows = conn.execute(
            f"SELECT t.* FROM supplier_account_transactions t WHERE supplier_id = ? {scoped} "
            "ORDER BY business_date, id", (supplier_id, *params),
        ).fetchall()
        running = {"payable": 0, "prepayment": 0, "credit": 0}
        opening = dict(running)
        period, changes = [], dict(running)
        reversed_ids = {row["reversal_of_id"] for row in rows
                        if row["reversal_of_id"] and (not end or row["business_date"] <= end)}
        for row in rows:
            if end and row["business_date"] > end:
                break
            for key in running:
                running[key] += row[f"{key}_delta_cents"]
            if start and row["business_date"] < start:
                opening = dict(running)
                continue
            entry = serialize_transaction(row)
            entry["status"] = "reversal" if row["reversal_of_id"] else "reversed" if row["id"] in reversed_ids else "audited"
            entry["balances"] = {key: amount(value) for key, value in running.items()}
            period.append(entry)
            for key in changes:
                changes[key] += row[f"{key}_delta_cents"]
        # Filters change visible rows, not the accounting equation.
        filtered = [row for row in period
                    if (not request.args.get("businessType") or row["businessType"] == request.args["businessType"])
                    and (not request.args.get("invoiceStatus") or row["invoiceStatus"] == request.args["invoiceStatus"])]
        page = max(1, request.args.get("page", default=1, type=int))
        page_size = min(200, max(1, request.args.get("pageSize", default=50, type=int)))
        selected = filtered if export else filtered[(page - 1) * page_size:page * page_size]
        return jsonify({
            "supplier": {"id": supplier_id, "name": supplier["supplier_name"]},
            "opening": {key: amount(value) for key, value in opening.items()},
            "changes": {key: amount(value) for key, value in changes.items()},
            "closing": {key: amount(value) for key, value in running.items()},
            "items": selected, "total": len(filtered), "page": page, "pageSize": page_size,
        })


@supplier_finance_bp.route("/suppliers/<int:supplier_id>/initial-balances", methods=["POST"])
@require_admin_permission("admin.finance.payable.initial")
@finance_errors
def initial_balance(supplier_id):
    data = request.get_json(silent=True) or {}
    store_id = positive_id(data.get("storeId"))
    check_scope(store_id)
    date = business_date(data.get("businessDate"))
    values = [cents(data.get(key, 0)) for key in ("payableAmount", "prepaymentAmount", "creditAmount")]
    if not any(values):
        raise FinanceError("至少填写一项非零期初余额")
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        supplier = supplier_row(conn, supplier_id)
        if supplier["store_id"] not in (None, store_id):
            raise FinanceError("供应商不属于所选门店")
        replay, token = idempotent_result(conn, f"supplier:{supplier_id}:{store_id}:initial", data)
        if replay:
            return jsonify(replay)
        from utils.supplier_periods import ensure_period_open
        ensure_period_open(conn, supplier_id, store_id, date)
        if conn.execute(
            "SELECT 1 FROM supplier_account_transactions WHERE supplier_id = ? AND store_id = ?",
            (supplier_id, store_id),
        ).fetchone():
            raise FinanceError("该供应商门店已有新账务流水，不能再录入期初余额", 409)
        cursor = conn.execute(
            """INSERT INTO supplier_account_transactions (
                supplier_id, store_id, business_date, audited_at, created_by,
                transaction_type, source_type, source_id, source_item_id, source_document_no,
                amount_excluding_tax_cents, amount_including_tax_cents, payable_delta_cents,
                prepayment_delta_cents, credit_delta_cents, invoice_status, remark
            ) VALUES (?, ?, ?, ?, ?, 'INITIAL', 'initial', ?, ?, ?, ?, ?, ?, ?, ?, 'not_required', ?)""",
            (supplier_id, store_id, date, now(), current_identity(), supplier_id, store_id,
             f"QC-{supplier_id}-{store_id}", values[0], values[0], *values, str(data.get("remark", ""))[:500]),
        )
        return jsonify(save_operation(conn, token, {
            "success": True, "transactionId": cursor.lastrowid,
            "balance": balance(conn, supplier_id, store_id), "businessDate": date,
            "auditedAt": now(), "createdBy": current_identity(), "version": 1,
        })), 201


@supplier_finance_bp.route("/supplier-payables/<int:transaction_id>/invoice", methods=["PUT"])
@require_admin_permission("admin.purchase.invoice_status.edit")
@finance_errors
def update_invoice_status(transaction_id):
    data = request.get_json(silent=True) or {}
    status = data.get("invoiceStatus")
    if status not in ("not_required", "unbilled", "partial", "billed", "difference"):
        raise FinanceError("开票状态无效")
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            f"SELECT * FROM supplier_account_transactions t WHERE id = ? AND {effective_sql()}",
            (transaction_id,),
        ).fetchone()
        if not row:
            raise FinanceError("应付来源不存在或已冲销", 404)
        if row["source_type"] != "stock_inbound":
            raise FinanceError("仅采购入库应付可登记基础开票状态", 409)
        if row["invoice_managed"]:
            raise FinanceError("该应付已有正式发票分配，请通过发票登记调整", 409)
        check_scope(row["store_id"])
        check_version(data, row)
        if row["locked_at"]:
            raise FinanceError("应付来源已被正式对账锁定，不能修改开票状态", 409)
        billed = cents(data.get("billedAmount", 0))
        if status == "unbilled" and billed != 0:
            raise FinanceError("未开票金额必须为零")
        if status == "not_required" and billed != 0:
            raise FinanceError("无需开票的已开票金额必须为零")
        if status == "partial" and not 0 < billed < row["amount_including_tax_cents"]:
            raise FinanceError("部分开票金额必须大于零且小于应付金额")
        if status == "billed" and billed != row["amount_including_tax_cents"]:
            raise FinanceError("已开票金额必须等于应付金额")
        if billed > row["amount_including_tax_cents"] and status != "difference":
            raise FinanceError("超额开票必须登记为开票有差异")
        if status == "difference" and not str(data.get("invoiceRemark", "")).strip():
            raise FinanceError("开票差异必须填写备注")
        conn.execute(
            """UPDATE supplier_account_transactions SET invoice_status = ?, billed_cents = ?, invoice_remark = ?,
               manual_invoice_status = ?, manual_billed_cents = ?, manual_invoice_remark = ?,
               invoice_updated_by = ?, invoice_updated_at = ?, version = version + 1 WHERE id = ?""",
            (status, billed, str(data.get("invoiceRemark", ""))[:500],
             status, billed, str(data.get("invoiceRemark", ""))[:500], current_identity(), now(), transaction_id),
        )
        updated = conn.execute("SELECT * FROM supplier_account_transactions WHERE id = ?", (transaction_id,)).fetchone()
        return jsonify({"success": True, "transaction": serialize_transaction(updated)})


def expense_response(row):
    data = {key: row[key] for key in ("id", "status", "version", "remark")}
    for key, target in {
        "purchase_order_id": "purchaseOrderId", "purchase_order_item_id": "purchaseOrderItemId",
        "inbound_item_id": "inboundItemId", "supplier_id": "supplierId", "expense_type": "expenseType",
        "confirmed_by": "confirmedBy", "confirmed_at": "confirmedAt", "created_by": "createdBy", "created_at": "createdAt",
    }.items():
        data[target] = row[key]
    for key, target in {
        "amount_excluding_tax_cents": "amountExcludingTax", "tax_amount_cents": "taxAmount",
        "amount_including_tax_cents": "amountIncludingTax",
    }.items():
        data[target] = amount(row[key])
    data["includeInPayable"] = bool(row["include_in_payable"])
    data["includeInInventoryCost"] = bool(row["include_in_inventory_cost"])
    return data


def expense_order(conn, order_id):
    row = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        raise FinanceError("采购订单不存在", 404)
    check_scope(row["store_id"])
    return row


def expense_values(conn, order_id, data):
    order = expense_order(conn, order_id)
    if order["status"] not in ("approved", "partial", "completed"):
        raise FinanceError("请先审核采购订单，再归属实际批次费用", 409)
    supplier_id, item_id = positive_id(data.get("supplierId")), positive_id(data.get("purchaseOrderItemId"))
    item = conn.execute(
        "SELECT * FROM purchase_order_items WHERE id = ? AND order_id = ?", (item_id, order_id)
    ).fetchone()
    if not item or item["supplier_id"] != supplier_id:
        raise FinanceError("费用供应商必须与采购商品明细一致")
    inbound_item_id = positive_id(data["inboundItemId"]) if data.get("inboundItemId") else None
    if inbound_item_id:
        source = conn.execute(
            """SELECT i.*, d.status, d.warehouse_id default_warehouse_id FROM stock_inbound_items i
               JOIN stock_inbounds d ON d.id = i.inbound_id
               WHERE i.id = ? AND d.purchase_order_id = ? AND i.purchase_order_item_id = ?""",
            (inbound_item_id, order_id, item_id),
        ).fetchone()
        if not source:
            raise FinanceError("费用入库明细与采购商品不匹配")
        if source["status"] != "draft":
            raise FinanceError("费用只能归属未审核的入库批次", 409)
        check_scope(order["store_id"], [source["warehouse_id"] or source["default_warehouse_id"]])
    base, tax = cents(data.get("amountExcludingTax", 0)), cents(data.get("taxAmount", 0))
    if base + tax <= 0:
        raise FinanceError("费用金额必须大于零")
    if "amountIncludingTax" in data and cents(data["amountIncludingTax"]) != base + tax:
        raise FinanceError("含税金额必须等于未税金额加税额")
    for key in ("includeInPayable", "includeInInventoryCost"):
        if key in data and not isinstance(data[key], bool):
            raise FinanceError("费用归属开关必须是布尔值")
    return (item_id, inbound_item_id, supplier_id, str(data.get("expenseType", "其它费用"))[:80],
            base, tax, base + tax, int(data.get("includeInPayable", True)),
            int(data.get("includeInInventoryCost", False)), str(data.get("remark", ""))[:500])


@supplier_finance_bp.route("/purchase-orders/<int:order_id>/expenses")
@require_admin_permission("admin.route.purchase.orders")
@finance_errors
def list_expenses(order_id):
    with get_db() as conn:
        expense_order(conn, order_id)
        return jsonify([expense_response(row) for row in conn.execute(
            "SELECT * FROM purchase_expense_lines WHERE purchase_order_id = ? ORDER BY id", (order_id,)
        )])


@supplier_finance_bp.route("/purchase-orders/<int:order_id>/expenses", methods=["POST"])
@require_admin_permission("admin.purchase.expense.create")
@finance_errors
def create_expense(order_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        replay, token = idempotent_result(conn, f"expense:{order_id}:create", data)
        if replay:
            return jsonify(replay)
        values = expense_values(conn, order_id, data)
        cursor = conn.execute(
            """INSERT INTO purchase_expense_lines (
                purchase_order_id, purchase_order_item_id, inbound_item_id, supplier_id, expense_type,
                amount_excluding_tax_cents, tax_amount_cents, amount_including_tax_cents,
                include_in_payable, include_in_inventory_cost, remark, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, *values, current_identity(), now()),
        )
        row = conn.execute("SELECT * FROM purchase_expense_lines WHERE id = ?", (cursor.lastrowid,)).fetchone()
        result = save_operation(conn, token, {"success": True, "expense": expense_response(row)})
        return jsonify(result), 201


def load_expense(conn, expense_id):
    row = conn.execute("SELECT * FROM purchase_expense_lines WHERE id = ?", (expense_id,)).fetchone()
    if not row:
        raise FinanceError("采购费用不存在", 404)
    expense_order(conn, row["purchase_order_id"])
    return row


@supplier_finance_bp.route("/purchase-expenses/<int:expense_id>", methods=["PUT"])
@require_admin_permission("admin.purchase.expense.edit")
@finance_errors
def edit_expense(expense_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = load_expense(conn, expense_id)
        if row["status"] != "draft":
            raise FinanceError("已确认费用不能修改", 409)
        check_version(data, row)
        values = expense_values(conn, row["purchase_order_id"], data)
        conn.execute(
            """UPDATE purchase_expense_lines SET purchase_order_item_id = ?, inbound_item_id = ?, supplier_id = ?,
               expense_type = ?, amount_excluding_tax_cents = ?, tax_amount_cents = ?, amount_including_tax_cents = ?,
               include_in_payable = ?, include_in_inventory_cost = ?, remark = ?, version = version + 1 WHERE id = ?""",
            (*values, expense_id),
        )
        return jsonify({"success": True, "expense": expense_response(load_expense(conn, expense_id))})


@supplier_finance_bp.route("/purchase-expenses/<int:expense_id>", methods=["DELETE"])
@require_admin_permission("admin.purchase.expense.delete")
@finance_errors
def delete_expense(expense_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = load_expense(conn, expense_id)
        if row["status"] != "draft":
            raise FinanceError("请先撤销费用确认", 409)
        check_version(data, row)
        conn.execute("DELETE FROM purchase_expense_lines WHERE id = ?", (expense_id,))
        return jsonify({"success": True, "deleted": True})


@supplier_finance_bp.route("/purchase-expenses/<int:expense_id>/confirm", methods=["POST", "DELETE"])
@require_admin_permission("admin.purchase.expense.confirm")
@finance_errors
def confirm_expense(expense_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = load_expense(conn, expense_id)
        replay, token = idempotent_result(conn, f"expense:{expense_id}:{request.method}", data)
        if replay:
            return jsonify(replay)
        target = "confirmed" if request.method == "POST" else "draft"
        if row["status"] == target:
            return jsonify(save_operation(conn, token, {"success": True, "expense": expense_response(row)}))
        check_version(data, row)
        values = expense_values(conn, row["purchase_order_id"], expense_response(row))
        if not values[1]:
            raise FinanceError("请明确归属到实际入库批次商品明细")
        conn.execute(
            "UPDATE purchase_expense_lines SET status = ?, confirmed_by = ?, confirmed_at = ?, version = version + 1 WHERE id = ?",
            (target, current_identity() if target == "confirmed" else None, now() if target == "confirmed" else None, expense_id),
        )
        return jsonify(save_operation(conn, token, {"success": True, "expense": expense_response(load_expense(conn, expense_id))}))
