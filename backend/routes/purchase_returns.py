"""Purchase returns backed by inbound batches, inventory movements and supplier ledger."""

from decimal import Decimal

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.supplier_ledger import (
    FinanceError, amount, business_date, cents, check_scope, effective_sql,
    idempotent_result, now, returned_payable_cents, save_operation, scope_sql,
)
from utils.supplier_settlement import (
    add_ledger, positive_id, quantity, required_version, supplier_store, text,
)
from routes.supplier_finance import finance_errors


purchase_returns_bp = Blueprint("purchase_returns", __name__, url_prefix="/api")
READ = "admin.route.purchase.returns"


def return_row(conn, return_id):
    row = conn.execute("SELECT * FROM purchase_returns WHERE id = ?", (return_id,)).fetchone()
    if not row:
        raise FinanceError("采购退货单不存在", 404)
    check_scope(row["store_id"])
    return row


def load_return_source(conn, inbound_item_id, supplier_id, store_id):
    row = conn.execute(
        f"""SELECT i.*, d.document_no inbound_no, d.document_date, d.store_id inbound_store_id,
                   d.warehouse_id inbound_warehouse_id, d.status inbound_status,
                   t.id payable_id, t.business_date payable_date, t.payable_delta_cents,
                   t.allocated_cents, t.locked_at payable_locked_at,
                   t.purchase_order_id, t.purchase_order_item_id,
                   m.unit_price original_unit_price,
                   w.name warehouse_name
            FROM stock_inbound_items i
            JOIN stock_inbounds d ON d.id = i.inbound_id
            JOIN supplier_account_transactions t ON t.source_type = 'stock_inbound'
                 AND t.source_item_id = i.id AND t.supplier_id = ? AND t.store_id = d.store_id
                 AND t.transaction_type IN ('PURCHASE_INBOUND', 'INDEPENDENT_PURCHASE_INBOUND')
                 AND {effective_sql('t')}
            JOIN stock_movements m ON m.movement_type = 'in'
                 AND m.source_document_id = d.id AND m.source_item_id = i.id
                 AND m.product_type = 'raw-material'
            LEFT JOIN warehouses w ON w.id = COALESCE(i.warehouse_id, d.warehouse_id)
            WHERE i.id = ? AND d.store_id = ? AND i.product_type = 'raw-material'
              AND d.status IN ('reviewed', 'posted')
            ORDER BY m.id DESC LIMIT 1""",
        (supplier_id, inbound_item_id, store_id),
    ).fetchone()
    if not row:
        raise FinanceError("请选择该供应商已确认应付的原材料入库批次", 409)
    check_scope(row["inbound_store_id"], [row["warehouse_id"] or row["inbound_warehouse_id"]])
    if row["payable_locked_at"]:
        raise FinanceError("来源应付已被正式对账锁定，不能退货", 409)
    returned = conn.execute(
        """SELECT COALESCE(SUM(CAST(i.quantity AS REAL)), 0) quantity
           FROM purchase_return_items i JOIN purchase_returns r ON r.id = i.return_id
           WHERE i.inbound_item_id = ? AND r.status = 'audited'""",
        (inbound_item_id,),
    ).fetchone()["quantity"]
    stock = conn.execute(
        """SELECT quantity FROM stock_balances WHERE product_type='raw-material'
           AND product_id=? AND warehouse_id=? AND store_id=? AND bin_code=? AND batch_no=?""",
        (row["product_id"], row["warehouse_id"] or row["inbound_warehouse_id"],
         store_id, row["bin_code"] or "", row["batch_no"] or ""),
    ).fetchone()
    original_qty = Decimal(str(row["received_qty"] or 0))
    returned_qty = Decimal(str(returned or 0))
    available_qty = max(Decimal("0"), original_qty - returned_qty)
    available_stock = Decimal(str(stock["quantity"] or 0)) if stock else Decimal("0")
    return {
        "source": row,
        "returnedQuantity": returned_qty,
        "availableQuantity": min(available_qty, available_stock),
    }


