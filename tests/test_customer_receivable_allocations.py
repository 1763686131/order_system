from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

from flask import Flask, g

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from utils.customer_receivables import get_open_receivable_documents, validate_allocations
from routes.customers import customers_bp
from routes.payment_receipts import payment_receipts_bp
import utils.db as db_module


class CustomerReceivableAllocationTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        self.conn.executescript("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                initial_receivable REAL,
                initial_receivable_at TEXT,
                receivable REAL,
                created_at TEXT
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                order_number TEXT,
                date TEXT,
                audit_state INTEGER
            );
            CREATE TABLE customer_account_transactions (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_id INTEGER,
                order_number TEXT,
                payment_id INTEGER,
                transaction_type TEXT,
                status TEXT,
                created_at TEXT,
                order_receivable REAL,
                receivable_change REAL,
                stored_balance_applied REAL,
                receivable_after REAL
            );
            CREATE TABLE payment_receipts (
                id INTEGER PRIMARY KEY,
                status TEXT,
                allocation_mode TEXT
            );
            CREATE TABLE customer_payment_allocations (
                id INTEGER PRIMARY KEY,
                payment_id INTEGER,
                source_type TEXT,
                source_id INTEGER,
                amount REAL
            );
            CREATE TABLE return_orders (
                id INTEGER PRIMARY KEY,
                return_number TEXT,
                original_order_number TEXT,
                return_date TEXT,
                writeoff_amount REAL,
                status TEXT,
                account_transaction_id INTEGER
            );
            INSERT INTO customers VALUES (1, 0, NULL, 150, '2025-01-01');
            INSERT INTO orders VALUES
                (101, 'SO-OLD', '2025-01-01', 1),
                (102, 'SO-NEW', '2025-02-01', 1);
            INSERT INTO payment_receipts VALUES
                (201, 'audited', 'fifo'),
                (202, 'audited', 'manual');
            INSERT INTO customer_account_transactions (
                id, customer_id, order_id, order_number, payment_id,
                transaction_type, status, created_at, order_receivable,
                receivable_change, stored_balance_applied, receivable_after
            ) VALUES
                (1, 1, 101, 'SO-OLD', NULL, 'order_audit', 'active',
                 '2025-01-01T09:00:00', 100, 100, 0, 100),
                (2, 1, 102, 'SO-NEW', NULL, 'order_audit', 'active',
                 '2025-02-01T09:00:00', 100, 100, 0, 200),
                (3, 1, NULL, NULL, 201, 'customer_payment', 'active',
                 '2025-03-01T09:00:00', 0, -30, 0, 170),
                (4, 1, NULL, NULL, 202, 'customer_payment', 'active',
                 '2025-04-01T09:00:00', 0, -20, 0, 150);
            INSERT INTO customer_payment_allocations VALUES
                (1, 202, 'order', 102, 20);
        """)

    def test_replays_fifo_and_manual_allocations_against_their_sources(self):
        documents = get_open_receivable_documents(self.conn, 1)

        self.assertEqual(
            [(row["documentNo"], row["outstandingAmount"]) for row in documents],
            [("SO-OLD", 70.0), ("SO-NEW", 80.0)],
        )

    def test_manual_allocation_is_checked_against_current_document_balance(self):
        allocations, total = validate_allocations(
            self.conn,
            1,
            [{"sourceType": "order", "sourceId": 102, "amount": 80}],
            100,
        )

        self.assertEqual(total, 80)
        self.assertEqual(allocations[0]["documentNo"], "SO-NEW")
        with self.assertRaisesRegex(ValueError, "未抵扣金额已变化"):
            validate_allocations(
                self.conn,
                1,
                [{"sourceType": "order", "sourceId": 102, "amount": 80.01}],
                100,
            )

    def test_reversing_an_earlier_payment_restores_the_original_document(self):
        self.conn.execute("UPDATE customer_account_transactions SET status = 'reversed' WHERE id = 3")
        self.conn.execute("UPDATE payment_receipts SET status = 'draft' WHERE id = 201")
        self.conn.execute("UPDATE customers SET receivable = 180 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        self.assertEqual(
            [(row['sourceId'], row['outstandingAmount']) for row in documents],
            [(101, 100.0), (102, 80.0)],
        )
        self.assertFalse(any(row['sourceType'] == 'initial' for row in documents))

    def test_payment_before_initial_date_cannot_consume_initial_debt(self):
        self.conn.execute("""
            UPDATE customers
            SET initial_receivable = 40, initial_receivable_at = '2025-03-15', receivable = 190
            WHERE id = 1
        """)
        documents = get_open_receivable_documents(self.conn, 1)
        self.assertEqual(
            [(row['documentNo'], row['outstandingAmount']) for row in documents],
            [('SO-OLD', 70.0), ('SO-NEW', 80.0), ('期初欠款', 40.0)],
        )
        self.assertEqual(
            sum(row['outstandingAmount'] for row in documents),
            190.0,
        )

    def test_reversed_payment_snapshot_does_not_create_opening_debt(self):
        self.conn.execute("UPDATE customer_account_transactions SET status = 'reversed' WHERE id = 3")
        self.conn.execute("UPDATE payment_receipts SET status = 'draft' WHERE id = 201")
        self.conn.execute("UPDATE customers SET receivable = 180 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        self.assertEqual(sum(row['outstandingAmount'] for row in documents), 180.0)
        self.assertEqual(
            {row['sourceType'] for row in documents},
            {'order'},
        )

    def test_return_credit_reduces_its_original_order(self):
        self.conn.execute("""
            INSERT INTO customer_account_transactions
            (id, customer_id, order_number, transaction_type, status, created_at,
             receivable_change, receivable_after)
            VALUES (5, 1, 'RT-NEW', 'customer_return', 'active', '2025-05-01', -10, 140)
        """)
        self.conn.execute("INSERT INTO return_orders VALUES (1, 'RT-NEW', 'SO-NEW', '2025-05-01', 10, 'audited', 5)")
        self.conn.execute("UPDATE customers SET receivable = 140 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        self.assertEqual([row['outstandingAmount'] for row in documents], [70.0, 70.0])
        self.conn.execute("UPDATE customer_account_transactions SET status = 'reversed' WHERE id = 5")
        self.conn.execute("UPDATE return_orders SET status = 'draft', account_transaction_id = NULL WHERE id = 1")
        self.conn.execute("UPDATE customers SET receivable = 150 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        self.assertEqual([row['outstandingAmount'] for row in documents], [70.0, 80.0])

    def test_initial_debt_and_stored_balance_are_counted_once(self):
        self.conn.execute("UPDATE customers SET initial_receivable = 50, initial_receivable_at = '2024-01-01', receivable = 160")
        self.conn.execute("UPDATE customer_account_transactions SET stored_balance_applied = 40, receivable_change = 60 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        self.assertEqual(
            [(row['sourceType'], row['documentNo'], row['outstandingAmount']) for row in documents],
            [('initial', '期初欠款', 20.0), ('order', 'SO-OLD', 60.0), ('order', 'SO-NEW', 80.0)],
        )

    def test_unknown_opening_debt_keeps_a_stable_allocation_source(self):
        self.conn.execute("UPDATE customers SET receivable = 225 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        self.assertEqual(sum(row['outstandingAmount'] for row in documents), 225)
        opening = next(row for row in documents if row['sourceType'] == 'initial')
        self.assertEqual(opening['sourceId'], 1)
        self.assertEqual(opening['outstandingAmount'], 45)
        self.assertEqual(
            {row['documentNo']: row['outstandingAmount'] for row in documents},
            {'SO-OLD': 100.0, 'SO-NEW': 80.0, '历史欠款调整': 45.0},
        )
        self.conn.execute("INSERT INTO payment_receipts VALUES (203, 'audited', 'manual')")
        self.conn.execute("INSERT INTO customer_payment_allocations VALUES (2, 203, 'legacy', 1, 5)")
        self.conn.execute("""
            INSERT INTO customer_account_transactions (id, customer_id, payment_id,
                transaction_type, status, created_at, receivable_change, receivable_after)
            VALUES (5, 1, 203, 'customer_payment', 'active', '2025-05-01', -5, 220)
        """)
        self.conn.execute("UPDATE customers SET receivable = 220 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        opening = next(row for row in documents if row['sourceType'] == 'initial')
        self.assertEqual(opening['outstandingAmount'], 40)
        self.assertEqual(sum(row['outstandingAmount'] for row in documents), 220)

    def test_missing_order_link_remains_an_allocatable_legacy_source(self):
        self.conn.execute("""
            INSERT INTO customer_account_transactions
            (id, customer_id, order_number, transaction_type, status, created_at,
             order_receivable, receivable_change, receivable_after)
            VALUES (5, 1, 'SO-UNLINKED', 'order_audit', 'active', '2025-05-01', 25, 25, 175)
        """)
        self.conn.execute("UPDATE customers SET receivable = 175 WHERE id = 1")
        documents = get_open_receivable_documents(self.conn, 1)
        legacy = next(row for row in documents if row['sourceType'] == 'legacy')
        self.assertEqual((legacy['sourceId'], legacy['documentNo'], legacy['outstandingAmount']), (5, 'SO-UNLINKED', 25))

    def test_invalid_duplicate_or_excess_allocations_are_rejected(self):
        valid = {'sourceType': 'order', 'sourceId': 101, 'amount': 30}
        for allocations, maximum, minimum in [
            ([valid, valid], 100, 0),
            ([valid], 20, 0),
            ([valid], 100, 40),
            ([dict(valid, sourceId=999)], 100, 0),
            ([dict(valid, amount='NaN')], 100, 0),
            ([dict(valid, amount='Infinity')], 100, 0),
        ]:
            with self.subTest(allocations=allocations, maximum=maximum, minimum=minimum):
                with self.assertRaises(ValueError):
                    validate_allocations(self.conn, 1, allocations, maximum, minimum)


class ReceiptAllocationApiTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.addCleanup(self.conn.close)
        self.conn.executescript('''
            CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, name TEXT);
            CREATE TABLE stores (id INTEGER PRIMARY KEY, name TEXT, status TEXT);
            CREATE TABLE warehouses (id INTEGER PRIMARY KEY);
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY, order_number TEXT, date TEXT, audit_state INTEGER,
                store_id INTEGER, customer_id INTEGER, warehouse_id INTEGER
            );
            CREATE TABLE bank_accounts (
                id INTEGER PRIMARY KEY, store_id INTEGER, account_name TEXT,
                account_number TEXT, bank_name TEXT, is_default INTEGER, balance REAL, updated_at TEXT
            );
            INSERT INTO stores VALUES (1, 'Test store', 'active');
            INSERT INTO bank_accounts VALUES (1, 1, 'Receipt account', '', '', 1, 1000, NULL);
        ''')
        for flag in ('_schema_ready', '_return_schema_ready'):
            patcher = patch.object(db_module, flag, False)
            patcher.start()
            self.addCleanup(patcher.stop)
        db_module._ensure_customer_schema(self.conn)
        db_module._ensure_return_schema(self.conn)
        self.conn.executescript('''
            INSERT INTO customers (id, customer_code, customer_name, store_id, balance,
                initial_receivable, receivable, status, created_at)
            VALUES (1, '001', 'Test customer', 1, 0, 0, 200, 'active', '2025-01-01');
            INSERT INTO orders (id, order_number, date, audit_state, store_id, customer_id)
            VALUES (101, 'SO-OLD', '2025-01-01', 1, 1, 1),
                   (102, 'SO-NEW', '2025-02-01', 1, 1, 1);
            INSERT INTO customer_account_transactions (customer_id, order_id, order_number,
                transaction_type, order_receivable, receivable_change, receivable_after, created_at)
            VALUES (1, 101, 'SO-OLD', 'order_audit', 100, 100, 100, '2025-01-01'),
                   (1, 102, 'SO-NEW', 'order_audit', 100, 100, 200, '2025-02-01');
        ''')
        for target in ('routes.payment_receipts.get_db', 'routes.customers.get_db'):
            patcher = patch(target, self.get_db)
            patcher.start()
            self.addCleanup(patcher.stop)
        for target in ('create_audit_notifications', 'complete_audit_notifications'):
            patcher = patch(f'routes.payment_receipts.{target}')
            patcher.start()
            self.addCleanup(patcher.stop)
        app = Flask(__name__)
        app.config['TESTING'] = True

        @app.before_request
        def set_current_user():
            g.current_user = {'id': 1, 'displayName': 'Test operator', 'canAccessAdmin': True, 'isSuperAdmin': True}

        app.register_blueprint(customers_bp)
        app.register_blueprint(payment_receipts_bp)
        self.client = app.test_client()

    @contextmanager
    def get_db(self):
        with self.conn:
            yield self.conn

    def create_receipt(self, **overrides):
        payload = {
            'customerId': 1, 'documentDate': '2026-10-31', 'paymentAmount': 120,
            'discountAmount': 10, 'allocationMode': 'manual',
            'allocations': [{'sourceType': 'order', 'sourceId': 102, 'amount': 80}],
        }
        payload.update(overrides)
        response = self.client.post('/api/payment-receipts', json=payload)
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()['receipt']

    def documents(self):
        response = self.client.get('/api/customers/1/receivable-documents')
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()['items']

    def test_save_reload_edit_audit_and_reverse_manual_receipt(self):
        receipt = self.create_receipt()
        receipt_id = receipt['id']
        self.assertEqual(receipt['writeoffAmount'], 80)
        self.assertEqual(receipt['advanceAmount'], 50)
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [100, 100])
        detail = self.client.get(f'/api/payment-receipts/{receipt_id}').get_json()
        self.assertEqual(detail['allocations'][0]['sourceId'], 102)
        edited = self.client.put(f'/api/payment-receipts/{receipt_id}', json={'remark': 'Keep allocations'})
        self.assertEqual(edited.status_code, 200, edited.get_json())
        self.assertEqual(edited.get_json()['receipt']['allocations'], detail['allocations'])
        audited = self.client.post(f'/api/payment-receipts/{receipt_id}/audit')
        self.assertEqual(audited.status_code, 200, audited.get_json())
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [100, 20])
        self.assertEqual(self.conn.execute('SELECT balance FROM bank_accounts').fetchone()[0], 1120)
        self.assertEqual(self.conn.execute('SELECT balance FROM customers').fetchone()[0], 50)
        reversed_response = self.client.delete(f'/api/payment-receipts/{receipt_id}/audit')
        self.assertEqual(reversed_response.status_code, 200, reversed_response.get_json())
        self.assertEqual(reversed_response.get_json()['receipt']['writeoffAmount'], 80)
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [100, 100])
        self.assertEqual(self.conn.execute('SELECT balance FROM bank_accounts').fetchone()[0], 1000)
        self.assertEqual(self.conn.execute('SELECT balance FROM customers').fetchone()[0], 0)
        reaudited = self.client.post(f'/api/payment-receipts/{receipt_id}/audit')
        self.assertEqual(reaudited.status_code, 200, reaudited.get_json())
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [100, 20])

    def test_audit_rejects_a_draft_if_selected_document_was_paid_elsewhere(self):
        first = self.create_receipt(paymentAmount=80, discountAmount=0)
        second = self.create_receipt(paymentAmount=80, discountAmount=0)
        result = self.client.post(f"/api/payment-receipts/{second['id']}/audit")
        self.assertEqual(result.status_code, 200, result.get_json())
        result = self.client.post(f"/api/payment-receipts/{first['id']}/audit")
        self.assertEqual(result.status_code, 409, result.get_json())
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [100, 20])
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM customer_account_transactions WHERE transaction_type = ?', ('customer_payment',)).fetchone()[0], 1)

    def test_fifo_clients_remain_compatible_and_draft_deletion_cleans_allocations(self):
        receipt = self.create_receipt(paymentAmount=30, discountAmount=0, allocationMode='fifo')
        self.assertEqual(receipt['allocations'], [])
        response = self.client.post(f"/api/payment-receipts/{receipt['id']}/audit")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [70, 100])
        draft = self.create_receipt()
        response = self.client.delete(f"/api/payment-receipts/{draft['id']}")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM customer_payment_allocations').fetchone()[0], 0)

    def test_automatic_receipt_surplus_becomes_advance_and_reverses_cleanly(self):
        receipt = self.create_receipt(paymentAmount=250, discountAmount=10, allocationMode='fifo', allocations=[])
        self.assertEqual(receipt['allocationMode'], 'fifo')
        self.assertEqual(receipt['writeoffAmount'], 200)
        self.assertEqual(receipt['advanceAmount'], 60)
        result = self.client.post(f"/api/payment-receipts/{receipt['id']}/audit")
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertEqual(self.documents(), [])
        customer = self.conn.execute('SELECT receivable, balance FROM customers WHERE id = 1').fetchone()
        self.assertEqual(tuple(customer), (0, 60))
        self.assertEqual(self.conn.execute('SELECT balance FROM bank_accounts').fetchone()[0], 1250)
        result = self.client.delete(f"/api/payment-receipts/{receipt['id']}/audit")
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [100, 100])
        self.assertEqual(self.conn.execute('SELECT balance FROM customers WHERE id = 1').fetchone()[0], 0)

    def test_switching_draft_to_automatic_clears_manual_allocations(self):
        receipt = self.create_receipt()
        result = self.client.put(f"/api/payment-receipts/{receipt['id']}", json={
            'allocationMode': 'fifo', 'allocations': [],
        })
        self.assertEqual(result.status_code, 200, result.get_json())
        receipt = result.get_json()['receipt']
        self.assertEqual(receipt['allocationMode'], 'fifo')
        self.assertEqual(receipt['allocations'], [])
        self.assertEqual(receipt['writeoffAmount'], 130)
        self.assertEqual(receipt['advanceAmount'], 0)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM customer_payment_allocations').fetchone()[0], 0)
        result = self.client.post(f"/api/payment-receipts/{receipt['id']}/audit")
        self.assertEqual(result.status_code, 200, result.get_json())
        self.assertEqual([row['outstandingAmount'] for row in self.documents()], [70])

    def test_customer_cannot_allocate_against_another_customers_document(self):
        self.conn.execute("INSERT INTO customers (id, customer_name, store_id, receivable, status) VALUES (2, 'Other customer', 1, 50, 'active')")
        self.conn.commit()
        response = self.client.post('/api/payment-receipts', json={
            'customerId': 2, 'documentDate': '2026-10-31', 'paymentAmount': 10,
            'allocationMode': 'manual',
            'allocations': [{'sourceType': 'order', 'sourceId': 101, 'amount': 10}],
        })
        self.assertEqual(response.status_code, 400, response.get_json())
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM payment_receipts').fetchone()[0], 0)

    def test_schema_upgrade_is_idempotent_and_keeps_saved_allocations(self):
        receipt = self.create_receipt()
        db_module._schema_ready = False
        db_module._ensure_customer_schema(self.conn)
        detail = self.client.get(f"/api/payment-receipts/{receipt['id']}").get_json()
        self.assertEqual(detail['allocationMode'], 'manual')
        self.assertEqual(detail['allocations'][0]['amount'], 80)
        self.assertEqual(self.conn.execute('PRAGMA foreign_key_check').fetchall(), [])


if __name__ == "__main__":
    unittest.main()
