import json
from pathlib import Path
import sqlite3
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from routes import customers


class CustomerStatementRecipientTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')
        self.connection.row_factory = sqlite3.Row
        self.addCleanup(self.connection.close)
        self.connection.executescript('''
            CREATE TABLE stores (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY, customer_code TEXT, customer_name TEXT,
                store_id INTEGER, balance REAL, balance_at TEXT,
                initial_receivable REAL, initial_receivable_at TEXT,
                receivable REAL, created_at TEXT
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY, audit_state INTEGER, date TEXT,
                order_number TEXT, should_receive REAL, current_payment REAL,
                remark TEXT, order_goods TEXT, contact_person TEXT,
                contact_address TEXT, receiver_name TEXT, receiver_address TEXT
            );
            CREATE TABLE customer_account_transactions (
                id INTEGER PRIMARY KEY, customer_id INTEGER, status TEXT,
                transaction_type TEXT, created_at TEXT, order_id INTEGER,
                order_number TEXT, payment_id INTEGER, payment_number TEXT,
                stored_balance_applied REAL DEFAULT 0,
                receivable_increase REAL DEFAULT 0,
                receivable_change REAL DEFAULT 0,
                receivable_after REAL DEFAULT 0,
                balance_change REAL DEFAULT 0
            );
            CREATE TABLE return_orders (
                id INTEGER PRIMARY KEY, account_transaction_id INTEGER,
                return_number TEXT, status TEXT, return_date TEXT,
                total_amount REAL, refund_amount REAL, writeoff_amount REAL,
                remark TEXT
            );
            CREATE TABLE return_order_items (
                id INTEGER PRIMARY KEY, return_id INTEGER, line_no INTEGER
            );
            CREATE TABLE payment_receipts (
                id INTEGER PRIMARY KEY, status TEXT, document_no TEXT,
                document_date TEXT, payment_amount REAL, remark TEXT
            );
            INSERT INTO stores VALUES (1, 'Store');
            INSERT INTO customers VALUES (
                7, 'C007', 'Customer', 1, 5, '2026-10-10',
                20, '2026-10-09', 280, '2026-10-09'
            );
            INSERT INTO return_orders VALUES (
                4, 4, 'R004', 'audited', '2026-10-14', 30, 0, 30, ''
            );
            INSERT INTO payment_receipts VALUES (
                5, 'audited', 'P005', '2026-10-15', 10, ''
            );
        ''')
        products = json.dumps([
            {'name': 'A', 'quantity': 2, 'unit': 'kg', 'price': 30},
            {'name': 'B', 'quantity': 1, 'unit': 'kg', 'price': 40},
        ])
        self.connection.executemany('''
            INSERT INTO orders VALUES (?, 1, ?, ?, 100, 0, '', ?, ?, ?, ?, ?)
        ''', [
            (1, '2026-10-11', 'O001', products,
             'Recipient', 'Delivery address', 'Old recipient', 'Old address'),
            (2, '2026-10-12', 'O002', products,
             '', None, 'Legacy recipient', 'Legacy address'),
            (3, '2026-10-13', 'O003', products, None, '', None, ''),
        ])
        self.connection.executemany('''
            INSERT INTO customer_account_transactions (
                id, customer_id, status, transaction_type, created_at,
                order_id, order_number, payment_id, payment_number,
                receivable_increase, receivable_change
            ) VALUES (?, 7, 'active', ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, 'order_audit', '2026-10-11', 1, 'O001', None, '', 100, 100),
            (2, 'order_audit', '2026-10-12', 2, 'O002', None, '', 100, 100),
            (3, 'order_audit', '2026-10-13', 3, 'O003', None, '', 100, 100),
            (4, 'customer_return', '2026-10-14', None, 'R004', None, '', -30, -30),
            (5, 'customer_payment', '2026-10-15', None, '', 5, 'P005', 0, -10),
        ])

        @contextmanager
        def isolated_database():
            yield self.connection

        patcher = patch.object(customers, 'get_db', isolated_database)
        patcher.start()
        self.addCleanup(patcher.stop)
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(customers.customers_bp)
        self.client = app.test_client()

    def statement(self, query=''):
        response = self.client.get(f'/api/customers/7/debt-details{query}')
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_order_recipient_fields_and_legacy_fallback(self):
        for query in ('', '?expandProducts=true'):
            with self.subTest(query=query):
                records = {
                    row['docNumber']: row
                    for row in self.statement(query)['records']
                }
                self.assertEqual(records['O001']['receiverName'], 'Recipient')
                self.assertEqual(records['O001']['receiverAddress'], 'Delivery address')
                self.assertEqual(records['O002']['receiverName'], 'Legacy recipient')
                self.assertEqual(records['O002']['receiverAddress'], 'Legacy address')
                self.assertEqual(records['O003']['receiverName'], '')
                self.assertEqual(records['O003']['receiverAddress'], '')

    def test_other_business_types_have_no_recipient_data(self):
        result = self.statement('?expandProducts=true')
        other_rows = [
            row for row in result['records'] if row['businessType'] != 'ORDER'
        ]
        self.assertEqual(
            {row['businessType'] for row in other_rows},
            {'RETURN', 'PAYMENT', 'INITIAL', 'BALANCE'},
        )
        for row in other_rows:
            with self.subTest(business_type=row['businessType']):
                self.assertFalse(row.get('receiverName'))
                self.assertFalse(row.get('receiverAddress'))
        self.assertEqual(result['total'], 7)
        self.assertEqual(result['summary']['receivable'], 275)
        self.assertEqual(result['records'][-1]['currentDebt'], 275)

    def test_order_schema_without_recipient_columns(self):
        for column in (
            'contact_person', 'contact_address', 'receiver_name', 'receiver_address',
        ):
            self.connection.execute(f'ALTER TABLE orders DROP COLUMN {column}')
        result = self.statement('?expandProducts=true&businessType=ORDER')
        self.assertEqual(result['total'], 3)
        for record in result['records']:
            self.assertEqual(record['receiverName'], '')
            self.assertEqual(record['receiverAddress'], '')

    def test_filter_and_product_allocation_keep_recipient_and_debt(self):
        result = self.statement(
            '?expandProducts=true&businessType=ORDER'
            '&startDate=2026-10-12&endDate=2026-10-12'
        )
        self.assertEqual(result['total'], 1)
        record = result['records'][0]
        self.assertEqual(record['receiverName'], 'Legacy recipient')
        self.assertEqual(record['receiverAddress'], 'Legacy address')
        self.assertEqual(record['debtAmount'], 100)
        self.assertEqual(record['currentDebt'], 215)
        self.assertEqual(
            [product['allocatedDebt'] for product in record['products']],
            [60, 40],
        )
        self.assertEqual(result['summary']['receivable'], 275)


if __name__ == '__main__':
    unittest.main()
