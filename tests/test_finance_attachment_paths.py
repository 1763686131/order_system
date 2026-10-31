from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from routes.settings import settings_bp
import utils.system_settings as system_settings


class FinanceAttachmentPathSettingsTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""
            CREATE TABLE system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self.addCleanup(self.conn.close)
        patcher = patch("utils.system_settings.get_db", self.get_db)
        patcher.start()
        self.addCleanup(patcher.stop)

        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(settings_bp)
        self.client = app.test_client()

    @contextmanager
    def get_db(self):
        with self.conn:
            yield self.conn

    def test_path_settings_save_and_return_both_custom_attachment_directories(self):
        with TemporaryDirectory() as root:
            paths = {
                "reportPath": "",
                "documentPath": str(Path(root) / "documents"),
                "receiptPath": str(Path(root) / "receipts"),
                "receiptAttachmentPath": str(Path(root) / "receipt-attachments"),
                "paymentAttachmentPath": str(Path(root) / "payment-attachments"),
                "bankCardBgPath": str(Path(root) / "bank-backgrounds"),
                "bankIconPath": str(Path(root) / "bank-icons"),
            }
            response = self.client.put("/api/settings/paths", json=paths)
            self.assertEqual(response.status_code, 200, response.get_json())
            data = response.get_json()["data"]
            self.assertEqual(data["receiptAttachmentPath"], str(Path(paths["receiptAttachmentPath"]).resolve()))
            self.assertEqual(data["paymentAttachmentPath"], str(Path(paths["paymentAttachmentPath"]).resolve()))
            self.assertTrue(Path(data["receiptAttachmentPath"]).is_dir())
            self.assertTrue(Path(data["paymentAttachmentPath"]).is_dir())

            loaded = self.client.get("/api/settings/paths")
            self.assertEqual(loaded.status_code, 200)
            self.assertEqual(loaded.get_json()["data"]["receiptAttachmentPath"], data["receiptAttachmentPath"])
            self.assertEqual(loaded.get_json()["data"]["paymentAttachmentPath"], data["paymentAttachmentPath"])

    def test_default_attachment_folders_are_under_uploads(self):
        response = self.client.get("/api/settings/paths")
        self.assertEqual(response.status_code, 200)
        paths = response.get_json()["data"]
        self.assertEqual(Path(paths["receiptAttachmentPath"]).name, "payment-receipts")
        self.assertEqual(Path(paths["paymentAttachmentPath"]).name, "supplier-payments")
        self.assertEqual(Path(paths["receiptAttachmentPath"]).parent.name, "uploads")
        self.assertEqual(Path(paths["paymentAttachmentPath"]).parent.name, "uploads")


if __name__ == "__main__":
    unittest.main()
