"""Order-backed invoices and their later allocation to actual inbound payables."""

from decimal import Decimal, ROUND_HALF_UP

from utils.supplier_ledger import FinanceError, amount, cents, check_scope, effective_sql


def ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS purchase_invoice_order_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL REFERENCES purchase_invoices(id) ON DELETE CASCADE,
            purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id),
            purchase_order_item_id INTEGER NOT NULL,
            document_no TEXT NOT NULL,
            product_name TEXT NOT NULL,
            business_date TEXT NOT NULL,
            source_amount_cents INTEGER NOT NULL,
            amount_excluding_tax_cents INTEGER NOT NULL,
            tax_amount_cents INTEGER NOT NULL,
            amount_including_tax_cents INTEGER NOT NULL,
            quantity TEXT NOT NULL DEFAULT '0',
            UNIQUE(invoice_id, purchase_order_item_id)
        );
        CREATE INDEX IF NOT EXISTS idx_invoice_order_source
            ON purchase_invoice_order_allocations(purchase_order_id, purchase_order_item_id);
        CREATE INDEX IF NOT EXISTS idx_invoice_order_item
            ON purchase_invoice_order_allocations(purchase_order_item_id);
        CREATE TABLE IF NOT EXISTS purchase_invoice_order_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_allocation_id INTEGER NOT NULL REFERENCES purchase_invoice_order_allocations(id) ON DELETE CASCADE,
            payable_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            amount_excluding_tax_cents INTEGER NOT NULL,
            tax_amount_cents INTEGER NOT NULL,
            amount_including_tax_cents INTEGER NOT NULL,
            quantity TEXT NOT NULL DEFAULT '0',
            UNIQUE(order_allocation_id, payable_transaction_id)
        );
        CREATE INDEX IF NOT EXISTS idx_invoice_order_match_payable
            ON purchase_invoice_order_matches(payable_transaction_id);
    """)


def load_order_source(conn, item_id, supplier_id=None, store_id=None):
    from utils.supplier_settlement import positive_id
    row = conn.execute(
        """SELECT p.*, o.store_id, o.order_no, o.order_date, o.status order_status
           FROM purchase_order_items p JOIN purchase_orders o ON o.id = p.order_id
           WHERE p.id = ?""", (positive_id(item_id),),
    ).fetchone()
    if not row:
        raise FinanceError("采购订单明细不存在", 404)
    check_scope(row["store_id"])
    if row["order_status"] not in ("approved", "partial", "completed"):
        raise FinanceError("采购订单审核通过后才能登记发票", 409)
    if supplier_id is not None and (row["supplier_id"] != supplier_id or row["store_id"] != store_id):
        raise FinanceError("采购订单明细的供应商或门店与发票不一致")
    if not row["supplier_id"] or row["unit_price"] is None:
        raise FinanceError("采购订单明细必须有供应商和采购单价")
    base, tax = cents(row["amount"] or 0), cents(row["tax_amount"] or 0)
    return {
        **dict(row), "purchase_order_id": row["order_id"],
        "amount_excluding_tax_cents": base, "tax_amount_cents": tax,
        "amount_including_tax_cents": base + tax,
    }


def order_usage(conn, item_id):
    roots = conn.execute(
        """SELECT a.amount_including_tax_cents, a.quantity
           FROM purchase_invoice_order_allocations a JOIN purchase_invoices i ON i.id = a.invoice_id
           WHERE a.purchase_order_item_id = ? AND i.status = 'confirmed'""", (item_id,),
    ).fetchall()
    payables = conn.execute(
        f"""SELECT t.* FROM supplier_account_transactions t
            WHERE t.purchase_order_item_id = ? AND t.source_type = 'stock_inbound'
              AND {effective_sql()}""", (item_id,),
    ).fetchall()
    used = sum(row["amount_including_tax_cents"] for row in roots)
    qty = sum((Decimal(row["quantity"]) for row in roots), Decimal(0))
    for payable in payables:
        used += payable["manual_billed_cents"]
        direct = conn.execute(
            """SELECT a.amount_including_tax_cents, a.quantity FROM purchase_invoice_allocations a
               JOIN purchase_invoices i ON i.id = a.invoice_id
               WHERE a.payable_transaction_id = ? AND i.status = 'confirmed'""", (payable["id"],),
        ).fetchall()
        used += sum(row["amount_including_tax_cents"] for row in direct)
        qty += sum((Decimal(row["quantity"]) for row in direct), Decimal(0))
    return used, qty, sum(row["amount_including_tax_cents"] for row in payables)


def order_capacity(conn, source, actual):
    locked = conn.execute(
        f"""SELECT COALESCE(SUM(MAX(0, t.amount_including_tax_cents - t.billed_cents)), 0)
            FROM supplier_account_transactions t
            WHERE t.purchase_order_item_id = ? AND t.source_type = 'stock_inbound'
              AND t.locked_at IS NOT NULL AND {effective_sql()}""", (source["id"],),
    ).fetchone()[0]
    return max(source["amount_including_tax_cents"], actual) - locked


def order_source_options(conn, store_id, supplier_id=None, order_id=None):
    sql = """SELECT p.id FROM purchase_order_items p JOIN purchase_orders o ON o.id = p.order_id
             WHERE o.store_id = ? AND o.status IN ('approved', 'partial', 'completed')
               AND p.supplier_id IS NOT NULL AND p.unit_price IS NOT NULL"""
    params = [store_id]
    for column, value in (("p.supplier_id", supplier_id), ("o.id", order_id)):
        if value is not None:
            sql += f" AND {column} = ?"
            params.append(value)
    results = []
    for item in conn.execute(sql + " ORDER BY o.order_date, o.id, p.line_no", params):
        row = load_order_source(conn, item["id"])
        used, _, actual = order_usage(conn, row["id"])
        total = max(row["amount_including_tax_cents"], actual)
        results.append({
            "id": f"order-item-{row['id']}", "purchaseOrderItemId": row["id"],
            "purchaseOrderId": row["order_id"], "supplierId": row["supplier_id"], "storeId": row["store_id"],
            "sourceType": "purchase_order", "sourceId": row["order_id"],
            "documentNo": row["order_no"], "productName": row["product_name"],
            "businessDate": row["order_date"], "payableAmount": amount(total),
            "amountIncludingTax": amount(total),
            "availableAmount": amount(max(0, order_capacity(conn, row, actual) - used)),
            "invoiceStatus": "billed" if total and used >= total else "partial" if used else "unbilled",
        })
    return results


def sync_order_invoices(conn, item_id):
    from utils.supplier_settlement import refresh_invoice
    roots = conn.execute(
        """SELECT a.* FROM purchase_invoice_order_allocations a
           JOIN purchase_invoices i ON i.id = a.invoice_id
           WHERE a.purchase_order_item_id = ? AND i.status = 'confirmed'
           ORDER BY i.invoice_date, i.id, a.id""", (item_id,),
    ).fetchall()
    payables = conn.execute(
        f"""SELECT t.* FROM supplier_account_transactions t
            WHERE t.purchase_order_item_id = ? AND t.source_type = 'stock_inbound'
              AND t.locked_at IS NULL AND {effective_sql()} ORDER BY t.business_date, t.id""", (item_id,),
    ).fetchall()
    touched = set()
    for root in roots:
        matched = conn.execute(
            "SELECT COALESCE(SUM(amount_including_tax_cents), 0) FROM purchase_invoice_order_matches WHERE order_allocation_id = ?",
            (root["id"],),
        ).fetchone()[0]
        for source in payables:
            remaining = root["amount_including_tax_cents"] - matched
            if remaining <= 0:
                break
            used = conn.execute(
                """SELECT COALESCE(SUM(value), 0) FROM (
                   SELECT a.amount_including_tax_cents value FROM purchase_invoice_allocations a
                   JOIN purchase_invoices i ON i.id = a.invoice_id
                   WHERE a.payable_transaction_id = ? AND i.status = 'confirmed'
                   UNION ALL
                   SELECT m.amount_including_tax_cents FROM purchase_invoice_order_matches m
                   JOIN purchase_invoice_order_allocations a ON a.id = m.order_allocation_id
                   JOIN purchase_invoices i ON i.id = a.invoice_id
                   WHERE m.payable_transaction_id = ? AND i.status = 'confirmed')""",
                (source["id"], source["id"]),
            ).fetchone()[0]
            value = min(remaining, source["amount_including_tax_cents"] - source["manual_billed_cents"] - used)
            if value <= 0:
                continue
            def tax_at(total):
                return int((Decimal(root["tax_amount_cents"]) * total / root["amount_including_tax_cents"])
                           .quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            tax = tax_at(matched + value) - tax_at(matched)
            qty = Decimal(root["quantity"]) * value / root["amount_including_tax_cents"]
            existing = conn.execute(
                "SELECT * FROM purchase_invoice_order_matches WHERE order_allocation_id = ? AND payable_transaction_id = ?",
                (root["id"], source["id"]),
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE purchase_invoice_order_matches SET amount_excluding_tax_cents = amount_excluding_tax_cents + ?,
                       tax_amount_cents = tax_amount_cents + ?, amount_including_tax_cents = amount_including_tax_cents + ?,
                       quantity = ? WHERE id = ?""",
                    (value - tax, tax, value, str(Decimal(existing["quantity"]) + qty), existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO purchase_invoice_order_matches
                       (order_allocation_id, payable_transaction_id, amount_excluding_tax_cents,
                        tax_amount_cents, amount_including_tax_cents, quantity) VALUES (?, ?, ?, ?, ?, ?)""",
                    (root["id"], source["id"], value - tax, tax, value, str(qty)),
                )
            matched += value
            touched.add(source["id"])
    for transaction_id in touched:
        refresh_invoice(conn, transaction_id)


def order_invoice_summary(conn, order_id, actual_billed, actual_total, actual_status):
    rows = conn.execute(
        """SELECT a.*, i.has_difference FROM purchase_invoice_order_allocations a
           JOIN purchase_invoices i ON i.id = a.invoice_id
           WHERE a.purchase_order_id = ? AND i.status = 'confirmed'""", (order_id,),
    ).fetchall()
    matched = conn.execute(
        """SELECT COALESCE(SUM(m.amount_including_tax_cents), 0)
           FROM purchase_invoice_order_matches m
           JOIN purchase_invoice_order_allocations a ON a.id = m.order_allocation_id
           JOIN purchase_invoices i ON i.id = a.invoice_id
           WHERE a.purchase_order_id = ? AND i.status = 'confirmed'""", (order_id,),
    ).fetchone()[0]
    pending = sum(row["amount_including_tax_cents"] for row in rows) - matched
    result = {"advanceBilledAmount": amount(pending)}
    if rows:
        planned = conn.execute(
            "SELECT COALESCE(SUM(amount + tax_amount), 0) FROM purchase_order_items WHERE order_id = ?", (order_id,),
        ).fetchone()[0]
        total = max(cents(planned), cents(actual_total))
        billed = cents(actual_billed) + pending
        result.update({
            "billedAmount": amount(billed), "unbilledAmount": amount(max(0, total - billed)),
            "invoiceStatus": "difference" if actual_status == "difference" or any(row["has_difference"] for row in rows)
            else "billed" if billed >= total else "partial" if billed else "unbilled",
        })
    return result


def order_has_invoices(conn, order_id, active_only=False):
    status = "AND i.status <> 'cancelled'" if active_only else ""
    return conn.execute(
        f"""SELECT 1 FROM purchase_invoice_order_allocations a JOIN purchase_invoices i ON i.id = a.invoice_id
            WHERE a.purchase_order_id = ? {status} LIMIT 1""", (order_id,),
    ).fetchone() is not None
