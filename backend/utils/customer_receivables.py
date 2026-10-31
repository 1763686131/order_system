"""Rebuild open customer receivables by source document."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


_CENT = Decimal("0.01")


def money(value):
    try:
        amount = Decimal(str(value if value not in (None, "") else 0))
        if not amount.is_finite():
            raise InvalidOperation
        return amount.quantize(_CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def source_key(source_type, source_id):
    return f"{source_type}:{int(source_id)}"


def _date_key(value):
    return str(value or "").replace("T", " ")


def _allocation_table_exists(conn):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'customer_payment_allocations'"
    ).fetchone() is not None


def _consume(documents, amount, target_key=None):
    remaining = max(money(amount), Decimal("0.00"))
    if remaining <= 0:
        return

    if target_key:
        for document in documents:
            if document["key"] != target_key:
                continue
            applied = min(document["_outstanding"], remaining)
            document["_outstanding"] -= applied
            remaining -= applied
            if remaining <= 0:
                return

    if remaining <= 0:
        return

    oldest_first = sorted(
        documents,
        key=lambda item: (
            _date_key(item["documentDate"]),
            item["_sortId"],
            item["key"],
        ),
    )
    for document in oldest_first:
        if target_key and document["key"] == target_key:
            continue
        available = max(document["_outstanding"], Decimal("0.00"))
        applied = min(available, remaining)
        document["_outstanding"] -= applied
        remaining -= applied
        if remaining <= 0:
            break


def _opening_source(customer_id, amount, document_date, document_no):
    amount = max(money(amount), Decimal("0.00"))
    return {
        "key": source_key("initial", customer_id),
        "sourceType": "initial",
        "sourceId": int(customer_id),
        "documentNo": document_no,
        "documentDate": document_date or "",
        "amount": amount,
        "_outstanding": amount,
        "_sortId": 0,
    }


def _reconcile_final(documents, opening_sources, target, customer_id,
                     opening_date, has_initial):
    target = max(money(target), Decimal("0.00"))
    current = sum(
        (item["_outstanding"] for item in documents + opening_sources),
        Decimal("0.00"),
    )
    difference = target - current
    if difference > 0:
        existing = next(
            (item for item in opening_sources if item["key"] == source_key("initial", customer_id)),
            None,
        )
        if existing:
            existing["_outstanding"] += difference
            existing["amount"] += difference
        else:
            opening_sources.append(_opening_source(
                customer_id,
                difference,
                opening_date,
                "期初欠款" if has_initial else "历史欠款调整",
            ))
    elif difference < 0:
        remaining = -difference
        for source in sorted(
            opening_sources,
            key=lambda item: (_date_key(item["documentDate"]), item["_sortId"]),
        ):
            applied = min(source["_outstanding"], remaining)
            source["_outstanding"] -= applied
            remaining -= applied
            if remaining <= 0:
                return
        _consume(documents, remaining)


def _receipt_allocations(conn, payment_id):
    if not payment_id or not _allocation_table_exists(conn):
        return []
    return conn.execute(
        """SELECT source_type, source_id, amount FROM customer_payment_allocations
           WHERE payment_id = ? ORDER BY id""",
        (payment_id,),
    ).fetchall()


def get_open_receivable_documents(conn, customer_id):
    """Return positive document balances after replaying active customer ledger entries."""
    customer = conn.execute(
        """SELECT id, initial_receivable, initial_receivable_at, receivable, created_at
           FROM customers WHERE id = ?""",
        (customer_id,),
    ).fetchone()
    if not customer:
        return None

    documents = []
    opening_sources = []
    events = []
    initial_amount = max(money(customer["initial_receivable"]), Decimal("0.00"))
    if initial_amount > 0:
        initial_date = customer["initial_receivable_at"] or customer["created_at"] or ""
        events.append({
            "date": initial_date,
            "sortId": 0,
            "type": "initial",
            "amount": initial_amount,
            "documentDate": initial_date,
            "netChange": initial_amount,
        })

    transactions = conn.execute(
        """SELECT * FROM customer_account_transactions
           WHERE customer_id = ? AND status = 'active'
             AND transaction_type IN ('order_audit', 'customer_payment', 'customer_return')
           ORDER BY created_at, id""",
        (customer_id,),
    ).fetchall()

    for transaction in transactions:
        event = {
            "date": transaction["created_at"] or "",
            "sortId": int(transaction["id"]),
            "transaction": transaction,
        }
        if transaction["transaction_type"] == "order_audit":
            order = None
            if transaction["order_id"]:
                order = conn.execute(
                    "SELECT id, order_number, date, audit_state FROM orders WHERE id = ?",
                    (transaction["order_id"],),
                ).fetchone()
            if order and order["audit_state"] != 1:
                continue
            amount = max(
                money(transaction["order_receivable"]),
                money(transaction["receivable_change"])
                + money(transaction["stored_balance_applied"]),
                Decimal("0.00"),
            )
            if amount <= 0:
                continue
            event.update({
                "type": "order",
                "sourceType": "order" if order else "legacy",
                "sourceId": int(order["id"]) if order else int(transaction["id"]),
                "documentNo": (
                    (order["order_number"] if order else None)
                    or transaction["order_number"]
                    or f"TX{transaction['id']}"
                ),
                "documentDate": (
                    (order["date"] if order else None)
                    or transaction["created_at"]
                    or ""
                ),
                "amount": amount,
                "netChange": max(amount - money(transaction["stored_balance_applied"]), Decimal("0.00")),
                "storedBalanceApplied": max(
                    money(transaction["stored_balance_applied"]), Decimal("0.00")
                ),
            })
        elif transaction["transaction_type"] == "customer_payment":
            payment = None
            if transaction["payment_id"]:
                payment = conn.execute(
                    "SELECT id, status, allocation_mode FROM payment_receipts WHERE id = ?",
                    (transaction["payment_id"],),
                ).fetchone()
            if payment and payment["status"] != "audited":
                continue
            event.update({
                "type": "payment",
                "amount": max(-money(transaction["receivable_change"]), Decimal("0.00")),
                "netChange": -max(-money(transaction["receivable_change"]), Decimal("0.00")),
                "paymentId": payment["id"] if payment else transaction["payment_id"],
                "manual": bool(payment and payment["allocation_mode"] == "manual"),
            })
        else:
            returned = conn.execute(
                """SELECT id, return_number, original_order_number, return_date,
                          writeoff_amount, status
                   FROM return_orders
                   WHERE account_transaction_id = ? OR return_number = ?
                   ORDER BY id DESC LIMIT 1""",
                (transaction["id"], transaction["order_number"] or ""),
            ).fetchone()
            if returned and returned["status"] not in ("audited", "completed"):
                continue
            event.update({
                "type": "return",
                "amount": max(
                    money(returned["writeoff_amount"] if returned else -money(transaction["receivable_change"])),
                    Decimal("0.00"),
                ),
                "originalOrderNo": returned["original_order_number"] if returned else "",
                "documentDate": (
                    (returned["return_date"] if returned else None)
                    or transaction["created_at"]
                    or ""
                ),
            })
            event["netChange"] = -event["amount"]
        events.append(event)

    opening_date = (
        customer["initial_receivable_at"]
        or customer["created_at"]
        or ""
    )
    # Reverse-audit snapshots can retain later-created values; current receivable
    # plus active ledger deltas is authoritative for an unmatched opening balance.
    event_change_total = sum(
        (money(event.get("netChange")) for event in events),
        Decimal("0.00"),
    )
    unattributed_opening = max(
        money(customer["receivable"]) - event_change_total,
        Decimal("0.00"),
    )
    if unattributed_opening > 0:
        events.append({
            "date": opening_date,
            "sortId": -1,
            "type": "opening_residual",
            "amount": unattributed_opening,
            "documentDate": opening_date,
            "netChange": unattributed_opening,
        })

    events.sort(key=lambda item: (_date_key(item["date"]), item["sortId"]))

    for event in events:
        event_type = event["type"]
        if event_type == "initial":
            opening_sources.append(_opening_source(
                customer_id, event["amount"], event["documentDate"], "期初欠款"
            ))
        elif event_type == "opening_residual":
            opening_sources.append(_opening_source(
                customer_id,
                event["amount"],
                event["documentDate"],
                "期初欠款" if initial_amount > 0 else "历史欠款调整",
            ))
        elif event_type == "order":
            key = source_key(event["sourceType"], event["sourceId"])
            amount = max(event["amount"] - event["storedBalanceApplied"], Decimal("0.00"))
            documents.append({
                "key": key,
                "sourceType": event["sourceType"],
                "sourceId": event["sourceId"],
                "documentNo": event["documentNo"],
                "documentDate": event["documentDate"],
                "amount": event["amount"],
                "_outstanding": amount,
                "_sortId": event["sortId"],
            })
        elif event_type == "payment":
            sources = documents + opening_sources
            if event["manual"]:
                for allocation in _receipt_allocations(conn, event["paymentId"]):
                    _consume(
                        sources,
                        allocation["amount"],
                        source_key(allocation["source_type"], allocation["source_id"]),
                    )
            else:
                _consume(sources, event["amount"])
        elif event_type == "return":
            target = next((item for item in documents if item["documentNo"] == event["originalOrderNo"]), None)
            target_key = target["key"] if target else None
            _consume(documents + opening_sources, event["amount"], target_key)

    _reconcile_final(
        documents,
        opening_sources,
        customer["receivable"],
        customer_id,
        opening_date,
        initial_amount > 0,
    )

    result = []
    for document in sorted(
        documents + opening_sources,
        key=lambda item: (
            _date_key(item["documentDate"]),
            item["_sortId"],
            item["key"],
        ),
    ):
        outstanding = max(document["_outstanding"], Decimal("0.00"))
        if outstanding <= 0:
            continue
        response_document = {
            "sourceType": document["sourceType"],
            "sourceId": document["sourceId"],
            "documentNo": document["documentNo"],
            "documentDate": str(document["documentDate"] or "")[:10],
            "amount": float(document["amount"]),
            "outstandingAmount": float(outstanding),
        }
        existing = next(
            (item for item in result if source_key(item["sourceType"], item["sourceId"]) == document["key"]),
            None,
        )
        if existing:
            existing["amount"] = round(existing["amount"] + response_document["amount"], 2)
            existing["outstandingAmount"] = round(
                existing["outstandingAmount"] + response_document["outstandingAmount"], 2
            )
            if response_document["documentDate"] < existing["documentDate"]:
                existing["documentDate"] = response_document["documentDate"]
        else:
            result.append(response_document)
    for document in result:
        if document["sourceType"] == "initial":
            document["documentNo"] = "期初欠款" if initial_amount > 0 else "历史欠款调整"
    return result


def validate_allocations(conn, customer_id, allocations, max_amount, min_amount=0):
    if not isinstance(allocations, list):
        raise ValueError("收款抵扣明细格式错误")
    documents = get_open_receivable_documents(conn, customer_id)
    available = {
        source_key(row["sourceType"], row["sourceId"]): row
        for row in (documents or [])
    }
    normalized = []
    seen = set()
    total = Decimal("0.00")
    for entry in allocations:
        if not isinstance(entry, dict):
            raise ValueError("收款抵扣明细格式错误")
        source_type = str(entry.get("sourceType") or "")
        if source_type not in {"order", "initial", "legacy"}:
            raise ValueError("收款抵扣来源无效")
        try:
            source_id = int(entry.get("sourceId"))
        except (TypeError, ValueError):
            raise ValueError("收款抵扣来源无效")
        if source_id < 0:
            raise ValueError("收款抵扣来源无效")
        key = source_key(source_type, source_id)
        if key in seen:
            raise ValueError("同一欠款单据不能重复添加抵扣明细")
        seen.add(key)
        amount = money(entry.get("amount"))
        if amount <= 0:
            raise ValueError("单据抵扣金额必须大于零")
        document = available.get(key)
        if not document:
            raise ValueError("抵扣来源已结清或不存在，请刷新欠款明细")
        if amount > money(document["outstandingAmount"]):
            raise ValueError(f"{document['documentNo']} 的未抵扣金额已变化，请刷新后重试")
        total += amount
        normalized.append({
            "sourceType": source_type,
            "sourceId": source_id,
            "documentNo": document["documentNo"],
            "amount": amount,
        })

    if total > money(max_amount):
        raise ValueError("抵扣合计不能超过本次收款及优惠金额")
    if total < money(min_amount):
        raise ValueError("抵扣金额不能小于优惠金额")
    return normalized, total
