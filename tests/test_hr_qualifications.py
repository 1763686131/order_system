from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask, g

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from routes.hr_qualifications import QUALIFICATION_PERMISSION, hr_qualifications_bp
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
            "title": "年度企业资料",
            "fields": [
                {"label": "资料编号", "value": "TEST-2026-001"},
                {"label": "负责人", "value": "资料管理员"},
                {"label": "使用范围", "value": "销售业务\n资料备案"},
            ],
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
            self.assertEqual(row["title"], self.payload["title"])
            self.assertEqual(json.loads(row["fields_json"]), self.payload["fields"])
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
            json={**self.payload, "folderId": second_folder["id"], "title": "已修改名称"},
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

    def test_files_are_not_limited_by_certificate_number_or_status(self):
        self.assertEqual(self.create().status_code, 201)
        fields = [
            {"label": "工作进度", "value": "待确认"},
            {"label": "计划时间", "value": "下季度"},
            {"label": "说明", "value": "第一项"},
            {"label": "说明", "value": "第二项"},
        ]
        response = self.create(fields=fields)
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["data"]["fields"], fields)
        self.assertEqual(len(self.client.get("/api/hr/qualifications").get_json()["data"]), 2)

    def test_edit_updates_titles_values_and_field_order(self):
        original = self.create().get_json()["data"]
        fields = [
            {"label": "新的标题", "value": "任意文本内容"},
            {"label": "备注", "value": "<script>alert('plain text')</script>\n第二行"},
        ]
        response = self.client.put(
            f'/api/hr/qualifications/{original["id"]}',
            json={**self.payload, "title": "文件新名称", "fields": fields},
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        saved = self.client.get(f'/api/hr/qualifications/{original["id"]}').get_json()["data"]
        self.assertEqual(saved["title"], "文件新名称")
        self.assertEqual(saved["fields"], fields)
        self.assertEqual(saved["folderId"], original["folderId"])
        self.assertEqual(saved["createdAt"], original["createdAt"])

    def test_title_and_fields_are_trimmed_and_maximum_lengths_are_accepted(self):
        response = self.create(
            title="  自定义名称  ",
            fields=[{"label": "  自定义标题  ", "value": "  内容\n下一行  "}],
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        self.assertEqual(response.get_json()["data"]["title"], "自定义名称")
        self.assertEqual(response.get_json()["data"]["fields"], [{"label": "自定义标题", "value": "内容\n下一行"}])
        response = self.create(
            title="文" * 200,
            fields=[{"label": "题" * 100, "value": "内" * 5000}] * 50,
        )
        self.assertEqual(response.status_code, 201, response.get_json())

    def test_invalid_folder_and_fields_do_not_create_records(self):
        invalid = [
            {"folderId": 999},
            {"folderId": "bad"},
            {"folderId": True},
            {"folderId": 1.5},
            {"folderId": 0},
            {"folderId": 10**30},
            {"title": None},
            {"title": "  "},
            {"title": ["invalid"]},
            {"title": "x" * 201},
            {"fields": None},
            {"fields": {}},
            {"fields": []},
            {"fields": self.payload["fields"] * 17},
            {"fields": ["invalid"]},
            {"fields": [{"label": "  ", "value": "内容"}]},
            {"fields": [{"label": True, "value": "内容"}]},
            {"fields": [{"label": "x" * 101, "value": "内容"}]},
            {"fields": [{"label": "标题", "value": "  "}]},
            {"fields": [{"label": "标题", "value": ["invalid"]}]},
            {"fields": [{"label": "标题", "value": "x" * 5001}]},
            {"fields": [{"label": "标题"}]},
            {"fields": [{"value": "内容"}]},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                self.assertEqual(self.create(**changes).status_code, 400)
        for key in ["title", "fields", "folderId"]:
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
        for changes, expected in (({"folderId": 999}, 400), ({"fields": [{"label": "", "value": "内容"}]}, 400)):
            with self.subTest(changes=changes):
                response = self.client.put(
                    f'/api/hr/qualifications/{original["id"]}', json={**self.payload, **changes}
                )
                self.assertEqual(response.status_code, expected)
                self.assertEqual(
                    self.client.get(f'/api/hr/qualifications/{original["id"]}').get_json()["data"],
                    original,
                )

    def install_legacy_schema(self, folder_id=None):
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
            if folder_id is not None:
                conn.execute("ALTER TABLE hr_company_qualifications ADD COLUMN folder_id INTEGER")
            conn.execute(
                """
                INSERT INTO hr_company_qualifications
                (id, folder_name, certificate_no, company_name, certification_basis,
                 registered_address, audit_address, certification_scope,
                 issue_date, valid_until, created_by, created_at, updated_at)
                VALUES (41, '旧目录', 'LEGACY-001', '旧公司', '依据', '注册地址',
                        '审核地址', '认证范围', '2026-01-01', '2027-01-01',
                        '旧录入人', '2026-01-02 10:00:00', '2026-01-03 11:00:00')
                """
            )
            if folder_id is not None:
                conn.execute("UPDATE hr_company_qualifications SET folder_id = ?", (folder_id,))

    def test_legacy_file_rows_are_migrated_into_directories(self):
        self.install_legacy_schema()
        with self.get_db() as conn:
            db_module._hr_qualifications_schema_ready = False
            _ensure_hr_qualifications_schema(conn)
        folder = next(
            folder for folder in self.client.get("/api/hr/qualifications/folders").get_json()["data"]
            if folder["name"] == "旧目录"
        )
        files = self.client.get(
            f"/api/hr/qualifications?folder_id={folder['id']}"
        ).get_json()["data"]
        self.assertEqual(files[0]["id"], 41)
        self.assertEqual(files[0]["title"], "LEGACY-001")
        self.assertEqual(files[0]["fields"], [
            {"label": "证书编号", "value": "LEGACY-001"},
            {"label": "中文名称", "value": "旧公司"},
            {"label": "认证依据", "value": "依据"},
            {"label": "注册地址", "value": "注册地址"},
            {"label": "审核地址", "value": "审核地址"},
            {"label": "认证范围", "value": "认证范围"},
            {"label": "发证日期", "value": "2026年1月1日"},
            {"label": "有效日期", "value": "2027年1月1日"},
            {"label": "证书状态", "value": "有效"},
        ])
        self.assertEqual(files[0]["createdAt"], "2026-01-02 10:00:00")
        self.assertEqual(files[0]["updatedAt"], "2026-01-03 11:00:00")
        with self.get_db() as conn:
            self.assertEqual(conn.execute("SELECT created_by FROM hr_company_qualifications WHERE id = 41").fetchone()[0], "旧录入人")
            db_module._hr_qualifications_schema_ready = False
            _ensure_hr_qualifications_schema(conn)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(
            self.client.get(f"/api/hr/qualifications?folder_id={folder['id']}").get_json()["data"],
            files,
        )
        response = self.client.put(
            "/api/hr/qualifications/41",
            json={**self.payload, "folderId": folder["id"], "fields": [{"label": "修改标题", "value": "新的内容"}]},
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["data"]["fields"], [{"label": "修改标题", "value": "新的内容"}])

    def test_current_certificate_schema_migrates_without_changing_folder(self):
        self.install_legacy_schema(folder_id=1)
        with self.get_db() as conn:
            db_module._hr_qualifications_schema_ready = False
            _ensure_hr_qualifications_schema(conn)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        saved = self.client.get("/api/hr/qualifications/41").get_json()["data"]
        self.assertEqual(saved["folderId"], 1)
        self.assertEqual(saved["folderName"], "环境管理体系认证")
        self.assertEqual(saved["title"], "LEGACY-001")

    def test_failed_migration_rolls_back_original_table_and_data(self):
        self.install_legacy_schema(folder_id=1)
        with self.get_db() as conn:
            conn.set_authorizer(
                lambda action, name, *_: sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_DROP_TABLE and name == "hr_company_qualifications_legacy"
                else sqlite3.SQLITE_OK
            )
            db_module._hr_qualifications_schema_ready = False
            try:
                with self.assertRaises(sqlite3.DatabaseError):
                    _ensure_hr_qualifications_schema(conn)
            finally:
                conn.set_authorizer(None)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(hr_company_qualifications)")}
            self.assertIn("certificate_no", columns)
            self.assertNotIn("fields_json", columns)
            self.assertEqual(conn.execute("SELECT certificate_no FROM hr_company_qualifications WHERE id = 41").fetchone()[0], "LEGACY-001")
            self.assertIsNone(conn.execute(
                "SELECT name FROM sqlite_master WHERE name = 'hr_company_qualifications_legacy'"
            ).fetchone())

    def test_missing_records_return_404(self):
        self.assertEqual(self.client.get("/api/hr/qualifications/999").status_code, 404)
        self.assertEqual(
            self.client.put("/api/hr/qualifications/999", json=self.payload).status_code, 404
        )

    def test_sharing_is_disabled_by_default_and_cannot_be_enabled_by_file_payload(self):
        file = self.create(shareEnabled=True, share_token="attacker").get_json()["data"]
        response = self.client.get(f'/api/hr/qualifications/{file["id"]}/share')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"], {"enabled": False, "path": None})
        self.assertIn("no-store", response.headers["Cache-Control"])
        with self.get_db() as conn:
            row = conn.execute(
                "SELECT share_enabled, share_token FROM hr_company_qualifications WHERE id = ?",
                (file["id"],),
            ).fetchone()
            self.assertEqual(tuple(row), (0, None))

    def test_enabled_share_exposes_only_the_document_without_logging_in(self):
        file = self.create().get_json()["data"]
        response = self.client.put(
            f'/api/hr/qualifications/{file["id"]}/share', json={"enabled": True}
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        settings = response.get_json()["data"]
        token = settings["path"].rsplit("/", 1)[1]
        self.assertRegex(token, r"^[A-Za-z0-9_-]{43}$")
        with self.get_db() as conn:
            row = conn.execute(
                "SELECT share_enabled, share_token FROM hr_company_qualifications WHERE id = ?",
                (file["id"],),
            ).fetchone()
            self.assertEqual(tuple(row), (1, token))
        self.user = None
        response = self.client.get(f"/api/hr/qualifications/share/{token}")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(
            response.get_json(), {"success": True, "data": {"title": file["title"], "fields": file["fields"]}}
        )
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        self.assertIn("noindex", response.headers["X-Robots-Tag"])
        self.assertNotIn("Set-Cookie", response.headers)

    def test_disabling_share_revokes_visitors_and_reenabling_preserves_printed_qr(self):
        file = self.create().get_json()["data"]
        path = f'/api/hr/qualifications/{file["id"]}/share'
        enabled = self.client.put(path, json={"enabled": True}).get_json()["data"]
        token = enabled["path"].rsplit("/", 1)[1]
        public_path = f"/api/hr/qualifications/share/{token}"
        admin = self.user
        self.user = None
        self.assertEqual(self.client.get(public_path).status_code, 200)
        self.user = admin
        disabled = self.client.put(path, json={"enabled": False})
        self.assertEqual(disabled.status_code, 200)
        self.assertFalse(disabled.get_json()["data"]["enabled"])
        self.user = None
        response = self.client.get(public_path)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("data", response.get_json())
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.user = admin
        reenabled = self.client.put(path, json={"enabled": True}).get_json()["data"]
        self.assertEqual(reenabled, enabled)
        self.user = None
        self.assertEqual(self.client.get(public_path).status_code, 200)

    def test_share_token_does_not_grant_access_to_admin_data_or_mutations(self):
        file = self.create().get_json()["data"]
        settings = self.client.put(
            f'/api/hr/qualifications/{file["id"]}/share', json={"enabled": True}
        ).get_json()["data"]
        token = settings["path"].rsplit("/", 1)[1]
        self.user = None
        self.assertEqual(self.client.get(f"/api/hr/qualifications/share/{token}").status_code, 200)
        protected_calls = [
            ("get", "/api/hr/qualifications", {}),
            ("get", "/api/hr/qualifications/folders", {}),
            ("get", f'/api/hr/qualifications/{file["id"]}', {}),
            ("get", f'/api/hr/qualifications/{file["id"]}?share_token={token}', {}),
            ("get", f'/api/hr/qualifications/{file["id"]}/share', {}),
            ("put", f'/api/hr/qualifications/{file["id"]}', {"json": self.payload}),
            ("post", "/api/hr/qualifications", {"json": self.payload}),
            ("put", f'/api/hr/qualifications/{file["id"]}/share', {"json": {"enabled": True}}),
        ]
        for method, path, kwargs in protected_calls:
            with self.subTest(method=method, path=path):
                self.assertEqual(getattr(self.client, method)(path, **kwargs).status_code, 401)

    def test_invalid_and_modified_tokens_never_expose_files(self):
        file = self.create().get_json()["data"]
        settings = self.client.put(
            f'/api/hr/qualifications/{file["id"]}/share', json={"enabled": True}
        ).get_json()["data"]
        token = settings["path"].rsplit("/", 1)[1]
        altered = ("A" if token[0] != "A" else "B") + token[1:]
        self.user = None
        for invalid in ("1", str(file["id"]), "not-a-token", "a" * 100, token[:-1], altered, "' OR 1=1 --"):
            with self.subTest(token=invalid):
                response = self.client.get(f"/api/hr/qualifications/share/{invalid}")
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("data", response.get_json())

    def test_share_token_cannot_be_used_to_edit_the_public_document(self):
        file = self.create().get_json()["data"]
        settings = self.client.put(
            f'/api/hr/qualifications/{file["id"]}/share', json={"enabled": True}
        ).get_json()["data"]
        token = settings["path"].rsplit("/", 1)[1]
        self.user = None
        for method in ("put", "post", "delete"):
            response = getattr(self.client, method)(
                f"/api/hr/qualifications/share/{token}", json=self.payload
            )
            self.assertEqual(response.status_code, 405)

    def test_enabled_share_remains_scoped_to_one_file_and_shows_edits(self):
        original = self.create().get_json()["data"]
        private_file = self.create(title="不公开的文件").get_json()["data"]
        share_path = f'/api/hr/qualifications/{original["id"]}/share'
        settings = self.client.put(share_path, json={"enabled": True}).get_json()["data"]
        token = settings["path"].rsplit("/", 1)[1]
        fields = [{"label": "公开更新", "value": "新的内容"}]
        response = self.client.put(
            f'/api/hr/qualifications/{original["id"]}',
            json={**self.payload, "title": "体系认证", "fields": fields},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(share_path).get_json()["data"], settings)
        self.assertEqual(
            self.client.get(f'/api/hr/qualifications/{private_file["id"]}/share').get_json()["data"],
            {"enabled": False, "path": None},
        )
        self.user = None
        response = self.client.get(f"/api/hr/qualifications/share/{token}")
        self.assertEqual(response.get_json()["data"], {"title": "体系认证", "fields": fields})
        self.assertEqual(self.client.get(f'/api/hr/qualifications/{private_file["id"]}').status_code, 401)

    def test_share_settings_validate_booleans_and_missing_files(self):
        file = self.create().get_json()["data"]
        for payload in (None, [], "true", {}, {"enabled": "true"}, {"enabled": 1}, {"enabled": None}):
            with self.subTest(payload=payload):
                response = self.client.put(f'/api/hr/qualifications/{file["id"]}/share', json=payload)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/hr/qualifications/999/share").status_code, 404)
        self.assertEqual(
            self.client.put("/api/hr/qualifications/999/share", json={"enabled": True}).status_code, 404
        )

    def test_share_schema_upgrade_keeps_existing_content_and_starts_disabled(self):
        file = self.create().get_json()["data"]
        with self.get_db() as conn:
            conn.execute("DROP INDEX idx_hr_qualifications_share_token")
            conn.execute("ALTER TABLE hr_company_qualifications DROP COLUMN share_token")
            conn.execute("ALTER TABLE hr_company_qualifications DROP COLUMN share_enabled")
            db_module._hr_qualifications_schema_ready = False
            _ensure_hr_qualifications_schema(conn)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.client.get(f'/api/hr/qualifications/{file["id"]}').get_json()["data"], file)
        self.assertEqual(
            self.client.get(f'/api/hr/qualifications/{file["id"]}/share').get_json()["data"],
            {"enabled": False, "path": None},
        )

    def test_every_endpoint_requires_login_and_admin_permission(self):
        calls = [
            ("get", "/api/hr/qualifications/folders", {}),
            ("post", "/api/hr/qualifications/folders", {"json": {"name": "x"}}),
            ("get", "/api/hr/qualifications", {}),
            ("get", "/api/hr/qualifications/1", {}),
            ("post", "/api/hr/qualifications", {"json": self.payload}),
            ("put", "/api/hr/qualifications/1", {"json": self.payload}),
            ("get", "/api/hr/qualifications/1/share", {}),
            ("put", "/api/hr/qualifications/1/share", {"json": {"enabled": True}}),
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
