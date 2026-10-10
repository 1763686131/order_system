"""Shared posting rules for supplier payments, balance use and purchase invoices."""

import json
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP

from utils.auth import admin_permission_granted, current_identity
from utils.supplier_ledger import (
    FinanceError, amount, business_date, cents, check_scope, check_version,
    effective_sql, now,
)


PAYABLE_TYPES = ("INITIAL", "PURCHASE_INBOUND", "INDEPENDENT_PURCHASE_INBOUND")
INVOICE_RULE_KEY = "purchase.payment_require_invoice"


def ensure_schema(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(supplier_account_transactions)")}
    for name, definition in {
        "invoice_managed": "INTEGER NOT NULL DEFAULT 0",
        "manual_billed_cents": "INTEGER NOT NULL DEFAULT 0",
        "manual_invoice_status": "TEXT NOT NULL DEFAULT 'unbilled'",
        "manual_invoice_remark": "TEXT NOT NULL DEFAULT ''",
    }.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE supplier_account_transactions ADD COLUMN {name} {definition}")
    if "manual_billed_cents" not in columns:
        conn.execute(
            """UPDATE supplier_account_transactions SET manual_billed_cents = billed_cents,
               manual_invoice_status = invoice_status, manual_invoice_remark = invoice_remark"""
        )
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS supplier_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_no TEXT NOT NULL UNIQUE,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            business_date TEXT NOT NULL,
            payment_date TEXT NOT NULL,
            bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(id),
            account_name TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            payment_cents INTEGER NOT NULL,
            advance_cents INTEGER NOT NULL,
            unbilled_reason TEXT NOT NULL DEFAULT '',
            invoice_override INTEGER NOT NULL DEFAULT 0,
            attachments TEXT NOT NULL DEFAULT '[]',
            remark TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            audited_by TEXT,
            audited_at TEXT,
            reversed_at TEXT,
            locked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS supplier_payment_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER NOT NULL REFERENCES supplier_payments(id) ON DELETE CASCADE,
            payable_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            amount_cents INTEGER NOT NULL,
            UNIQUE(payment_id, payable_transaction_id)
        );
        CREATE TABLE IF NOT EXISTS supplier_balance_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            source_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            kind TEXT NOT NULL,
            business_date TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            unbilled_reason TEXT NOT NULL DEFAULT '',
            invoice_override INTEGER NOT NULL DEFAULT 0,
            remark TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'audited',
            version INTEGER NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL,
            audited_at TEXT NOT NULL,
            reversed_at TEXT,
            locked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS supplier_settlement_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            document_version INTEGER NOT NULL,
            balance_transaction_id INTEGER REFERENCES supplier_account_transactions(id),
            balance_kind TEXT,
            payable_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            amount_cents INTEGER NOT NULL,
            ledger_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            active INTEGER NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reversed_at TEXT,
            UNIQUE(source_type, source_id, document_version, payable_transaction_id)
        );
        CREATE INDEX IF NOT EXISTS idx_supplier_allocations_balance
            ON supplier_settlement_allocations(balance_transaction_id, balance_kind, active);
        CREATE INDEX IF NOT EXISTS idx_supplier_allocations_payable
            ON supplier_settlement_allocations(payable_transaction_id, active);
        CREATE TABLE IF NOT EXISTS bank_account_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            business_date TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            document_no TEXT NOT NULL,
            document_version INTEGER NOT NULL,
            delta_cents INTEGER NOT NULL,
            balance_after_cents INTEGER NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reversal_of_id INTEGER UNIQUE REFERENCES bank_account_transactions(id),
            UNIQUE(source_type, source_id, document_version, reversal_of_id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_bank_posting
            ON bank_account_transactions(source_type, source_id, document_version)
            WHERE reversal_of_id IS NULL;
        CREATE TABLE IF NOT EXISTS purchase_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            invoice_no TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            business_date TEXT NOT NULL,
            invoice_type TEXT NOT NULL,
            amount_excluding_tax_cents INTEGER NOT NULL,
            tax_amount_cents INTEGER NOT NULL,
            amount_including_tax_cents INTEGER NOT NULL,
            difference_reason TEXT NOT NULL DEFAULT '',
            has_difference INTEGER NOT NULL DEFAULT 0,
            attachments TEXT NOT NULL DEFAULT '[]',
            remark TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            confirmed_by TEXT,
            confirmed_at TEXT,
            reversed_at TEXT,
            locked_at TEXT,
            UNIQUE(supplier_id, invoice_no)
        );
        CREATE TABLE IF NOT EXISTS purchase_invoice_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL REFERENCES purchase_invoices(id) ON DELETE CASCADE,
            payable_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            amount_excluding_tax_cents INTEGER NOT NULL,
            tax_amount_cents INTEGER NOT NULL,
            amount_including_tax_cents INTEGER NOT NULL,
            quantity TEXT NOT NULL DEFAULT '0',
            UNIQUE(invoice_id, payable_transaction_id)
        );
        CREATE TABLE IF NOT EXISTS purchase_invoice_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL REFERENCES purchase_invoices(id),
            document_version INTEGER NOT NULL,
            action TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            allocations_json TEXT NOT NULL,
            UNIQUE(invoice_id, document_version, action)
        );
        CREATE TABLE IF NOT EXISTS supplier_finance_attachments (
            token TEXT PRIMARY KEY,
            store_id INTEGER NOT NULL REFERENCES stores(id),
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            mimetype TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_supplier_payments_period
            ON supplier_payments(store_id, business_date, status);
        CREATE INDEX IF NOT EXISTS idx_purchase_invoices_period
            ON purchase_invoices(store_id, business_date, status);
        CREATE TABLE IF NOT EXISTS purchase_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_no TEXT NOT NULL UNIQUE,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            business_date TEXT NOT NULL,
            remark TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            audited_by TEXT,
            audited_at TEXT,
            reversed_at TEXT,
            locked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS purchase_return_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            return_id INTEGER NOT NULL REFERENCES purchase_returns(id) ON DELETE CASCADE,
            line_no INTEGER NOT NULL,
            inbound_item_id INTEGER NOT NULL REFERENCES stock_inbound_items(id),
            payable_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            quantity TEXT NOT NULL,
            original_unit_price_cents INTEGER NOT NULL,
            original_cost_cents INTEGER NOT NULL,
            return_amount_cents INTEGER NOT NULL,
            applied_payable_cents INTEGER NOT NULL DEFAULT 0,
            credit_cents INTEGER NOT NULL DEFAULT 0,
            difference_reason TEXT NOT NULL DEFAULT '',
            UNIQUE(return_id, inbound_item_id)
        );
        CREATE INDEX IF NOT EXISTS idx_purchase_return_items_inbound
            ON purchase_return_items(inbound_item_id);
        CREATE TABLE IF NOT EXISTS purchase_return_stock_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            return_item_id INTEGER NOT NULL REFERENCES purchase_return_items(id),
            document_version INTEGER NOT NULL,
            movement_id INTEGER NOT NULL REFERENCES stock_movements(id),
            reversal_movement_id INTEGER REFERENCES stock_movements(id),
            UNIQUE(return_item_id, document_version)
        );
        CREATE TABLE IF NOT EXISTS supplier_refunds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_no TEXT NOT NULL UNIQUE,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            business_date TEXT NOT NULL,
            refund_date TEXT NOT NULL,
            bank_account_id INTEGER NOT NULL REFERENCES bank_accounts(id),
            account_name TEXT NOT NULL,
            refund_cents INTEGER NOT NULL,
            credits_json TEXT NOT NULL DEFAULT '[]',
            remark TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            audited_by TEXT,
            audited_at TEXT,
            reversed_at TEXT,
            locked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS supplier_refund_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refund_id INTEGER NOT NULL REFERENCES supplier_refunds(id) ON DELETE CASCADE,
            credit_transaction_id INTEGER NOT NULL REFERENCES supplier_account_transactions(id),
            amount_cents INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            UNIQUE(refund_id, credit_transaction_id)
        );
        CREATE INDEX IF NOT EXISTS idx_supplier_refund_allocations_credit
            ON supplier_refund_allocations(credit_transaction_id, active);
        CREATE TABLE IF NOT EXISTS supplier_reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_no TEXT NOT NULL UNIQUE,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            store_id INTEGER NOT NULL REFERENCES stores(id),
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            snapshot_json TEXT NOT NULL,
            supplier_balances_json TEXT,
            difference_reason TEXT NOT NULL DEFAULT '',
            confirmation_note TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            confirmed_by TEXT,
            confirmed_at TEXT,
            locked_at TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_reconciliation_active_period
            ON supplier_reconciliations(supplier_id, store_id, period_start, period_end)
            WHERE status IN ('draft', 'confirmed');
        CREATE INDEX IF NOT EXISTS idx_supplier_reconciliation_period
            ON supplier_reconciliations(supplier_id, store_id, period_start, period_end, status);
    """)
    refund_columns = {row["name"] for row in conn.execute("PRAGMA table_info(supplier_refunds)")}
    if "credits_json" not in refund_columns:
        conn.execute("ALTER TABLE supplier_refunds ADD COLUMN credits_json TEXT NOT NULL DEFAULT '[]'")
    from utils.purchase_invoice_orders import ensure_schema as ensure_order_invoice_schema
    ensure_order_invoice_schema(conn)
    balance_columns = {row["name"] for row in conn.execute("PRAGMA table_info(supplier_balance_allocations)")}
    for name, definition in {
        "unbilled_reason": "TEXT NOT NULL DEFAULT ''",
        "invoice_override": "INTEGER NOT NULL DEFAULT 0",
    }.items():
        if name not in balance_columns:
            conn.execute(f"ALTER TABLE supplier_balance_allocations ADD COLUMN {name} {definition}")
    conn.execute(
        "INSERT OR IGNORE INTO system_settings (setting_key, setting_value, updated_at) "
        "VALUES (?, 'false', ?)",
        (INVOICE_RULE_KEY, now()),
    )
    from utils.supplier_periods import ensure_schema as ensure_period_schema
    ensure_period_schema(conn)


def positive_id(value):
    if isinstance(value, bool) or not str(value).isdigit() or int(value) <= 0:
        raise FinanceError("ID 必须为正整数")
    return int(value)


def required_version(data, row):
    if data.get("version") is None:
        raise FinanceError("请携带当前单据版本")
    check_version(data, row)


def text(value, limit=500):
    return str(value or "").strip()[:limit]


def supplier_store(conn, supplier_id, store_id):
    supplier_id, store_id = positive_id(supplier_id), positive_id(store_id)
    check_scope(store_id)
    supplier = conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    store = conn.execute("SELECT * FROM stores WHERE id = ?", (store_id,)).fetchone()
    if not supplier or not store:
        raise FinanceError("供应商或门店不存在", 404)
    if supplier["status"] != "active" or store["status"] != "active":
        raise FinanceError("供应商或门店已停用")
    if supplier["store_id"] not in (None, store_id):
        raise FinanceError("供应商不属于所选门店")
    return supplier_id, store_id


def load_payable(conn, transaction_id, supplier_id, store_id, invoice=False):
    row = conn.execute(
        f"SELECT * FROM supplier_account_transactions t WHERE id = ? AND {effective_sql()}",
        (positive_id(transaction_id),),
    ).fetchone()
    if not row:
        raise FinanceError("应付来源不存在或已冲销", 409)
    check_scope(row["store_id"])
    if row["supplier_id"] != supplier_id or row["store_id"] != store_id:
        raise FinanceError("应付来源的供应商或门店不一致")
    if row["transaction_type"] not in PAYABLE_TYPES or (invoice and row["source_type"] != "stock_inbound"):
        raise FinanceError("该流水不是有效采购应付来源")
    if row["locked_at"]:
        raise FinanceError("应付来源已被正式对账锁定", 409)
    return row


def allocation_values(conn, data, supplier_id, store_id):
    entries = data.get("allocations", [])
    if not isinstance(entries, list) or len(entries) > 500:
        raise FinanceError("核销明细必须是最多 500 项的数组")
    result, seen = [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise FinanceError("核销明细格式错误")
        row = load_payable(conn, entry.get("payableTransactionId"), supplier_id, store_id)
        if row["id"] in seen:
            raise FinanceError("同一应付不能重复分配")
        seen.add(row["id"])
        value = cents(entry.get("amount"))
        if value <= 0:
            raise FinanceError("核销金额必须大于零")
        payable_available = payable_available_cents(
            conn, row, data.get("businessDate") or now()[:10]
        )
        if value > payable_available:
            raise FinanceError("核销金额超过最新未核销余额，请刷新后重试", 409)
        result.append((row, value))
    return result


def require_invoice(conn):
    row = conn.execute(
        "SELECT setting_value FROM system_settings WHERE setting_key = ?", (INVOICE_RULE_KEY,)
    ).fetchone()
    return bool(row and row["setting_value"] == "true")


def invoice_payment_check(conn, entries, data):
    missing = any(row["invoice_status"] not in ("billed", "not_required") for row, _ in entries)
    if not missing:
        return
    if not text(data.get("unbilledReason")):
        raise FinanceError("未开票或开票差异付款必须填写原因")
    if require_invoice(conn) and not (
        data.get("invoiceOverride") is True
        and admin_permission_granted("admin.finance.supplier_payment.invoice_override")
    ):
        raise FinanceError("已启用见票付款，请先完成开票或申请财务豁免", 409)


def attachments_value(conn, value, store_id):
    if not isinstance(value, list) or len(value) > 10:
        raise FinanceError("附件必须是最多 10 项的数组")
    result = []
    for item in value:
        if not isinstance(item, dict):
            raise FinanceError("附件格式错误")
        url = text(item.get("url"), 500)
        prefix = "/api/supplier-finance/attachments/"
        token = url.removeprefix(prefix)
        if not url.startswith(prefix) or len(token) != 32 or any(char not in "0123456789abcdef" for char in token):
            raise FinanceError("只能使用已上传的采购财务附件")
        uploaded = conn.execute("SELECT * FROM supplier_finance_attachments WHERE token = ?", (token,)).fetchone()
        if not uploaded or uploaded["store_id"] != store_id:
            raise FinanceError("附件不存在或不属于当前门店")
        result.append({"name": uploaded["original_name"], "url": url})
    return json.dumps(result, ensure_ascii=False)


def add_ledger(conn, document, source_type, source_id, source_item_id, kind,
               payable=0, prepayment=0, credit=0, target=None):
    target = target or {}
    cursor = conn.execute(
        """INSERT INTO supplier_account_transactions (
            supplier_id, store_id, business_date, audited_at, created_by, transaction_type,
            source_type, source_id, source_item_id, source_document_no, document_version,
            purchase_order_id, purchase_order_item_id, product_name, payable_delta_cents,
            prepayment_delta_cents, credit_delta_cents, invoice_status, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_required', ?)""",
        (document["supplier_id"], document["store_id"], document["business_date"], now(),
         current_identity(), kind, source_type, source_id, source_item_id, document["document_no"],
         document["version"], target.get("purchase_order_id"), target.get("purchase_order_item_id"),
         target.get("product_name", ""), payable, prepayment, credit, document["remark"]),
    )
    return cursor.lastrowid


