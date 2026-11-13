from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

from flask import Flask, g

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from routes.material_outbounds import material_outbounds_bp
import utils.db as db_module


class MaterialOutboundStockHistoryTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.ensure_schema(self.conn)
        self.conn.executescript("""
            CREATE TABLE stock_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_type TEXT NOT NULL, product_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL, store_id INTEGER NOT NULL,
                bin_code TEXT NOT NULL DEFAULT '', batch_no TEXT NOT NULL DEFAULT '',
                quantity REAL NOT NULL, updated_at TEXT,
                UNIQUE(product_type, product_id, warehouse_id, store_id, bin_code, batch_no)
            );
            CREATE TABLE stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_type TEXT NOT NULL, receipt_type TEXT NOT NULL,
                source_document_id INTEGER NOT NULL, source_document_no TEXT NOT NULL,
                source_item_id INTEGER, product_type TEXT NOT NULL,
                product_id INTEGER NOT NULL, warehouse_id INTEGER NOT NULL,
                store_id INTEGER NOT NULL, bin_code TEXT, batch_no TEXT,
                quantity REAL NOT NULL, unit_price REAL, tax_rate REAL,
                total_amount REAL, created_at TEXT
            );
        """)
        for name in ("create_audit_notifications", "complete_audit_notifications",
                     "broadcast_material_outbound_event"):
            patcher = patch("routes.material_outbounds." + name)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch("routes.material_outbounds.get_db", self.get_db)
        patcher.start()
        self.addCleanup(patcher.stop)
        app = Flask(__name__)
        app.config["TESTING"] = True

        @app.before_request
        def set_current_user():
            g.current_user = {
                "id": 1, "displayName": "Reviewer",
                "isSuperAdmin": True, "canAccessAdmin": True,
            }

        app.register_blueprint(material_outbounds_bp)
        self.client = app.test_client()

    def ensure_schema(self, conn):
        with patch.object(db_module, "_material_outbound_schema_ready", False):
            db_module._ensure_material_outbound_schema(conn)

    @contextmanager
    def get_db(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def add_stock(self, quantity, product=1, warehouse=1, store=1, batch=""):
        self.conn.execute("""
            INSERT INTO stock_balances (
                product_type, product_id, warehouse_id, store_id,
                bin_code, batch_no, quantity, updated_at
            ) VALUES ('raw-material', ?, ?, ?, '', ?, ?, '2026-11-01 08:00:00')
            ON CONFLICT(product_type, product_id, warehouse_id, store_id, bin_code, batch_no)
            DO UPDATE SET quantity = stock_balances.quantity + excluded.quantity
        """, (product, warehouse, store, batch, quantity))
        self.conn.commit()

    def draft(self, items):
        cursor = self.conn.execute("""
            INSERT INTO material_outbounds (
                document_no, document_date, store_id, warehouse_id,
                status, total_quantity, finished_linked
            ) VALUES (?, '2026-11-13', 1, 1, 'draft', ?, 0)
        """, (f"TEST-{self.conn.total_changes}", sum(qty for _, qty in items)))
        document_id = cursor.lastrowid
        for line, (product, quantity) in enumerate(items, start=1):
            self.conn.execute("""
                INSERT INTO material_outbound_items (
                    outbound_id, line_no, product_id, product_name, unit, quantity
                ) VALUES (?, ?, ?, ?, 'kg', ?)
            """, (document_id, line, product, f"Material {product}", quantity))
        self.conn.commit()
        return document_id

    def audit(self, document_id, expected=200):
        response = self.client.post(
            f"/api/material-outbounds/{document_id}/audit",
            json={"stockAfter": 9999, "items": [{"stockAfter": 9999}]},
        )
        self.assertEqual(response.status_code, expected, response.get_json())
        return response.get_json()

    def document(self, document_id):
        response = self.client.get(f"/api/material-outbounds/{document_id}")
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def snapshots(self, document_id):
        return [(item["stockBefore"], item["stockAfter"])
                for item in self.document(document_id)["items"]]

    def balance(self, product=1):
        return self.conn.execute("""
            SELECT COALESCE(SUM(quantity), 0) FROM stock_balances
            WHERE product_type = 'raw-material' AND product_id = ?
              AND warehouse_id = 1 AND store_id = 1
        """, (product,)).fetchone()[0]

    def test_history_survives_receipts_later_audits_and_reversal(self):
        self.add_stock(100)
        self.add_stock(500, warehouse=2)
        self.add_stock(700, store=2)
        first = self.draft([(1, 20)])
        response = self.audit(first)
        self.assertEqual(response["materialOutbound"]["items"][0]["stockAfter"], 80)
        self.add_stock(50, batch="later receipt")
        second = self.draft([(1, 30)])
        self.audit(second)
        self.assertEqual(self.balance(), 100)
        self.assertEqual(self.snapshots(first), [(100, 80)])
        self.assertEqual(self.snapshots(second), [(130, 100)])
        self.audit(first, expected=409)
        response = self.client.delete(f"/api/material-outbounds/{first}/audit")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(self.balance(), 120)
        self.assertEqual(self.snapshots(second), [(130, 100)])
        records = self.client.get("/api/material-outbounds").get_json()
        self.assertEqual(next(row for row in records if row["id"] == second)["items"][0]["stockAfter"], 100)

    def test_each_line_keeps_its_own_balance_across_fifo_batches(self):
        self.add_stock(10, batch="first")
        self.add_stock(90, batch="second")
        self.add_stock(15, product=2)
        document_id = self.draft([(1, 20), (1, 30), (2, 5)])
        self.audit(document_id)
        self.assertEqual(self.snapshots(document_id), [(100, 80), (80, 50), (15, 10)])
        self.assertEqual(self.balance(), 50)
        first_item_id = self.document(document_id)["items"][0]["id"]
        self.assertEqual(self.conn.execute(
            "SELECT COUNT(*) FROM stock_movements WHERE source_item_id = ?",
            (first_item_id,),
        ).fetchone()[0], 2)

    def test_zero_balance_is_saved_even_after_empty_batches_are_removed(self):
        self.add_stock(100)
        document_id = self.draft([(1, 100)])
        self.audit(document_id)
        self.assertEqual(self.snapshots(document_id), [(100, 0)])
        self.assertEqual(self.balance(), 0)
        self.add_stock(25)
        self.assertEqual(self.snapshots(document_id), [(100, 0)])

    def test_reverse_clears_snapshots_and_reaudit_uses_new_stock(self):
        self.add_stock(100)
        document_id = self.draft([(1, 20)])
        self.audit(document_id)
        self.add_stock(50)
        response = self.client.delete(f"/api/material-outbounds/{document_id}/audit")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(self.document(document_id)["status"], "draft")
        self.assertEqual(self.snapshots(document_id), [(None, None)])
        self.assertEqual(self.balance(), 150)
        self.audit(document_id)
        self.assertEqual(self.snapshots(document_id), [(150, 130)])

    def test_failed_later_line_rolls_back_deductions_and_snapshots(self):
        self.add_stock(100)
        document_id = self.draft([(1, 20), (1, 90)])
        self.audit(document_id, expected=409)
        self.assertEqual(self.balance(), 100)
        self.assertEqual(self.snapshots(document_id), [(None, None), (None, None)])
        self.assertEqual(self.document(document_id)["status"], "draft")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0], 0)

    def test_error_after_posting_rolls_back_snapshots(self):
        self.add_stock(100)
        document_id = self.draft([(1, 20)])
        with patch("routes.material_outbounds.complete_audit_notifications", side_effect=RuntimeError("fail")):
            self.audit(document_id, expected=500)
        self.assertEqual(self.balance(), 100)
        self.assertEqual(self.snapshots(document_id), [(None, None)])

    def test_failed_reverse_preserves_the_reviewed_snapshot(self):
        self.add_stock(100)
        document_id = self.draft([(1, 20)])
        self.audit(document_id)
        with patch("routes.material_outbounds.create_audit_notifications", side_effect=RuntimeError("fail")):
            response = self.client.delete(f"/api/material-outbounds/{document_id}/audit")
        self.assertEqual(response.status_code, 500, response.get_json())
        self.assertEqual(self.balance(), 80)
        self.assertEqual(self.snapshots(document_id), [(100, 80)])
        self.assertEqual(self.document(document_id)["status"], "reviewed")

    def test_schema_upgrade_preserves_old_items_without_inventing_history(self):
        legacy = sqlite3.connect(":memory:")
        self.addCleanup(legacy.close)
        legacy.row_factory = sqlite3.Row
        legacy.executescript("""
            CREATE TABLE material_outbound_items (
                id INTEGER PRIMARY KEY, outbound_id INTEGER, line_no INTEGER,
                product_id INTEGER, product_code TEXT, product_name TEXT,
                specification TEXT, unit TEXT, quantity REAL, remark TEXT
            );
            INSERT INTO material_outbound_items VALUES
                (7, 1, 1, 1, 'M1', 'Existing material', '', 'kg', 20, 'Keep remark');
        """)
        self.ensure_schema(legacy)
        self.ensure_schema(legacy)
        item = dict(legacy.execute("SELECT * FROM material_outbound_items WHERE id = 7").fetchone())
        self.assertEqual(item["quantity"], 20)
        self.assertEqual(item["remark"], "Keep remark")
        self.assertIsNone(item["stock_before"])
        self.assertIsNone(item["stock_after"])


if __name__ == "__main__":
    unittest.main()
