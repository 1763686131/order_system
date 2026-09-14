"""结算账户解析辅助方法。"""


def resolve_settlement_account(conn, store_id, requested="", fallback=""):
    """Return a configured account name while keeping old text values compatible."""
    requested = str(requested or "").strip()
    if requested:
        row = conn.execute(
            """
            SELECT account_name
            FROM bank_accounts
            WHERE store_id = ?
              AND (account_name = ? OR account_number = ? OR bank_name = ?)
            ORDER BY is_default DESC, id
            LIMIT 1
            """,
            (store_id, requested, requested, requested),
        ).fetchone()
        if row:
            return row["account_name"]
        # Existing documents may contain a historical free-text settlement account.
        return requested

    row = conn.execute(
        """
        SELECT account_name
        FROM bank_accounts
        WHERE store_id = ?
        ORDER BY is_default DESC, id
        LIMIT 1
        """,
        (store_id,),
    ).fetchone()
    return (row["account_name"] if row else "") or str(fallback or "").strip()


def adjust_bank_account_balance(conn, store_id, settlement_account, delta):
    """Adjust a configured account balance when a cash movement is audited.

    Historical free-text settlement values are intentionally ignored so old
    documents remain readable without accidentally changing a new account.
    """
    value = str(settlement_account or "").strip()
    if not value:
        return None
    row = conn.execute(
        """
        SELECT id, balance
        FROM bank_accounts
        WHERE store_id = ?
          AND (account_name = ? OR account_number = ? OR bank_name = ?)
        ORDER BY is_default DESC, id
        LIMIT 1
        """,
        (store_id, value, value, value),
    ).fetchone()
    if not row:
        return None
    amount = float(row["balance"] or 0) + float(delta or 0)
    conn.execute(
        "UPDATE bank_accounts SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (round(amount, 2), row["id"]),
    )
    return row["id"]
