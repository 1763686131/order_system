"""Supplier reconciliation snapshots and posting-period guards."""

from utils.supplier_ledger import FinanceError, business_date, now


def ensure_schema(conn):
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_supplier_refund_period
           ON supplier_refunds(supplier_id, store_id, business_date, status)"""
    )


def ensure_period_open(conn, supplier_id, store_id, value):
    date = business_date(value)
    row = conn.execute(
        """SELECT document_no FROM supplier_reconciliations
           WHERE supplier_id = ? AND store_id = ? AND status = 'confirmed'
             AND period_start <= ? AND period_end >= ?
           LIMIT 1""",
        (supplier_id, store_id, date, date),
    ).fetchone()
    if row:
        raise FinanceError(
            f"业务日期位于已确认对账期间（{row['document_no']}），不能新增或修改账务",
            409,
        )


def lock_period(conn, supplier_id, store_id, period_end, reconciliation_id):
    stamp = now()
    conn.execute(
        """UPDATE supplier_account_transactions SET locked_at = COALESCE(locked_at, ?)
           WHERE supplier_id = ? AND store_id = ? AND business_date <= ?""",
        (stamp, supplier_id, store_id, period_end),
    )
    for table, date_column, status in (
        ("supplier_payments", "business_date", "audited"),
        ("supplier_balance_allocations", "business_date", "audited"),
        ("purchase_invoices", "business_date", "confirmed"),
        ("purchase_returns", "business_date", "audited"),
        ("supplier_refunds", "business_date", "audited"),
    ):
        conn.execute(
            f"""UPDATE {table} SET locked_at = COALESCE(locked_at, ?)
                WHERE supplier_id = ? AND store_id = ? AND {date_column} <= ?
                  AND status = ?""",
            (stamp, supplier_id, store_id, period_end, status),
        )
    conn.execute(
        "UPDATE supplier_reconciliations SET locked_at = ?, version = version + 1 "
        "WHERE id = ?",
        (stamp, reconciliation_id),
    )

