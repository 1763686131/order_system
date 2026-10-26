from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from routes.stores import stores_bp
from routes.warehouses import warehouses_bp
from utils.db_helper import read_warehouses, write_warehouses


class StoreWarehouseManagementTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db_path = Path(self.directory.name) / "management.db"
        with self.get_db() as conn:
            conn.executescript("""
                CREATE TABLE stores (
                    id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT NOT NULL,
                    status TEXT, remark TEXT, color TEXT, text_color TEXT,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE warehouses (
                    id INTEGER PRIMARY KEY, code TEXT, name TEXT NOT NULL,
                    store_id INTEGER REFERENCES stores(id), address TEXT,
                    manager TEXT, phone TEXT, status TEXT, remark TEXT,
                    categories TEXT, created_at TEXT, updated_at TEXT
                );
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY, store_id INTEGER REFERENCES stores(id),
                    warehouse_id INTEGER REFERENCES warehouses(id)
                );
                CREATE TABLE customers (
                    id INTEGER PRIMARY KEY, store_id INTEGER
                );
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY,
                    warehouse_id INTEGER REFERENCES warehouses(id)
                );
                CREATE TABLE supplier_payments (
                    id INTEGER PRIMARY KEY, store_id INTEGER REFERENCES stores(id)
                );
                INSERT INTO stores VALUES
                    (1, 'S1', 'Used store', 'active', '', '#fff', '#333', '2026-01-01', ''),
                    (2, 'S2', 'Empty store', 'active', '', '#fff', '#333', '2026-01-02', '');
                INSERT INTO warehouses VALUES
                    (1, 'W1', 'Used warehouse', 1, 'Address', 'Manager', '123',
                     'active', 'Remark', '[]', '2026-01-01', ''),
                    (2, 'W2', 'Empty warehouse', 1, '', '', '', 'active', '',
                     '[{"id":201,"name":"Existing category","code":"CAT201"}]',
                     '2026-01-02', '');
                INSERT INTO orders VALUES (1, 1, 1);
                INSERT INTO customers VALUES (1, 1);
                INSERT INTO products VALUES (1, 1);
            """)

        for target in ("utils.db_helper.get_db", "routes.stores.get_db"):
            patcher = patch(target, self.get_db)
            patcher.start()
            self.addCleanup(patcher.stop)
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(stores_bp)
        app.register_blueprint(warehouses_bp)
        self.client = app.test_client()

    @contextmanager
    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def assert_references_preserved(self):
        with self.get_db() as conn:
            self.assertEqual(conn.execute("SELECT warehouse_id FROM orders").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT warehouse_id FROM products").fetchone()[0], 1)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_category_changes_on_referenced_warehouse(self):
        response = self.client.post("/api/warehouses/1/categories", json={"name": "New category"})
        self.assertEqual(response.status_code, 201, response.get_json())
        category_id = response.get_json()["id"]
        self.assertEqual(category_id, 101)

        response = self.client.put(
            f"/api/warehouses/1/categories/{category_id}",
            json={"name": "Updated category"},
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["name"], "Updated category")
        warehouses = self.client.get("/api/warehouses").get_json()
        self.assertEqual(warehouses[0]["categories"][0]["name"], "Updated category")
        self.assertEqual(warehouses[0]["address"], "Address")
        self.assertEqual(warehouses[0]["created_at"], "2026-01-01")
        self.assertEqual(warehouses[1]["categories"][0]["id"], 201)

        response = self.client.delete(f"/api/warehouses/1/categories/{category_id}")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(self.client.get("/api/warehouses/1").get_json()["categories"], [])
        self.assert_references_preserved()

    def test_category_changes_when_another_warehouse_is_referenced(self):
        response = self.client.post("/api/warehouses/2/categories", json={"name": "Second category"})
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["id"], 202)
        categories = self.client.get("/api/warehouses/2").get_json()["categories"]
        self.assertEqual([category["id"] for category in categories], [201, 202])
        self.assert_references_preserved()

    def test_create_and_update_warehouse_preserves_existing_references(self):
        response = self.client.post(
            "/api/warehouses", json={"code": "W3", "name": "New warehouse", "storeId": 2}
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        response = self.client.put("/api/warehouses/1", json={"name": "Updated warehouse"})
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["name"], "Updated warehouse")
        self.assertEqual(response.get_json()["created_at"], "2026-01-01")
        self.assertEqual(len(self.client.get("/api/warehouses").get_json()), 3)
        self.assert_references_preserved()

    def test_delete_empty_warehouse_preserves_referenced_warehouse(self):
        response = self.client.delete("/api/warehouses/2")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(self.client.get("/api/warehouses/2").status_code, 404)
        self.assertEqual(self.client.get("/api/warehouses/1").status_code, 200)
        self.assert_references_preserved()

    def test_delete_referenced_warehouse_returns_conflict(self):
        response = self.client.delete("/api/warehouses/1")
        self.assertEqual(response.status_code, 409, response.get_json())
        self.assertTrue(response.get_json()["error"])
        self.assert_references_preserved()

    def test_failed_bulk_delete_rolls_back_updates(self):
        warehouses = read_warehouses()
        remaining = [warehouse for warehouse in warehouses if warehouse["id"] == 2]
        remaining[0]["name"] = "Must roll back"
        with self.assertRaises(sqlite3.IntegrityError):
            write_warehouses(remaining)
        self.assertEqual(self.client.get("/api/warehouses/2").get_json()["name"], "Empty warehouse")
        self.assert_references_preserved()

    def test_delete_store_with_orders_and_customers_returns_conflict(self):
        response = self.client.delete("/api/stores/1")
        self.assertEqual(response.status_code, 409, response.get_json())
        self.assertTrue(response.get_json()["error"])
        self.assertEqual(self.client.get("/api/stores/1").status_code, 200)
        self.assert_references_preserved()

    def test_delete_store_with_only_warehouse_returns_conflict(self):
        with self.get_db() as conn:
            conn.execute("UPDATE warehouses SET store_id = 2 WHERE id = 2")
        response = self.client.delete("/api/stores/2")
        self.assertEqual(response.status_code, 409, response.get_json())
        self.assertTrue(response.get_json()["error"])
        self.assertEqual(self.client.get("/api/stores/2").status_code, 200)
        self.assertEqual(self.client.get("/api/warehouses/2").get_json()["storeId"], 2)

    def test_delete_store_with_other_foreign_key_returns_conflict(self):
        with self.get_db() as conn:
            conn.execute("INSERT INTO supplier_payments VALUES (1, 2)")
        response = self.client.delete("/api/stores/2")
        self.assertEqual(response.status_code, 409, response.get_json())
        self.assertTrue(response.get_json()["error"])
        self.assertEqual(self.client.get("/api/stores/2").status_code, 200)
        with self.get_db() as conn:
            self.assertEqual(conn.execute("SELECT store_id FROM supplier_payments").fetchone()[0], 2)

    def test_delete_empty_store_succeeds_and_repeated_delete_returns_not_found(self):
        response = self.client.delete("/api/stores/2")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertTrue(response.get_json()["success"])
        self.assertEqual(self.client.delete("/api/stores/2").status_code, 404)
        self.assertEqual(self.client.get("/api/stores/1").status_code, 200)
        self.assert_references_preserved()


if __name__ == "__main__":
    unittest.main()