def return_values(conn, data):
    supplier_id, store_id = supplier_store(conn, data.get("supplierId"), data.get("storeId"))
    date = business_date(data.get("businessDate"))
    entries = data.get("items")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 300:
        raise FinanceError("退货明细必须是 1 至 300 项的数组")
    result, seen = [], set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise FinanceError("退货明细格式错误")
        inbound_item_id = positive_id(entry.get("inboundItemId"))
        if inbound_item_id in seen:
            raise FinanceError("同一入库明细不能重复退货")
        seen.add(inbound_item_id)
        loaded = load_return_source(conn, inbound_item_id, supplier_id, store_id)
        source = loaded["source"]
        qty = quantity(entry.get("quantity"))
        if qty <= 0:
            raise FinanceError("退货数量必须大于零")
        if qty > loaded["availableQuantity"]:
            raise FinanceError("退货数量超过该批次可退数量或当前库存", 409)
        if date < source["payable_date"]:
            raise FinanceError("退货日期不能早于来源入库日期")
        unit_price = cents(source["original_unit_price"] or 0)
        original_cost = cents(Decimal(unit_price) / 100 * qty)
        return_amount = cents(entry.get("returnAmount"))
        difference = original_cost - return_amount
        reason = text(entry.get("differenceReason"))
        if difference and not reason:
            raise FinanceError("退货金额与原库存成本不一致时必须填写差异原因")
        result.append({
            "line_no": index, "inbound_item_id": inbound_item_id,
            "payable_transaction_id": source["payable_id"], "quantity": str(qty),
            "original_unit_price_cents": unit_price, "original_cost_cents": original_cost,
            "return_amount_cents": return_amount, "difference_reason": reason,
        })
    return {
        "supplier_id": supplier_id, "store_id": store_id, "business_date": date,
        "remark": text(data.get("remark")), "items": result,
    }


def serialize_return(conn, row):
    supplier = conn.execute("SELECT supplier_name FROM suppliers WHERE id=?", (row["supplier_id"],)).fetchone()
    store = conn.execute("SELECT name FROM stores WHERE id=?", (row["store_id"],)).fetchone()
    items = []
    for line in conn.execute(
        """SELECT i.*, inbound.document_no inbound_no, inbound_item.product_name,
                  inbound_item.product_code, inbound_item.unit, inbound_item.batch_no,
                  inbound_item.bin_code, inbound_item.warehouse_id, inbound.warehouse_id inbound_warehouse_id
           FROM purchase_return_items i
           JOIN stock_inbound_items inbound_item ON inbound_item.id=i.inbound_item_id
           JOIN stock_inbounds inbound ON inbound.id=inbound_item.inbound_id
           WHERE i.return_id=? ORDER BY i.line_no, i.id""", (row["id"],)
    ):
        items.append({
            "id": line["id"], "lineNo": line["line_no"], "inboundItemId": line["inbound_item_id"],
            "payableTransactionId": line["payable_transaction_id"], "inboundDocumentNo": line["inbound_no"],
            "productName": line["product_name"], "productCode": line["product_code"],
            "unit": line["unit"], "batchNo": line["batch_no"], "binCode": line["bin_code"],
            "warehouseId": line["warehouse_id"] or line["inbound_warehouse_id"],
            "quantity": float(line["quantity"]), "originalUnitPrice": amount(line["original_unit_price_cents"]),
            "originalCost": amount(line["original_cost_cents"]),
            "returnAmount": amount(line["return_amount_cents"]),
            "appliedPayable": amount(line["applied_payable_cents"]), "creditAmount": amount(line["credit_cents"]),
            "differenceReason": line["difference_reason"],
        })
    return {
        "id": row["id"], "documentNo": row["document_no"], "supplierId": row["supplier_id"],
        "supplierName": supplier["supplier_name"], "storeId": row["store_id"], "storeName": store["name"],
        "businessDate": row["business_date"], "remark": row["remark"], "status": row["status"],
        "version": row["version"], "createdBy": row["created_by"], "createdAt": row["created_at"],
        "auditedBy": row["audited_by"], "auditedAt": row["audited_at"], "reversedAt": row["reversed_at"],
        "lockedAt": row["locked_at"], "items": items,
        "originalCost": amount(sum(item["original_cost_cents"] for item in conn.execute(
            "SELECT original_cost_cents FROM purchase_return_items WHERE return_id=?", (row["id"],)
        ))),
        "returnAmount": amount(sum(item["return_amount_cents"] for item in conn.execute(
            "SELECT return_amount_cents FROM purchase_return_items WHERE return_id=?", (row["id"],)
        ))),
    }


