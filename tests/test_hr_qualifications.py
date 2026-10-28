from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask, g

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from routes.hr_qualifications import FIELDS, QUALIFICATION_PERMISSION, hr_qualifications_bp
import utils.db as db_module
from utils.db import _ensure_hr_qualifications_schema
from utils.permission_catalog import ALL_PERMISSION_CODES, PERMISSION_MODULES


class CompanyQualificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db_path = Path(self.directory.name) / "qualifications.db"
        db_module._hr_qualifications_schema_ready = False
        with self.get_db() as conn:
            _ensure_hr_qualifications_schema(conn)
        patcher = patch("routes.hr_qualifications.get_db", self.get_db)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = {
            "canAccessAdmin": True,
            "isSuperAdmin": False,
            "permissions": [QUALIFICATION_PERMISSION],
            "displayName": "Qualification tester",
        }
        app = Flask(__name__)
        app.config.update(TESTING=True, SECRET_KEY="qualification-test-key")

        @app.before_request
        def set_current_user():
            g.current_user = self.user

        app.register_blueprint(hr_qualifications_bp)
        self.client = app.test_client()
        self.payload = {
            "folderId": 1,
            "certificateNo": "TEST-2026-001",
            "companyName": "测试复合材料有限公司",
            "certificationBasis": "GB/T24001-2016/ISO14001:2015",
            "registeredAddress": "测试注册地址",
            "auditAddress": "测试审核地址",
            "certificationScope": "复合材料的销售及相关环境管理活动",
            "issueDate": "2026-03-11",
            "validUntil": "2029-03-10",
            "certificateStatus": "有效",
        }
        self.assertEqual(self.create_folder().status_code, 201)

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

    def create_folder(self, name="环境管理体系认证"):
        return self.client.post("/api/hr/qualifications/folders", json={"name": name})

    def create(self, **changes):
        return self.client.post(
            "/api/hr/qualifications", json={**self.payload, **changes}
        )

    def test_folder_and_file_are_separate_records(self):
        folder = self.client.get("/api/hr/qualifications/folders").get_json()["data"][0]
        self.assertEqual(folder["name"], "环境管理体系认证")
        self.assertEqual(folder["fileCount"], 0)

        response = self.create()
        self.assertEqual(response.status_code, 201, response.get_json())
        created = response.get_json()["data"]
        self.assertEqual(created["folderId"], folder["id"])
        self.assertEqual(created["folderName"], folder["name"])

        folder = self.client.get("/api/hr/qualifications/folders").get_json()["data"][0]
        self.assertEqual(folder["fileCount"], 1)
        files = self.client.get(
            f"/api/hr/qualifications?folder_id={folder['id']}"
        ).get_json()["data"]
        self.assertEqual(files, [created])

    def test_create_persists_all_file_fields_and_can_be_read(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.get_json())
        created = response.get_json()["data"]
        with self.get_db() as conn:
            row = conn.execute(
                "SELECT * FROM hr_company_qualifications WHERE id = ?", (created["id"],)
            ).fetchone()
            self.assertEqual(row["folder_id"], 1)
            for key, (column, _, _) in FIELDS.items():
                self.assertEqual(row[column], self.payload[key])
            self.assertEqual(row["created_by"], "Qualification tester")
        detail = self.client.get(f'/api/hr/qualifications/{created["id"]}')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["data"], created)

    def test_update_can_move_file_to_another_folder(self):
        original = self.create().get_json()["data"]
        response = self.create_folder("另一套体系")
        self.assertEqual(response.status_code, 201)
        second_folder = response.get_json()["data"]
        self.assertNotEqual(original["folderId"], second_folder["id"])
        response = self.client.put(
            f'/api/hr/qualifications/{original["id"]}',
            json={**self.payload, "folderId": second_folder["id"], "certificateNo": "TEST-MOVED"},
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        saved = response.get_json()["data"]
        self.assertEqual(saved["folderId"], second_folder["id"])
        self.assertEqual(saved["folderName"], second_folder["name"])
        self.assertEqual(
            self.client.get(f"/api/hr/qualifications?folder_id={second_folder['id']}").get_json()["data"],
            [saved],
        )
        self.assertEqual(
            self.client.get(f"/api/hr/qualifications?folder_id={original['folderId']}").get_json()["data"],
            [],
        )

    def test_only_selected_folder_contains_new_file(self):
        second_folder = self.create_folder("独立目录").get_json()["data"]
        file = self.create(folderId=second_folder["id"]).get_json()["data"]
        self.assertEqual(self.client.get("/api/hr/qualifications?folder_id=1").get_json()["data"], [])
        self.assertEqual(
            self.client.get(f"/api/hr/qualifications?folder_id={second_folder['id']}").get_json()["data"],
            [file],
        )
        counts = {
            folder["id"]: folder["fileCount"]
            for folder in self.client.get("/api/hr/qualifications/folders").get_json()["data"]
        }
        self.assertEqual(counts, {1: 0, second_folder["id"]: 1})

    def test_folder_creation_only_requires_directory_name(self):
        response = self.create_folder("  Quality files  ")
        self.assertEqual(response.status_code, 201, response.get_json())
        folder = response.get_json()["data"]
        self.assertEqual(folder["name"], "Quality files")
        self.assertEqual(folder["fileCount"], 0)
        self.assertEqual(self.client.get("/api/hr/qualifications").get_json()["data"], [])

    def test_folder_creation_rejects_invalid_payloads(self):
        for payload in (None, [], ["invalid"], "invalid", {}, {"name": True}, {"name": []}, {"name": "  "}, {"name": "x" * 101}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/hr/qualifications/folders", json=payload)
                self.assertEqual(response.status_code, 400, response.get_json())

    def test_permission_is_in_final_catalog(self):
        self.assertIn(QUALIFICATION_PERMISSION, ALL_PERMISSION_CODES)
        module = next(
            module for module in PERMISSION_MODULES
            if module["code"] == "admin_company_qualifications"
        )
        self.assertEqual([item["code"] for item in module["permissions"]], [QUALIFICATION_PERMISSION])

    def test_folder_name_is_unique_case_insensitively(self):
        response = self.create_folder("环境管理体系认证")
        self.assertEqual(response.status_code, 409, response.get_json())
        self.assertEqual(self.create_folder("TEST DIRECTORY").status_code, 201)
        response = self.create_folder("test directory")
        self.assertEqual(response.status_code, 409, response.get_json())

    def test_duplicate_certificate_is_rejected_case_insensitively(self):
        self.assertEqual(self.create().status_code, 201)
        response = self.create(certificateNo=self.payload["certificateNo"].lower())
        self.assertEqual(response.status_code, 409, response.get_json())
        self.assertEqual(len(self.client.get("/api/hr/qualifications").get_json()["data"]), 1)

    def test_invalid_folder_and_fields_do_not_create_records(self):
        invalid = [
            {"folderId": 999},
            {"folderId": "bad"},
            {"folderId": True},
            {"folderId": 1.5},
            {"folderId": 0},
            {"folderId": 10**30},
            {"certificateNo": None},
            {"companyName": ["invalid"]},
            {"certificationBasis": "x" * 501},
            {"issueDate": "2026-02-30"},
            {"issueDate": "20260311"},
            {"validUntil": "2026-01-01"},
            {"certificateStatus": "unknown"},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assertEqual(self.create(**changes).status_code, 400)
        for key in [*FIELDS, "folderId"]:
            with self.subTest(missing=key):
                payload = {field: value for field, value in self.payload.items() if field != key}
                self.assertEqual(self.client.post("/api/hr/qualifications", json=payload).status_code, 400)
        self.assertEqual(self.client.get("/api/hr/qualifications").get_json()["data"], [])

    def test_folder_filter_rejects_invalid_or_missing_directories(self):
        for value in ("bad", "", "0", "-1", "1.5"):
            with self.subTest(value=value):
                response = self.client.get("/api/hr/qualifications", query_string={"folder_id": value})
                self.assertEqual(response.status_code, 400, response.get_json())
        self.assertEqual(self.client.get("/api/hr/qualifications?folder_id=999").status_code, 404)

    def test_failed_edit_keeps_original_file_and_directory(self):
        original = self.create().get_json()["data"]
        for changes, expected in (({"folderId": 999}, 400), ({"validUntil": "2020-01-01"}, 400)):
            with self.subTest(changes=changes):
                response = self.client.put(
                    f'/api/hr/qualifications/{original["id"]}', json={**self.payload, **changes}
                )
                self.assertEqual(response.status_code, expected)
                self.assertEqual(
                    self.client.get(f'/api/hr/qualifications/{original["id"]}').get_json()["data"],
                    original,
                )

    def test_legacy_file_rows_are_migrated_into_directories(self):
        with self.get_db() as conn:
            conn.execute("DROP TABLE hr_company_qualifications")
            conn.execute(
                """
                CREATE TABLE hr_company_qualifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_name TEXT NOT NULL,
                    certificate_no TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    company_name TEXT NOT NULL,
                    certification_basis TEXT NOT NULL,
                    registered_address TEXT NOT NULL,
                    audit_address TEXT NOT NULL,
                    certification_scope TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    certificate_status TEXT NOT NULL DEFAULT '有效',
                    created_by TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                INSERT INTO hr_company_qualifications
                (folder_name, certificate_no, company_name, certification_basis,
                 registered_address, audit_address, certification_scope,
                 issue_date, valid_until)
                VALUES ('旧目录', 'LEGACY-001', '旧公司', '依据', '注册地址',
                        '审核地址', '认证范围', '2026-01-01', '2027-01-01')
                """
            )
            db_module._hr_qualifications_schema_ready = False
            _ensure_hr_qualifications_schema(conn)
        folder = self.client.get("/api/hr/qualifications/folders").get_json()["data"][0]
        self.assertEqual(folder["name"], "旧目录")
        files = self.client.get(
            f"/api/hr/qualifications?folder_id={folder['id']}"
        ).get_json()["data"]
        self.assertEqual(files[0]["certificateNo"], "LEGACY-001")
        with self.get_db() as conn:
            db_module._hr_qualifications_schema_ready = False
            _ensure_hr_qualifications_schema(conn)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(
            self.client.get(f"/api/hr/qualifications?folder_id={folder['id']}").get_json()["data"],
            files,
        )

    def test_missing_records_return_404(self):
        self.assertEqual(self.client.get("/api/hr/qualifications/999").status_code, 404)
        self.assertEqual(
            self.client.put("/api/hr/qualifications/999", json=self.payload).status_code, 404
        )
    def test_every_endpoint_requires_login_and_admin_permission(self):
        calls = [
            ("get", "/api/hr/qualifications/folders", {}),
            ("post", "/api/hr/qualifications/folders", {"json": {"name": "x"}}),
            ("get", "/api/hr/qualifications", {}),
            ("get", "/api/hr/qualifications/1", {}),
            ("post", "/api/hr/qualifications", {"json": self.payload}),
            ("put", "/api/hr/qualifications/1", {"json": self.payload}),
        ]
        for user, expected in (
            (None, 401),
            ({"canAccessAdmin": False, "permissions": [QUALIFICATION_PERMISSION]}, 403),
            ({"canAccessAdmin": True, "permissions": []}, 403),
        ):
            self.user = user
            for method, path, kwargs in calls:
                with self.subTest(user=user, method=method, path=path):
                    self.assertEqual(getattr(self.client, method)(path, **kwargs).status_code, expected)

    def test_super_admin_can_access_without_explicit_permission(self):
        self.user = {"canAccessAdmin": True, "isSuperAdmin": True}
        self.assertEqual(self.client.get("/api/hr/qualifications/folders").status_code, 200)


if __name__ == "__main__":
    unittest.main()
