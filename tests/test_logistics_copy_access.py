from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

from flask import Flask, g

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from routes.logistics_copy import logistics_copy_bp
from utils.permission_catalog import ADMIN_ROUTE_BRANCH_PERMISSIONS


class LogisticsCopyAccessTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.addCleanup(self.conn.close)
        self.conn.execute("""
            CREATE TABLE logistics_copy_settings (
                id INTEGER PRIMARY KEY,
                fields_json TEXT,
                templates_json TEXT,
                updated_at TEXT
            )
        """)
        self.default_fields = [{"key": "title", "template": "Default template"}]
        self.bound_fields = [{"key": "title", "template": "Order information"}]
        self.conn.execute(
            "INSERT INTO logistics_copy_settings VALUES (1, ?, ?, ?)",
            (
                json.dumps(self.default_fields),
                json.dumps([{
                    "bindingTarget": "order-info",
                    "boundUserIds": [101],
                    "fields": self.bound_fields,
                }]),
                "2026-10-29",
            ),
        )
        patcher = patch("routes.logistics_copy.get_db", self.get_db)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = {
            "id": 101,
            "canAccessAdmin": True,
            "isSuperAdmin": False,
            "permissions": [],
        }
        app = Flask(__name__)
        app.config.update(TESTING=True, SECRET_KEY="copy-access-test")

        @app.before_request
        def set_current_user():
            g.current_user = self.user

        app.register_blueprint(logistics_copy_bp)
        self.client = app.test_client()

    @contextmanager
    def get_db(self):
        yield self.conn

    def resolve(self, target="order-info"):
        return self.client.get(
            "/api/settings/logistics-copy/resolve", query_string={"target": target}
        )

    def test_order_copy_accepts_sales_or_logistics_route_permission(self):
        for route in ("orders", "logistics"):
            with self.subTest(route=route):
                self.user["permissions"] = [
                    ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"][route]
                ]
                response = self.resolve()
                self.assertEqual(response.status_code, 200, response.get_json())
                self.assertEqual(response.get_json()["data"]["fields"], self.bound_fields)

    def test_logistics_copy_still_requires_logistics_route_permission(self):
        self.user["permissions"] = [
            ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["orders"]
        ]
        self.assertEqual(self.resolve("logistics-info").status_code, 403)
        self.user["permissions"] = [
            ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["logistics"]
        ]
        self.assertEqual(self.resolve("logistics-info").status_code, 200)

    def test_accounts_without_route_permission_cannot_resolve_templates(self):
        for target in ("order-info", "logistics-info"):
            with self.subTest(target=target):
                self.assertEqual(self.resolve(target).status_code, 403)

    def test_order_copy_keeps_template_binding_scoped_to_current_account(self):
        self.user["id"] = 102
        self.user["permissions"] = [
            ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["logistics"]
        ]
        response = self.resolve()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["fields"], self.default_fields)

    def test_new_copy_access_does_not_grant_template_management_access(self):
        self.user["permissions"] = [
            ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["logistics"]
        ]
        self.assertEqual(
            self.client.get("/api/settings/logistics-copy").status_code, 403
        )
        self.assertEqual(
            self.client.put("/api/settings/logistics-copy", json={}).status_code, 403
        )

    def test_copy_still_requires_login_and_admin_access(self):
        self.user["permissions"] = [
            ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["logistics"]
        ]
        self.user["canAccessAdmin"] = False
        self.assertEqual(self.resolve().status_code, 403)
        self.user = None
        self.assertEqual(self.resolve().status_code, 401)


if __name__ == "__main__":
    unittest.main()