def next_document_no(conn, date):
    prefix = "TH" + date.replace("-", "")
    rows = conn.execute("SELECT document_no FROM purchase_returns WHERE document_no LIKE ?", (prefix + "%",))
    suffixes = [str(row["document_no"])[len(prefix):] for row in rows]
    return prefix + f"{max([int(value) for value in suffixes if value.isdigit()] or [0]) + 1:03d}"


def replace_items(conn, return_id, items):
    conn.execute("DELETE FROM purchase_return_items WHERE return_id=?", (return_id,))
    conn.executemany(
        """INSERT INTO purchase_return_items (
            return_id,line_no,inbound_item_id,payable_transaction_id,quantity,
            original_unit_price_cents,original_cost_cents,return_amount_cents,difference_reason
        ) VALUES (?,?,?,?,?,?,?,?,?)""",
        [(return_id, item["line_no"], item["inbound_item_id"], item["payable_transaction_id"],
          item["quantity"], item["original_unit_price_cents"], item["original_cost_cents"],
          item["return_amount_cents"], item["difference_reason"]) for item in items],
    )


@purchase_returns_bp.route("/purchase-returns/options")
@require_admin_permission(READ)
@finance_errors
def return_options():
    with get_db() as conn:
        scoped, params = scope_sql(alias="s")
        stores = [dict(row) for row in conn.execute(
            f"""SELECT s.id, s.name FROM stores s WHERE s.status='active' {scoped}
                ORDER BY s.name""", params
        )]
        store_ids = {row["id"] for row in stores}
        suppliers = [
            {"id": row["id"], "supplierName": row["supplier_name"], "storeId": row["store_id"]}
            for row in conn.execute("SELECT id,supplier_name,store_id FROM suppliers WHERE status='active' ORDER BY supplier_name")
            if row["store_id"] is None or row["store_id"] in store_ids
        ]
        return jsonify({"stores": stores, "suppliers": suppliers})


@purchase_returns_bp.route("/suppliers/<int:supplier_id>/purchase-return-sources")
@require_admin_permission(READ)
@finance_errors
def return_sources(supplier_id):
    store_id = positive_id(request.args.get("storeId"))
    with get_db() as conn:
        supplier_store(conn, supplier_id, store_id)
        rows = conn.execute(
            """SELECT i.id FROM stock_inbound_items i
               JOIN stock_inbounds d ON d.id=i.inbound_id
               JOIN supplier_account_transactions t ON t.source_type='stock_inbound'
                    AND t.source_item_id=i.id AND t.supplier_id=? AND t.store_id=d.store_id
                    AND t.transaction_type IN ('PURCHASE_INBOUND','INDEPENDENT_PURCHASE_INBOUND')
               WHERE d.store_id=? AND d.status IN ('reviewed','posted')
                 AND i.product_type='raw-material' AND t.reversal_of_id IS NULL
                 AND NOT EXISTS (SELECT 1 FROM supplier_account_transactions r WHERE r.reversal_of_id=t.id)
               ORDER BY d.document_date DESC, i.line_no, i.id""",
            (supplier_id, store_id),
        ).fetchall()
        result = []
        for item in rows:
            loaded = load_return_source(conn, item["id"], supplier_id, store_id)
            source = loaded["source"]
            if loaded["availableQuantity"] <= 0:
                continue
            result.append({
                "inboundItemId": source["id"], "inboundDocumentNo": source["inbound_no"],
                "inboundDate": source["document_date"], "payableTransactionId": source["payable_id"],
                "productId": source["product_id"], "productCode": source["product_code"],
                "productName": source["product_name"], "unit": source["unit"],
                "warehouseId": source["warehouse_id"] or source["inbound_warehouse_id"],
                "warehouseName": source["warehouse_name"], "binCode": source["bin_code"],
                "batchNo": source["batch_no"], "receivedQuantity": float(source["received_qty"] or 0),
                "returnedQuantity": float(loaded["returnedQuantity"]),
                "availableQuantity": float(loaded["availableQuantity"]),
                "originalUnitPrice": float(source["original_unit_price"] or 0),
                "originalPayable": amount(source["payable_delta_cents"]),
            })
        return jsonify({"items": result})