def apply_allocations(conn, document, source_type, source_id, entries,
                      balance_source=None, balance_kind=None):
    for row, value in entries:
        kind = "PAYMENT" if source_type in ("supplier_payment", "purchase_order_payment", "purchase_inbound_payment") else (
            "PREPAYMENT_ALLOCATION" if balance_kind == "prepayment" else "CREDIT_ALLOCATION"
        )
        ledger_id = add_ledger(
            conn, document, source_type, source_id, row["id"], kind, payable=-value,
            prepayment=-value if balance_kind == "prepayment" else 0,
            credit=-value if balance_kind == "credit" else 0, target=dict(row),
        )
        conn.execute(
            """INSERT INTO supplier_settlement_allocations (
                source_type, source_id, document_version, balance_transaction_id, balance_kind,
                payable_transaction_id, amount_cents, ledger_transaction_id, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source_type, source_id, document["version"], balance_source, balance_kind,
             row["id"], value, ledger_id, current_identity(), now()),
        )
        conn.execute(
            "UPDATE supplier_account_transactions SET allocated_cents = allocated_cents + ?, "
            "version = version + 1 WHERE id = ?", (value, row["id"]),
        )


def balance_available(conn, row, kind):
    used = conn.execute(
        """SELECT COALESCE(SUM(amount_cents), 0) value FROM supplier_settlement_allocations
           WHERE balance_transaction_id = ? AND balance_kind = ? AND active = 1""",
        (row["id"], kind),
    ).fetchone()["value"]
    if kind == "credit":
        refunds = conn.execute(
            """SELECT COALESCE(SUM(amount_cents), 0) value FROM supplier_refund_allocations
               WHERE credit_transaction_id = ? AND active = 1""", (row["id"],),
        ).fetchone()["value"]
        used += refunds
    return row[f"{kind}_delta_cents"] - used


def payable_available_cents(conn, row, as_of=None):
    from utils.supplier_ledger import returned_payable_cents
    return max(
        0,
        row["payable_delta_cents"] - row["allocated_cents"]
        - returned_payable_cents(conn, row["id"], as_of),
    )


def reverse_ledger(conn, source_type, source_id):
    rows = conn.execute(
        f"SELECT * FROM supplier_account_transactions t WHERE source_type = ? AND source_id = ? "
        f"AND {effective_sql()}", (source_type, source_id),
    ).fetchall()
    if any(row["locked_at"] for row in rows):
        raise FinanceError("账务已被正式对账锁定", 409)
    for row in rows:
        if row["prepayment_delta_cents"] > 0 and balance_available(conn, row, "prepayment") != row["prepayment_delta_cents"]:
            raise FinanceError("本单预付款已被后续核销，请先撤销核销", 409)
        if row["credit_delta_cents"] > 0 and balance_available(conn, row, "credit") != row["credit_delta_cents"]:
            raise FinanceError("本单贷项已被后续核销或退款，请先撤销后续业务", 409)
        conn.execute(
            """INSERT INTO supplier_account_transactions (
                supplier_id, store_id, business_date, audited_at, created_by, transaction_type,
                source_type, source_id, source_item_id, source_document_no, document_version,
                purchase_order_id, purchase_order_item_id, product_name, payable_delta_cents,
                prepayment_delta_cents, credit_delta_cents, reversal_of_id, invoice_status, remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_required', ?)""",
            (row["supplier_id"], row["store_id"], max(now()[:10], row["business_date"]), now(), current_identity(),
             row["transaction_type"] + "_REVERSAL", source_type, source_id, row["source_item_id"],
             row["source_document_no"], row["document_version"], row["purchase_order_id"],
             row["purchase_order_item_id"], row["product_name"], -row["payable_delta_cents"],
             -row["prepayment_delta_cents"], -row["credit_delta_cents"], row["id"], "反审核冲销"),
        )
    allocations = conn.execute(
        "SELECT * FROM supplier_settlement_allocations WHERE source_type = ? AND source_id = ? AND active = 1",
        (source_type, source_id),
    ).fetchall()
    for entry in allocations:
        row = conn.execute(
            "SELECT * FROM supplier_account_transactions WHERE id = ?",
            (entry["payable_transaction_id"],),
        ).fetchone()
        if row["locked_at"] or row["allocated_cents"] < entry["amount_cents"]:
            raise FinanceError("核销来源已锁定或金额不一致，不能反审核", 409)
        conn.execute(
            "UPDATE supplier_account_transactions SET allocated_cents = allocated_cents - ?, "
            "version = version + 1 WHERE id = ?",
            (entry["amount_cents"], row["id"]),
        )
    conn.execute(
        "UPDATE supplier_settlement_allocations SET active = 0, reversed_at = ? "
        "WHERE source_type = ? AND source_id = ? AND active = 1",
        (now(), source_type, source_id),
    )
    if source_type == "supplier_refund":
        conn.execute(
            "UPDATE supplier_refund_allocations SET active = 0 WHERE refund_id = ? AND active = 1",
            (source_id,),
        )


def post_bank(conn, payment, reverse=False):
    account = conn.execute(
        "SELECT * FROM bank_accounts WHERE id = ?", (payment["bank_account_id"],)
    ).fetchone()
    if not account or account["store_id"] != payment["store_id"]:
        raise FinanceError("付款银行账户不存在或门店不一致", 409)
    delta = payment["payment_cents"] if reverse else -payment["payment_cents"]
    current = cents(account["balance"], nonnegative=False)
    if current + delta < 0:
        raise FinanceError("银行账户余额不足", 409)
    original = None
    if reverse:
        original = conn.execute(
            """SELECT t.* FROM bank_account_transactions t WHERE source_type = 'supplier_payment'
               AND source_id = ? AND reversal_of_id IS NULL AND NOT EXISTS
               (SELECT 1 FROM bank_account_transactions r WHERE r.reversal_of_id = t.id)""",
            (payment["id"],),
        ).fetchone()
        if not original:
            raise FinanceError("找不到有效银行付款流水", 409)
    else:
        active = conn.execute(
            """SELECT 1 FROM bank_account_transactions t WHERE source_type = 'supplier_payment'
               AND source_id = ? AND reversal_of_id IS NULL AND NOT EXISTS
               (SELECT 1 FROM bank_account_transactions r WHERE r.reversal_of_id = t.id)""",
            (payment["id"],),
        ).fetchone()
        if active:
            raise FinanceError("该付款单已有有效银行流水", 409)
    conn.execute(
        """INSERT INTO bank_account_transactions (
            bank_account_id, store_id, business_date, source_type, source_id, document_no,
            document_version, delta_cents, balance_after_cents, created_by, created_at, reversal_of_id
        ) VALUES (?, ?, ?, 'supplier_payment', ?, ?, ?, ?, ?, ?, ?, ?)""",
        (account["id"], payment["store_id"], max(now()[:10], original["business_date"]) if reverse else payment["business_date"],
         payment["id"], payment["document_no"], original["document_version"] if original else payment["version"],
         delta, current + delta, current_identity(), now(), original["id"] if original else None),
    )
    conn.execute(
        "UPDATE bank_accounts SET balance = ?, updated_at = ? WHERE id = ?",
        (amount(current + delta), now(), account["id"]),
    )


def quantity(value):
    try:
        result = Decimal(str(value or 0))
        if not result.is_finite() or result < 0 or result > Decimal("999999999999"):
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise FinanceError("开票数量必须为非负有限数字")


def refresh_invoice(conn, transaction_id):
    row = conn.execute(
        "SELECT * FROM supplier_account_transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    entries = conn.execute(
        """SELECT a.*, i.has_difference, i.invoice_no, i.difference_reason FROM purchase_invoice_allocations a
           JOIN purchase_invoices i ON i.id = a.invoice_id
           WHERE a.payable_transaction_id = ? AND i.status = 'confirmed'
           UNION ALL
           SELECT m.id, a.invoice_id, m.payable_transaction_id, m.amount_excluding_tax_cents,
                  m.tax_amount_cents, m.amount_including_tax_cents, m.quantity,
                  i.has_difference, i.invoice_no, i.difference_reason
           FROM purchase_invoice_order_matches m
           JOIN purchase_invoice_order_allocations a ON a.id = m.order_allocation_id
           JOIN purchase_invoices i ON i.id = a.invoice_id
           WHERE m.payable_transaction_id = ? AND i.status = 'confirmed'""", (transaction_id, transaction_id),
    ).fetchall()
    billed = row["manual_billed_cents"] + sum(entry["amount_including_tax_cents"] for entry in entries)
    status = (
        row["manual_invoice_status"] if not entries else
        "difference" if row["manual_invoice_status"] == "difference" or any(entry["has_difference"] for entry in entries) else
        "billed" if billed == row["amount_including_tax_cents"] else
        "partial" if billed else "unbilled"
    )
    conn.execute(
        """UPDATE supplier_account_transactions SET billed_cents = ?, invoice_status = ?, invoice_remark = ?,
           invoice_managed = ?,
           invoice_updated_by = ?, invoice_updated_at = ?, version = version + 1 WHERE id = ?""",
        (billed, status, text("; ".join(
            [row["manual_invoice_remark"]] + [
                entry["invoice_no"] + (": " + entry["difference_reason"] if entry["has_difference"] else "")
                for entry in entries
            ])), int(bool(entries)), current_identity(), now(), transaction_id),
    )


def proportional_tax(row, inclusive):
    if not row["amount_including_tax_cents"]:
        return 0
    return int((Decimal(row["tax_amount_cents"]) * inclusive / row["amount_including_tax_cents"])
               .quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def invoice_allocation_suggestion(row, available, source_qty, used=0, used_tax=None, used_qty=None):
    tax = proportional_tax(row, available)
    if used_tax is not None and used + available == row["amount_including_tax_cents"]:
        remaining_tax = row["tax_amount_cents"] - used_tax
        if 0 <= remaining_tax <= available and abs(remaining_tax - tax) <= 1:
            tax = remaining_tax
    qty = quantity(source_qty)
    if used:
        qty = max(Decimal(0), qty - used_qty) if used_qty is not None else Decimal(0)
    remaining = max(0, row["amount_including_tax_cents"] - used)
    if remaining and available < remaining:
        qty *= Decimal(available) / remaining
    qty = qty.quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
    return {
        "amountExcludingTax": amount(available - tax), "taxAmount": amount(tax),
        "amountIncludingTax": amount(available), "quantity": format(qty.normalize(), "f"),
    }
