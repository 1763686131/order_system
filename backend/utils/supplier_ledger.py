"""Supplier accounting uses integer cents, independent of purchase commitments."""

import hashlib
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import request

from utils.auth import current_identity, get_current_user
from utils.access_scope import accessible_scope_ids, can_access_scope


class FinanceError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def business_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        raise FinanceError("业务日期必须为 YYYY-MM-DD")


def cents(value, nonnegative=True):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise FinanceError("金额格式不正确")
    if not number.is_finite() or (nonnegative and number < 0):
        raise FinanceError("金额必须为非负有限数字")
    if abs(number) > Decimal("99999999999.99"):
        raise FinanceError("金额超出允许范围")
    return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def amount(value):
    return int(value or 0) / 100


def ensure_schema(conn):
    for table, columns in {
        "purchase_orders": {"version": "INTEGER NOT NULL DEFAULT 1"},
        "stock_inbounds": {
            "settlement_type": "TEXT NOT NULL DEFAULT 'none'",
            "settlement_remark": "TEXT NOT NULL DEFAULT ''",
            "version": "INTEGER NOT NULL DEFAULT 1",
            "audited_by": "TEXT NOT NULL DEFAULT ''",
            "reversed_at": "TEXT",
        },
        "stock_inbound_items": {
            "supplier_id": "INTEGER",
            "supplier_assignment_status": "TEXT NOT NULL DEFAULT 'not_required'",
            "supplier_assigned_by": "TEXT",
            "supplier_assigned_at": "TEXT",
            "payable_transaction_id": "INTEGER",
        },
    }.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column, definition in columns.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS supplier_account_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            business_date TEXT NOT NULL,
            audited_at TEXT NOT NULL,
            created_by TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            source_item_id INTEGER NOT NULL DEFAULT 0,
            source_document_no TEXT NOT NULL,
            purchase_order_id INTEGER,
            purchase_order_item_id INTEGER,
            product_name TEXT NOT NULL DEFAULT '',
            amount_excluding_tax_cents INTEGER NOT NULL DEFAULT 0,
            tax_amount_cents INTEGER NOT NULL DEFAULT 0,
            amount_including_tax_cents INTEGER NOT NULL DEFAULT 0,
            payable_delta_cents INTEGER NOT NULL DEFAULT 0,
            prepayment_delta_cents INTEGER NOT NULL DEFAULT 0,
            credit_delta_cents INTEGER NOT NULL DEFAULT 0,
            allocated_cents INTEGER NOT NULL DEFAULT 0,
            invoice_status TEXT NOT NULL DEFAULT 'unbilled',
            billed_cents INTEGER NOT NULL DEFAULT 0,
            invoice_remark TEXT NOT NULL DEFAULT '',
            invoice_updated_by TEXT,
            invoice_updated_at TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            document_version INTEGER NOT NULL DEFAULT 1,
            reversal_of_id INTEGER UNIQUE REFERENCES supplier_account_transactions(id),
            locked_at TEXT,
            remark TEXT NOT NULL DEFAULT '',
            UNIQUE(source_type, source_id, source_item_id, transaction_type, document_version)
        );
        CREATE INDEX IF NOT EXISTS idx_supplier_ledger_period
            ON supplier_account_transactions(supplier_id, store_id, business_date, id);
        CREATE INDEX IF NOT EXISTS idx_supplier_ledger_purchase
            ON supplier_account_transactions(purchase_order_id, purchase_order_item_id);
        CREATE TABLE IF NOT EXISTS supplier_finance_operations (
            operation_key TEXT PRIMARY KEY,
            operation TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS purchase_expense_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_order_id INTEGER NOT NULL REFERENCES purchase_orders(id),
            purchase_order_item_id INTEGER NOT NULL,
            inbound_item_id INTEGER,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            expense_type TEXT NOT NULL,
            amount_excluding_tax_cents INTEGER NOT NULL,
            tax_amount_cents INTEGER NOT NULL,
            amount_including_tax_cents INTEGER NOT NULL,
            include_in_payable INTEGER NOT NULL DEFAULT 1,
            include_in_inventory_cost INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'draft',
            confirmed_by TEXT,
            confirmed_at TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            remark TEXT NOT NULL DEFAULT '',
            version INTEGER NOT NULL DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_purchase_expenses_inbound
            ON purchase_expense_lines(inbound_item_id, status);
    """)
    from utils.supplier_settlement import ensure_schema as ensure_settlement_schema
    ensure_settlement_schema(conn)
    audited_operations = conn.execute(
        """SELECT operation, created_at FROM supplier_finance_operations
           WHERE operation LIKE 'received-purchase:%:audit'"""
    ).fetchall()
    for operation in audited_operations:
        parts = operation["operation"].split(":")
        if len(parts) != 3 or parts[0] != "received-purchase" or parts[2] != "audit":
            continue
        try:
            inbound_id = int(parts[1])
        except ValueError:
            continue
        conn.execute(
            """UPDATE stock_inbounds SET procurement_audited_at = ?
               WHERE id = ? AND procurement_audited_at IS NULL""",
            (operation["created_at"], inbound_id),
        )
    conn.commit()


def check_scope(store_id, warehouse_ids=()):
    user = get_current_user()
    if not can_access_scope(user, "store", store_id):
        raise FinanceError("无权访问该门店数据", 403)
    if any(not can_access_scope(user, "warehouse", value) for value in warehouse_ids):
        raise FinanceError("无权访问该仓库数据", 403)


def scope_sql(alias="t", store_id=None):
    clauses, params = [], []
    allowed = accessible_scope_ids(get_current_user(), "store")
    if store_id is not None:
        check_scope(store_id)
        clauses.append(f"{alias}.store_id = ?")
        params.append(store_id)
    if allowed is not None:
        if not allowed:
            clauses.append("0 = 1")
        else:
            clauses.append(f"{alias}.store_id IN ({','.join('?' for _ in allowed)})")
            params.extend(sorted(allowed))
    return (" AND " + " AND ".join(clauses) if clauses else ""), params


def check_version(data, row):
    if data.get("version") is not None:
        if isinstance(data["version"], bool) or str(data["version"]) != str(row["version"]):
            raise FinanceError("单据已被修改，请刷新后重试", 409)


def idempotent_result(conn, operation, data):
    key = request.headers.get("Idempotency-Key") or data.get("idempotencyKey")
    if not key:
        return None, None
    if not isinstance(key, str) or not key.strip() or len(key) > 160:
        raise FinanceError("幂等键格式不正确")
    payload = {k: v for k, v in data.items() if k != "idempotencyKey"}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    stored = conn.execute(
        "SELECT * FROM supplier_finance_operations WHERE operation_key = ?", (key,)
    ).fetchone()
    if stored:
        if stored["operation"] != operation or stored["payload_hash"] != digest:
            raise FinanceError("幂等键已用于其他请求", 409)
        return json.loads(stored["result_json"]), None
    return None, (key, operation, digest)


def save_operation(conn, token, result):
    if token:
        conn.execute(
            "INSERT INTO supplier_finance_operations VALUES (?, ?, ?, ?, ?)",
            (*token, json.dumps(result, ensure_ascii=False), now()),
        )
    return result


def effective_sql(alias="t"):
    return (
        f"{alias}.reversal_of_id IS NULL AND NOT EXISTS "
        f"(SELECT 1 FROM supplier_account_transactions r WHERE r.reversal_of_id = {alias}.id)"
    )


def balance(conn, supplier_id, store_id=None, as_of=None):
    scoped, params = scope_sql(store_id=store_id)
    date_clause = " AND t.business_date <= ?" if as_of else ""
    if as_of:
        params.append(business_date(as_of))
    row = conn.execute(
        f"""SELECT COALESCE(SUM(payable_delta_cents), 0) payable,
                   COALESCE(SUM(prepayment_delta_cents), 0) prepayment,
                   COALESCE(SUM(credit_delta_cents), 0) credit
            FROM supplier_account_transactions t WHERE supplier_id = ? {scoped} {date_clause}""",
        (supplier_id, *params),
    ).fetchone()
    return {
        "payableBalance": amount(row["payable"]),
        "prepaymentBalance": amount(row["prepayment"]),
        "creditBalance": amount(row["credit"]),
        "netSettlement": amount(row["payable"] - row["prepayment"] - row["credit"]),
        "hasAvailableBalance": row["prepayment"] > 0 or row["credit"] > 0,
    }


def returned_payable_cents(conn, payable_transaction_id, as_of=None):
    date_clause = " AND business_date <= ?" if as_of else ""
    params = (payable_transaction_id, business_date(as_of)) if as_of else (payable_transaction_id,)
    row = conn.execute(
        f"""SELECT COALESCE(SUM(payable_delta_cents), 0) value
            FROM supplier_account_transactions
            WHERE source_type = 'purchase_return' AND source_item_id = ? {date_clause}""",
        params,
    ).fetchone()
    return max(0, -row["value"])


def source_summary(conn, field, value):
    if field not in ("purchase_order_id", "source_id"):
        raise ValueError("Invalid supplier source")
    scoped, params = scope_sql()
    rows = conn.execute(
        f"SELECT * FROM supplier_account_transactions t WHERE t.{field} = ? "
        f"AND t.source_type = 'stock_inbound' AND {effective_sql()} {scoped}", (value, *params),
    ).fetchall()
    confirmed = sum(row["amount_including_tax_cents"] for row in rows)
    allocated = sum(row["allocated_cents"] for row in rows)
    billed = sum(row["billed_cents"] for row in rows)
    returned = sum(returned_payable_cents(conn, row["id"]) for row in rows)
    invoice_status = (
        "not_required" if not rows or all(row["invoice_status"] == "not_required" for row in rows) else
        "difference" if any(row["invoice_status"] == "difference" for row in rows) else
        "billed" if all(row["invoice_status"] in ("billed", "not_required") for row in rows) else
        "partial" if billed > 0 else "unbilled"
    )
    return {
        "confirmedPayable": amount(max(0, confirmed - returned)), "allocatedAmount": amount(allocated),
        "returnedAmount": amount(returned), "unpaidAmount": amount(max(0, confirmed - allocated - returned)),
        "billedAmount": amount(billed), "unbilledAmount": amount(sum(
            max(0, row["amount_including_tax_cents"] - row["billed_cents"])
            for row in rows if row["invoice_status"] != "not_required"
        )),
        "invoiceStatus": invoice_status,
        "paymentStatus": "not_confirmed" if not rows else
                         "paid" if confirmed <= allocated else "partial" if allocated else "unpaid",
        "payableCount": len(rows),
    }


def post_inbound_payables(conn, document, items):
    linked = bool(document["purchase_order_id"])
    if not linked and document["settlement_type"] != "pending_supplier":
        return
    order = conn.execute(
        "SELECT * FROM purchase_orders WHERE id = ?", (document["purchase_order_id"],)
    ).fetchone() if linked else None
    invoice_status = "unbilled" if not order or order["invoice_required"] else "not_required"
    for item in items:
        supplier_id = item.get("supplier_id")
        if not supplier_id:
            raise FinanceError("请先为每条入库明细确认供应商")
        if item["unit_price"] is None:
            raise FinanceError("确认应付前必须填写入库单价")
        supplier = conn.execute(
            "SELECT store_id, status FROM suppliers WHERE id = ?", (supplier_id,)
        ).fetchone()
        if not supplier or supplier["status"] != "active" or supplier["store_id"] not in (None, document["store_id"]):
            raise FinanceError("供应商不存在、已停用或不属于该门店")
        from utils.supplier_periods import ensure_period_open
        ensure_period_open(conn, supplier_id, document["store_id"], document["document_date"])
        expenses = conn.execute(
            "SELECT * FROM purchase_expense_lines WHERE inbound_item_id = ?", (item["id"],)
        ).fetchall()
        if any(line["status"] != "confirmed" for line in expenses):
            raise FinanceError("该批次仍有未确认的采购费用，请先完成费用归属")
        base = cents(Decimal(str(item["received_qty"])) * Decimal(str(item["unit_price"])))
        tax = cents(item["tax_amount"])
        base += sum(line["amount_excluding_tax_cents"] for line in expenses if line["include_in_payable"])
        tax += sum(line["tax_amount_cents"] for line in expenses if line["include_in_payable"])
        cursor = conn.execute(
            """INSERT INTO supplier_account_transactions (
                supplier_id, store_id, business_date, audited_at, created_by, transaction_type,
                source_type, source_id, source_item_id, source_document_no,
                purchase_order_id, purchase_order_item_id, product_name,
                amount_excluding_tax_cents, tax_amount_cents, amount_including_tax_cents,
                payable_delta_cents, document_version, invoice_status, manual_invoice_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'stock_inbound', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (supplier_id, document["store_id"], business_date(document["document_date"]), now(),
             current_identity(), "PURCHASE_INBOUND" if linked else "INDEPENDENT_PURCHASE_INBOUND",
             document["id"], item["id"], document["document_no"], document["purchase_order_id"],
             item.get("purchase_order_item_id"), item["product_name"], base, tax, base + tax,
             base + tax, document["version"], invoice_status, invoice_status),
        )
        conn.execute(
            "UPDATE stock_inbound_items SET payable_transaction_id = ? WHERE id = ?",
            (cursor.lastrowid, item["id"]),
        )
    if order:
        _allocate_order_payment(conn, order)


def _allocate_order_payment(conn, order):
    from utils.supplier_settlement import apply_allocations, payable_available_cents
    from utils.supplier_periods import ensure_period_open

    allocated = conn.execute(
        """SELECT COALESCE(SUM(amount_cents), 0) value FROM supplier_settlement_allocations
           WHERE source_type = 'purchase_order_payment' AND source_id = ? AND active = 1""",
        (order["id"],),
    ).fetchone()["value"]
    remaining = cents(order["current_payment"]) - allocated
    if remaining <= 0:
        return
    rows = conn.execute(
        f"""SELECT * FROM supplier_account_transactions t
            WHERE purchase_order_id = ? AND source_type = 'stock_inbound' AND {effective_sql()}
            ORDER BY business_date, source_id, source_item_id""", (order["id"],),
    ).fetchall()
    # Attribute the entry payment as batches confirm their suppliers and payables.
    for row in rows:
        value = min(remaining, payable_available_cents(conn, row))
        if value <= 0:
            continue
        date = max(row["business_date"], order["order_date"])
        ensure_period_open(conn, row["supplier_id"], row["store_id"], date)
        payment = {
            "supplier_id": row["supplier_id"], "store_id": row["store_id"],
            "business_date": date, "document_no": order["order_no"],
            "version": order["version"], "remark": "采购订单已付金额核销",
        }
        apply_allocations(conn, payment, "purchase_order_payment", order["id"], [(row, value)])
        remaining -= value
        if remaining <= 0:
            break


def _reverse_order_payment_allocations(conn, row):
    entries = conn.execute(
        """SELECT a.id allocation_id, a.amount_cents, a.ledger_transaction_id, t.*
           FROM supplier_settlement_allocations a
           JOIN supplier_account_transactions t ON t.id = a.ledger_transaction_id
           WHERE a.payable_transaction_id = ? AND a.source_type = 'purchase_order_payment'
             AND a.active = 1""", (row["id"],),
    ).fetchall()
    if sum(entry["amount_cents"] for entry in entries) != row["allocated_cents"]:
        raise FinanceError("应付已被后续付款核销，请先解除后续业务", 409)
    if any(entry["locked_at"] for entry in entries):
        raise FinanceError("采购订单付款核销已被对账锁定，不能反审核入库", 409)
    for entry in entries:
        conn.execute(
            """INSERT INTO supplier_account_transactions (
                supplier_id, store_id, business_date, audited_at, created_by, transaction_type,
                source_type, source_id, source_item_id, source_document_no, document_version,
                purchase_order_id, purchase_order_item_id, product_name, payable_delta_cents,
                reversal_of_id, invoice_status, remark
            ) VALUES (?, ?, ?, ?, ?, 'PAYMENT_REVERSAL', 'purchase_order_payment', ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      'not_required', '入库反审核退回采购订单已付金额核销')""",
            (entry["supplier_id"], entry["store_id"], max(now()[:10], entry["business_date"]),
             now(), current_identity(), entry["source_id"], row["id"], entry["source_document_no"],
             entry["document_version"], entry["purchase_order_id"], entry["purchase_order_item_id"],
             entry["product_name"], -entry["payable_delta_cents"], entry["ledger_transaction_id"]),
        )
        conn.execute(
            "UPDATE supplier_settlement_allocations SET active = 0, reversed_at = ? WHERE id = ?",
            (now(), entry["allocation_id"]),
        )
    if entries:
        conn.execute(
            "UPDATE supplier_account_transactions SET allocated_cents = 0, version = version + 1 WHERE id = ?",
            (row["id"],),
        )


def reverse_inbound_payables(conn, document):
    rows = conn.execute(
        f"SELECT * FROM supplier_account_transactions t WHERE source_type = 'stock_inbound' "
        f"AND source_id = ? AND {effective_sql()}", (document["id"],),
    ).fetchall()
    if any(row["locked_at"] or row["billed_cents"] for row in rows):
        raise FinanceError("应付已被开票或对账引用，请先解除后续业务", 409)
    returned = conn.execute(
        """SELECT 1 FROM purchase_return_items i
           JOIN purchase_returns r ON r.id = i.return_id
           JOIN stock_inbound_items inbound ON inbound.id = i.inbound_item_id
           WHERE inbound.inbound_id = ? AND r.status = 'audited' LIMIT 1""",
        (document["id"],),
    ).fetchone()
    if returned:
        raise FinanceError("该入库批次已有已审核采购退货，不能反审核", 409)
    from utils.supplier_periods import ensure_period_open
    for row in rows:
        ensure_period_open(conn, row["supplier_id"], row["store_id"], row["business_date"])
        _reverse_order_payment_allocations(conn, row)
        conn.execute(
            """INSERT INTO supplier_account_transactions (
                supplier_id, store_id, business_date, audited_at, created_by, transaction_type,
                source_type, source_id, source_item_id, source_document_no, purchase_order_id,
                purchase_order_item_id, product_name, amount_excluding_tax_cents, tax_amount_cents,
                amount_including_tax_cents, payable_delta_cents, document_version, reversal_of_id,
                invoice_status, remark
            ) VALUES (?, ?, ?, ?, ?, ?, 'stock_inbound', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_required', ?)""",
            (row["supplier_id"], row["store_id"], datetime.now().strftime("%Y-%m-%d"), now(),
             current_identity(), row["transaction_type"] + "_REVERSAL", row["source_id"],
             row["source_item_id"], row["source_document_no"], row["purchase_order_id"],
             row["purchase_order_item_id"], row["product_name"], -row["amount_excluding_tax_cents"],
             -row["tax_amount_cents"], -row["amount_including_tax_cents"],
             -row["payable_delta_cents"], row["document_version"], row["id"], "入库反审核/删除冲销"),
        )
    conn.execute(
        "UPDATE stock_inbound_items SET payable_transaction_id = NULL WHERE inbound_id = ?",
        (document["id"],),
    )