@purchase_returns_bp.route("/purchase-returns")
@require_admin_permission(READ)
@finance_errors
def list_returns():
    with get_db() as conn:
        scoped, params = scope_sql(alias="r", store_id=request.args.get("storeId", type=int))
        sql = f"SELECT r.* FROM purchase_returns r WHERE 1=1 {scoped}"
        for column, key in (("supplier_id", "supplierId"), ("status", "status")):
            if request.args.get(key):
                sql += f" AND r.{column}=?"
                params.append(positive_id(request.args[key]) if key == "supplierId" else request.args[key])
        for column, key, operator in (("business_date", "startDate", ">="), ("business_date", "endDate", "<=")):
            if request.args.get(key):
                sql += f" AND r.{column} {operator} ?"
                params.append(business_date(request.args[key]))
        rows = conn.execute(sql + " ORDER BY r.business_date DESC,r.id DESC", params).fetchall()
        items = [serialize_return(conn, row) for row in rows]
        keyword = text(request.args.get("keyword")).lower()
        items = [item for item in items if not keyword or keyword in
                 (item["documentNo"] + item["supplierName"] + item["remark"]).lower()]
        return jsonify({"items": items, "total": len(items)})


@purchase_returns_bp.route("/purchase-returns/<int:return_id>")
@require_admin_permission(READ)
@finance_errors
def get_return(return_id):
    with get_db() as conn:
        return jsonify(serialize_return(conn, return_row(conn, return_id)))


@purchase_returns_bp.route("/purchase-returns", methods=["POST"])
@require_admin_permission("admin.purchase.return.create")
@finance_errors
def create_return():
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        supplier_store(conn, data.get("supplierId"), data.get("storeId"))
        replay, token = idempotent_result(conn, "purchase-return:create", data)
        if replay:
            return jsonify(replay)
        values = return_values(conn, data)
        document_no = next_document_no(conn, values["business_date"])
        cursor = conn.execute(
            """INSERT INTO purchase_returns (
                document_no,supplier_id,store_id,business_date,remark,created_by,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?)""",
            (document_no, values["supplier_id"], values["store_id"], values["business_date"],
             values["remark"], current_identity(), now(), now()),
        )
        replace_items(conn, cursor.lastrowid, values["items"])
        row = return_row(conn, cursor.lastrowid)
        return jsonify(save_operation(conn, token, {
            "success": True, "purchaseReturn": serialize_return(conn, row)
        })), 201


