from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import utils.db as db_module


class RetiredFinanceSchemaTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.addCleanup(self.conn.close)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                freight_costs TEXT,
                current_payment REAL
            );
            CREATE TABLE freight_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER REFERENCES orders(id),
                paid_amount REAL
            );
            CREATE INDEX idx_retired_freight_order ON freight_records(order_id);
            CREATE TABLE reserve_funds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL
            );
            CREATE TABLE permissions (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE
            );
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY
            );
            CREATE TABLE role_permissions (
                role_id INTEGER REFERENCES roles(id),
                permission_id INTEGER REFERENCES permissions(id)
            );
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                display_name TEXT
            );
            CREATE TABLE supplier_reconciliations (
                id INTEGER PRIMARY KEY,
                status TEXT
            );
            INSERT INTO orders VALUES
                (1, '[{"type":"freight","amount":280}]', 100);
            INSERT INTO freight_records VALUES (1, 1, 50);
            INSERT INTO reserve_funds VALUES (1, 1000);
            INSERT INTO roles VALUES (1);
            INSERT INTO permissions VALUES
                (1, 'admin.route.finance.employee_expenses'),
                (2, 'admin.finance.employee_expense.read'),
                (3, 'admin.route.finance.logistics_truck'),
                (4, 'admin.route.finance.express_courier'),
                (5, 'admin.route.finance.receivables'),
                (6, 'admin.finance.supplier_reconciliation.confirm');
            INSERT INTO role_permissions VALUES
                (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6);
            INSERT INTO employees VALUES (1, 'Existing employee');
            INSERT INTO supplier_reconciliations VALUES (1, 'confirmed');
        """)

    def snapshot(self):
        return "\n".join(self.conn.iterdump())

    def assert_cleaned(self):
        tables = {
            row[0] for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        self.assertNotIn("freight_records", tables)
        self.assertNotIn("reserve_funds", tables)
        self.assertIsNone(self.conn.execute(
            "SELECT name FROM sqlite_master WHERE name = 'idx_retired_freight_order'"
        ).fetchone())
        self.assertEqual(
            self.conn.execute("SELECT id FROM permissions ORDER BY id").fetchall(),
            [(5,), (6,)],
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT permission_id FROM role_permissions ORDER BY permission_id"
            ).fetchall(),
            [(5,), (6,)],
        )
        self.assertEqual(
            self.conn.execute("SELECT * FROM orders").fetchall(),
            [(1, '[{"type":"freight","amount":280}]', 100)],
        )
        self.assertEqual(
            self.conn.execute("SELECT * FROM employees").fetchall(),
            [(1, "Existing employee")],
        )
        self.assertEqual(
            self.conn.execute("SELECT * FROM supplier_reconciliations").fetchall(),
            [(1, "confirmed")],
        )
        self.assertEqual(self.conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_removes_retired_tables_permissions_and_links(self):
        db_module._remove_retired_finance_schema(self.conn)
        self.assert_cleaned()

    def test_removes_links_without_relying_on_foreign_key_cascades(self):
        self.conn.execute("PRAGMA foreign_keys = OFF")
        db_module._remove_retired_finance_schema(self.conn)
        self.assert_cleaned()

    def test_cleanup_is_idempotent_after_restart(self):
        db_module._remove_retired_finance_schema(self.conn)
        original = self.snapshot()
        db_module._remove_retired_finance_schema(self.conn)
        self.assertEqual(self.snapshot(), original)
        self.assert_cleaned()

    def test_missing_retired_tables_and_permission_schema_are_supported(self):
        with closing(sqlite3.connect(":memory:")) as empty:
            db_module._remove_retired_finance_schema(empty)
            self.assertEqual(
                empty.execute("SELECT name FROM sqlite_master").fetchall(), []
            )

    def test_cleanup_does_not_require_role_permission_table(self):
        self.conn.execute("DROP TABLE role_permissions")
        db_module._remove_retired_finance_schema(self.conn)
        self.assertEqual(
            self.conn.execute("SELECT id FROM permissions ORDER BY id").fetchall(),
            [(5,), (6,)],
        )

    def test_failed_table_removal_rolls_back_all_changes(self):
        original = self.snapshot()
        self.conn.set_authorizer(
            lambda action, name, *_: sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_DROP_TABLE and name == "reserve_funds"
            else sqlite3.SQLITE_OK
        )
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                db_module._remove_retired_finance_schema(self.conn)
        finally:
            self.conn.set_authorizer(None)
        self.assertEqual(self.snapshot(), original)
        db_module._remove_retired_finance_schema(self.conn)
        self.assert_cleaned()

    def test_failed_permission_removal_restores_tables_and_role_links(self):
        original = self.snapshot()
        self.conn.set_authorizer(
            lambda action, name, *_: sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_DELETE and name == "permissions"
            else sqlite3.SQLITE_OK
        )
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                db_module._remove_retired_finance_schema(self.conn)
        finally:
            self.conn.set_authorizer(None)
        self.assertEqual(self.snapshot(), original)

    def test_cleanup_respects_outer_transaction_rollback(self):
        original = self.snapshot()
        self.conn.execute("BEGIN IMMEDIATE")
        db_module._remove_retired_finance_schema(self.conn)
        self.assert_cleaned()
        self.conn.rollback()
        self.assertEqual(self.snapshot(), original)


if __name__ == "__main__":
    unittest.main()