@purchase_returns_bp.route("/purchase-returns/<int:return_id>", methods=["PUT"])
@require_admin_permission("admin.purchase.return.edit")
@finance_errors
def edit_return(return_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = return_row(conn, return_id)
        if row["status"] != "draft" or row["locked_at"]:
            raise FinanceError("只有未审核采购退货草稿可以修改", 409)
        required_version(data, row)
        values = return_values(conn, data)
        if values["supplier_id"] != row["supplier_id"] or values["store_id"] != row["store_id"]:
            raise FinanceError("退货供应商和门店不能修改", 409)
        conn.execute(
            """UPDATE purchase_returns SET business_date=?,remark=?,version=version+1,updated_at=?
               WHERE id=?""", (values["business_date"], values["remark"], now(), return_id)
        )
        replace_items(conn, return_id, values["items"])
        return jsonify({"success": True, "purchaseReturn": serialize_return(conn, return_row(conn, return_id))})


@purchase_returns_bp.route("/purchase-returns/<int:return_id>", methods=["DELETE"])
@require_admin_permission("admin.purchase.return.delete")
@finance_errors
def delete_return(return_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = return_row(conn, return_id)
        if row["status"] != "draft" or row["locked_at"]:
            raise FinanceError("只有未审核采购退货草稿可以删除", 409)
        required_version(data, row)
        conn.execute("DELETE FROM purchase_returns WHERE id=?", (return_id,))
        return jsonify({"success": True, "deleted": True})


@purchase_returns_bp.route("/purchase-returns/<int:return_id>/audit", methods=["POST"])
@require_admin_permission("admin.purchase.return.audit")
@finance_errors
def audit_return(return_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = return_row(conn, return_id)
        replay, token = idempotent_result(conn, f"purchase-return:{return_id}:audit", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "audited":
            return jsonify(save_operation(conn, token, {
                "success": True, "purchaseReturn": serialize_return(conn, row)
            }))
        required_version(data, row)
        if row["status"] not in ("draft", "reversed") or row["locked_at"]:
            raise FinanceError("采购退货状态不允许审核", 409)
        from utils.supplier_periods import ensure_period_open
        ensure_period_open(conn, row["supplier_id"], row["store_id"], row["business_date"])
        document = dict(row)
        document["version"] += 1
        lines = conn.execute(
            "SELECT * FROM purchase_return_items WHERE return_id=? ORDER BY line_no,id", (return_id,)
        ).fetchall()
        if not lines:
            raise FinanceError("采购退货明细不能为空")
        consumed_by_source = {}
        for line in lines:
            loaded = load_return_source(conn, line["inbound_item_id"], row["supplier_id"], row["store_id"])
            source = loaded["source"]
            qty = quantity(line["quantity"])
            if qty > loaded["availableQuantity"]:
                raise FinanceError("当前批次可退数量或库存已变化，请刷新后重试", 409)
            available = max(
                0,
                source["payable_delta_cents"] - source["allocated_cents"]
                - returned_payable_cents(conn, source["payable_id"])
                - consumed_by_source.get(source["payable_id"], 0),
            )
            applied = min(line["return_amount_cents"], available)
            credit = line["return_amount_cents"] - applied
            product_type = "raw-material"
            warehouse_id = source["warehouse_id"] or source["inbound_warehouse_id"] or 0
            bin_code, batch_no = source["bin_code"] or "", source["batch_no"] or ""
            stock = conn.execute(
                """UPDATE stock_balances SET quantity=quantity-?,updated_at=?
                   WHERE product_type=? AND product_id=? AND warehouse_id=? AND store_id=?
                     AND bin_code=? AND batch_no=? AND quantity+0.0000001>=?""",
                (float(qty), now(), product_type, source["product_id"], warehouse_id,
                 row["store_id"], bin_code, batch_no, float(qty)),
            )
            if stock.rowcount != 1:
                raise FinanceError("当前批次库存不足，不能审核采购退货", 409)
            movement = conn.execute(
                """INSERT INTO stock_movements (
                    movement_type,receipt_type,source_document_id,source_document_no,source_item_id,
                    product_type,product_id,warehouse_id,store_id,bin_code,batch_no,quantity,
                    unit_price,tax_rate,total_amount,created_at
                ) VALUES ('out','purchase-return',?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (return_id, row["document_no"], line["id"], product_type, source["product_id"],
                 warehouse_id, row["store_id"], bin_code, batch_no, float(qty),
                 float(source["original_unit_price"] or 0), source["tax_rate"],
                 amount(line["original_cost_cents"]), now()),
            )
            conn.execute(
                """INSERT INTO purchase_return_stock_events
                   (return_item_id,document_version,movement_id) VALUES (?,?,?)""",
                (line["id"], document["version"], movement.lastrowid),
            )
            target = {
                "product_name": source["product_name"],
                "purchase_order_id": source["purchase_order_id"],
                "purchase_order_item_id": source["purchase_order_item_id"],
            }
            add_ledger(
                conn, document, "purchase_return", return_id, source["payable_id"],
                "PURCHASE_RETURN", payable=-applied, credit=credit, target=target,
            )
            difference = line["original_cost_cents"] - line["return_amount_cents"]
            if difference:
                add_ledger(
                    conn, document, "purchase_return", return_id, source["payable_id"],
                    "PURCHASE_RETURN_ADJUSTMENT", target=target,
                )
                conn.execute(
                    """UPDATE supplier_account_transactions SET amount_excluding_tax_cents=?,
                       amount_including_tax_cents=?,remark=? WHERE source_type='purchase_return'
                         AND source_id=? AND source_item_id=? AND transaction_type='PURCHASE_RETURN_ADJUSTMENT'
                         AND document_version=?""",
                    (abs(difference), abs(difference), line["difference_reason"],
                     return_id, source["payable_id"], document["version"]),
                )
            conn.execute(
                """UPDATE purchase_return_items SET applied_payable_cents=?,credit_cents=?
                   WHERE id=?""", (applied, credit, line["id"])
            )
            consumed_by_source[source["payable_id"]] = consumed_by_source.get(source["payable_id"], 0) + applied
        conn.execute(
            """UPDATE purchase_returns SET status='audited',version=version+1,audited_by=?,
               audited_at=?,reversed_at=NULL,updated_at=? WHERE id=?""",
            (current_identity(), now(), now(), return_id),
        )
        return jsonify(save_operation(conn, token, {
            "success": True, "purchaseReturn": serialize_return(conn, return_row(conn, return_id))
        }))


@purchase_returns_bp.route("/purchase-returns/<int:return_id>/reverse-audit", methods=["POST"])
@require_admin_permission("admin.purchase.return.reverse_audit")
@finance_errors
def reverse_return(return_id):
    data = request.get_json(silent=True) or {}
    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = return_row(conn, return_id)
        replay, token = idempotent_result(conn, f"purchase-return:{return_id}:reverse", data)
        if replay:
            return jsonify(replay)
        if row["status"] == "reversed":
            return jsonify(save_operation(conn, token, {
                "success": True, "purchaseReturn": serialize_return(conn, row)
            }))
        required_version(data, row)
        if row["status"] != "audited" or row["locked_at"]:
            raise FinanceError("只有未锁定的已审核采购退货可以反审核", 409)
        from utils.supplier_settlement import reverse_ledger
        reverse_ledger(conn, "purchase_return", return_id)
        events = conn.execute(
            """SELECT e.*,m.* FROM purchase_return_stock_events e
               JOIN stock_movements m ON m.id=e.movement_id
               WHERE e.reversal_movement_id IS NULL AND e.return_item_id IN
                   (SELECT id FROM purchase_return_items WHERE return_id=?)""",
            (return_id,),
        ).fetchall()
        for event in events:
            conn.execute(
                """INSERT INTO stock_balances (
                    product_type,product_id,warehouse_id,store_id,bin_code,batch_no,quantity,updated_at
                ) VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(product_type,product_id,warehouse_id,store_id,bin_code,batch_no)
                DO UPDATE SET quantity=stock_balances.quantity+excluded.quantity,updated_at=excluded.updated_at""",
                (event["product_type"], event["product_id"], event["warehouse_id"], event["store_id"],
                 event["bin_code"], event["batch_no"], event["quantity"], now()),
            )
            movement = conn.execute(
                """INSERT INTO stock_movements (
                    movement_type,receipt_type,source_document_id,source_document_no,source_item_id,
                    product_type,product_id,warehouse_id,store_id,bin_code,batch_no,quantity,
                    unit_price,tax_rate,total_amount,created_at
                ) VALUES ('in','purchase-return-reversal',?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (return_id, row["document_no"], event["source_item_id"], event["product_type"],
                 event["product_id"], event["warehouse_id"], event["store_id"], event["bin_code"],
                 event["batch_no"], event["quantity"], event["unit_price"], event["tax_rate"],
                 event["total_amount"], now()),
            )
            conn.execute(
                "UPDATE purchase_return_stock_events SET reversal_movement_id=? WHERE id=?",
                (movement.lastrowid, event["id"]),
            )
        conn.execute(
            """UPDATE purchase_returns SET status='reversed',version=version+1,reversed_at=?,updated_at=?
               WHERE id=?""", (now(), now(), return_id)
        )
        return jsonify(save_operation(conn, token, {
            "success": True, "purchaseReturn": serialize_return(conn, return_row(conn, return_id))
        }))

