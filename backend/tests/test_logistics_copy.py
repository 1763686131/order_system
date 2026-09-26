import copy
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from routes.logistics_copy import logistics_copy_bp
from utils import db
from utils.permission_catalog import (
    ADMIN_LOGISTICS_COPY_PERMISSIONS as COPY_PERMISSIONS,
    ADMIN_ROUTE_BRANCH_PERMISSIONS,
    PERMISSION_MODULES,
)


class LogisticsCopySettingsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = patch.object(
            db, "DB_PATH", os.path.join(self.temp_dir.name, "settings.db")
        )
        self.db_path.start()
        self.schema_ready = patch.object(db, "_logistics_copy_schema_ready", False)
        self.schema_ready.start()
        self.auth_schema_ready = patch.object(db, "_auth_schema_ready", False)
        self.auth_schema_ready.start()
        self.user = patch("utils.auth.get_current_user", return_value={
            "id": 1,
            "canAccessAdmin": True,
            "permissions": list(COPY_PERMISSIONS.values()),
        })
        self.user.start()
        self.app = Flask(__name__)
        self.app.register_blueprint(logistics_copy_bp)
        self.client = self.app.test_client()

    def as_permissions(self, *actions, user_id=1, routes=()):
        return patch("utils.auth.get_current_user", return_value={
            "id": user_id,
            "canAccessAdmin": True,
            "permissions": [COPY_PERMISSIONS[action] for action in actions] + list(routes),
        })

    def seed_templates(self):
        config = {
            "fields": [{
                "key": "title", "name": "标题", "template": "@storeName", "enabled": True,
            }],
            "templates": [{
                "id": "template_1", "name": "模板一", "description": "",
                "bindingTarget": "logistics-info", "boundUserIds": [1],
                "fields": [{
                    "key": "custom_editor_content", "name": "内容",
                    "template": "模板一 @allGoods | @allQuantity～kg", "enabled": True,
                }],
            }],
        }
        response = self.client.put('/api/settings/logistics-copy', json=config)
        self.assertEqual(response.status_code, 200, response.json)
        return response.json["data"]

    def tearDown(self):
        self.user.stop()
        self.auth_schema_ready.stop()
        self.schema_ready.stop()
        self.db_path.stop()
        self.temp_dir.cleanup()

    def test_round_trip_and_empty_configuration(self):
        initial = self.client.get('/api/settings/logistics-copy').json['data']
        self.assertIsNone(initial['fields'])
        self.assertIsNone(initial['templates'])
        fields = [
            {"key": "receiver_name", "name": "姓名", "template": "姓名：@receiverName", "enabled": True},
            {"key": "custom_1", "name": "自定义字段", "template": "@allGoods", "enabled": False},
        ]
        templates = [
            {
                "id": "template_1",
                "name": "送货模板",
                "description": "客户送货使用",
                "fields": fields,
            }
        ]
        response = self.client.put(
            '/api/settings/logistics-copy',
            json={"fields": fields, "templates": templates},
        )
        self.assertEqual(response.status_code, 200)
        saved = self.client.get('/api/settings/logistics-copy').json['data']
        self.assertEqual(saved['fields'], [fields[0], {**fields[1], "custom": True}])
        self.assertEqual(saved['templates'][0]['fields'], saved['fields'])
        self.client.put('/api/settings/logistics-copy', json={"fields": []})
        saved_without_templates = self.client.get('/api/settings/logistics-copy').json['data']
        self.assertEqual(saved_without_templates['fields'], [])
        self.assertEqual(len(saved_without_templates['templates']), 1)

    def test_invalid_fields_do_not_overwrite(self):
        fields = [{"key": "title", "name": "标题", "template": "@storeName", "enabled": True}]
        self.client.put('/api/settings/logistics-copy', json={"fields": fields})
        response = self.client.put('/api/settings/logistics-copy', json={"fields": fields * 2})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get('/api/settings/logistics-copy').json['data']['fields'], fields)

    def test_invalid_templates_do_not_overwrite(self):
        fields = [{"key": "title", "name": "标题", "template": "@storeName", "enabled": True}]
        templates = [{
            "id": "template_1",
            "name": "默认模板",
            "description": "",
            "fields": fields,
        }]
        self.client.put(
            '/api/settings/logistics-copy',
            json={"fields": fields, "templates": templates},
        )
        response = self.client.put(
            '/api/settings/logistics-copy',
            json={
                "fields": fields,
                "templates": [{
                    **templates[0],
                    "fields": [{
                        "key": "invalid",
                        "name": "非法",
                        "template": "@storeName",
                        "enabled": True,
                    }],
                }],
            },
        )
        self.assertEqual(response.status_code, 400)
        saved = self.client.get('/api/settings/logistics-copy').json['data']
        self.assertEqual(saved['templates'][0]['fields'], fields)

    def test_template_binding_and_duplicate_binding_validation(self):
        fields = [{"key": "title", "name": "标题", "template": "@storeName", "enabled": True}]
        templates = [
            {
                "id": "logistics_template",
                "name": "物流模板",
                "description": "",
                "bindingTarget": "logistics-info",
                "boundUserIds": [1, 2],
                "fields": fields,
            },
            {
                "id": "order_template",
                "name": "订单模板",
                "description": "",
                "bindingTarget": "order-info",
                "boundUserIds": [1],
                "fields": fields,
            },
        ]
        response = self.client.put(
            '/api/settings/logistics-copy',
            json={"fields": fields, "templates": templates},
        )
        self.assertEqual(response.status_code, 200)
        saved = self.client.get('/api/settings/logistics-copy').json['data']['templates']
        self.assertEqual(saved[0]['bindingTarget'], 'logistics-info')
        self.assertEqual(saved[0]['boundUserIds'], [1, 2])

        duplicate = self.client.put(
            '/api/settings/logistics-copy',
            json={
                "fields": fields,
                "templates": templates + [{
                    "id": "duplicate_template",
                    "name": "重复模板",
                    "description": "",
                    "bindingTarget": "logistics-info",
                    "boundUserIds": [2],
                    "fields": fields,
                }],
            },
        )
        self.assertEqual(duplicate.status_code, 400)

    def test_requires_admin_session(self):
        with patch("utils.auth.get_current_user", return_value=None):
            self.assertEqual(self.client.get('/api/settings/logistics-copy').status_code, 401)
            self.assertEqual(self.client.put('/api/settings/logistics-copy', json={"fields": []}).status_code, 401)
        with patch("utils.auth.get_current_user", return_value={"canAccessAdmin": False}):
            self.assertEqual(self.client.get('/api/settings/logistics-copy').status_code, 403)

    def test_catalog_exposes_all_five_permissions(self):
        module = next(item for item in PERMISSION_MODULES if item["code"] == "admin_logistics_copy")
        self.assertEqual(
            {permission["code"] for permission in module["permissions"]},
            set(COPY_PERMISSIONS.values()),
        )
        self.client.get('/api/settings/logistics-copy')
        with db.get_db() as conn:
            registered = conn.execute(
                "SELECT code FROM permissions WHERE module_code = 'admin_logistics_copy'"
            ).fetchall()
        self.assertEqual({row["code"] for row in registered}, set(COPY_PERMISSIONS.values()))

    def test_entry_and_read_are_both_required(self):
        for actions in [(), ("read",), ("entry",), ("create", "edit", "delete")]:
            with self.subTest(actions=actions), self.as_permissions(*actions):
                self.assertEqual(self.client.get('/api/settings/logistics-copy').status_code, 403)
                self.assertEqual(
                    self.client.put('/api/settings/logistics-copy', json={"fields": []}).status_code,
                    403,
                )
        with self.as_permissions("entry", "read"):
            self.assertEqual(self.client.get('/api/settings/logistics-copy').status_code, 200)
            self.assertEqual(
                self.client.put('/api/settings/logistics-copy', json={"fields": []}).status_code,
                403,
            )

    def test_create_only_preserves_shared_fields_and_existing_templates(self):
        before = self.seed_templates()
        new_template = {**copy.deepcopy(before["templates"][0]),
                        "id": "template_2", "name": "模板二", "boundUserIds": [2]}
        with self.as_permissions("entry", "read", "create"):
            response = self.client.put('/api/settings/logistics-copy', json={
                "templates": before["templates"] + [new_template],
            })
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json["data"]["fields"], before["fields"])
        self.assertEqual(response.json["data"]["templates"][0], before["templates"][0])

    def test_first_template_can_be_created_without_editing_default_fields(self):
        template = {"id": "new", "name": "新模板", "fields": [],
                    "bindingTarget": "order-info", "boundUserIds": [1]}
        with self.as_permissions("entry", "read", "create"):
            response = self.client.put('/api/settings/logistics-copy', json={"templates": [template]})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertIsNone(response.json["data"]["fields"])
        saved = self.client.get('/api/settings/logistics-copy').json["data"]
        self.assertIsNone(saved["fields"])
        self.assertEqual(saved["templates"][0]["id"], "new")

    def test_create_cannot_hide_edits_or_deletes_in_bulk_save(self):
        before = self.seed_templates()
        changed = copy.deepcopy(before["templates"])
        changed[0]["fields"][0]["template"] = "非法编辑"
        added = {**copy.deepcopy(before["templates"][0]), "id": "new", "boundUserIds": [2]}
        for payload, required in [
            ({"templates": changed + [added]}, "edit"),
            ({"templates": [added]}, "delete"),
            ({"fields": [], "templates": before["templates"] + [added]}, "edit"),
        ]:
            with self.subTest(required=required), self.as_permissions("entry", "read", "create"):
                response = self.client.put('/api/settings/logistics-copy', json=payload)
                self.assertEqual(response.status_code, 403, response.json)
                self.assertEqual(response.json["permission"], COPY_PERMISSIONS[required])
            after = self.client.get('/api/settings/logistics-copy').json["data"]
            self.assertEqual(after["fields"], before["fields"])
            self.assertEqual(after["templates"], before["templates"])

    def test_edit_only_can_change_content_and_bindings_but_not_add_or_delete(self):
        before = self.seed_templates()
        changed = copy.deepcopy(before["templates"])
        changed[0]["fields"][0]["template"] = "修改后 @allGoods"
        changed[0]["bindingTarget"] = "order-info"
        changed[0]["boundUserIds"] = [2, 3]
        with self.as_permissions("entry", "read", "edit"):
            response = self.client.put('/api/settings/logistics-copy', json={"templates": changed})
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json["data"]["templates"], changed)
            self.assertEqual(
                self.client.put('/api/settings/logistics-copy', json={"templates": []}).status_code,
                403,
            )
            new = {**changed[0], "id": "new", "boundUserIds": [4]}
            self.assertEqual(self.client.put(
                '/api/settings/logistics-copy', json={"templates": changed + [new]}
            ).status_code, 403)
            self.assertEqual(
                self.client.put('/api/settings/logistics-copy', json={"fields": []}).status_code,
                200,
            )

    def test_delete_only_cannot_update_other_data(self):
        before = self.seed_templates()
        with self.as_permissions("entry", "read", "delete"):
            forbidden = self.client.put('/api/settings/logistics-copy', json={
                "templates": [], "fields": [],
            })
            self.assertEqual(forbidden.status_code, 403)
            response = self.client.put('/api/settings/logistics-copy', json={"templates": []})
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json["data"]["fields"], before["fields"])
            self.assertEqual(response.json["data"]["templates"], [])

    def test_super_admin_bypasses_explicit_permissions(self):
        with patch("utils.auth.get_current_user", return_value={
            "id": 1, "canAccessAdmin": True, "isSuperAdmin": True,
        }):
            self.assertEqual(self.client.get('/api/settings/logistics-copy').status_code, 200)
            self.assertEqual(
                self.client.put('/api/settings/logistics-copy', json={"fields": []}).status_code,
                200,
            )

    def test_resolve_uses_session_user_and_never_returns_management_data(self):
        before = self.seed_templates()
        route = ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["logistics"]
        with self.as_permissions(user_id=1, routes=[route]):
            self.assertEqual(self.client.get('/api/settings/logistics-copy').status_code, 403)
            response = self.client.get('/api/settings/logistics-copy/resolve?target=logistics-info&userId=2')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["data"]["fields"], before["templates"][0]["fields"])
            self.assertEqual(set(response.json["data"]), {"fields", "updatedAt"})
            other_target = self.client.get('/api/settings/logistics-copy/resolve?target=order-info')
            self.assertEqual(other_target.status_code, 403)
            self.assertEqual(
                other_target.json["permission"],
                ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["orders"],
            )
        with self.as_permissions(user_id=2, routes=[route]):
            response = self.client.get('/api/settings/logistics-copy/resolve?target=logistics-info&userId=1')
            self.assertEqual(response.json["data"]["fields"], before["fields"])

    def test_resolve_validates_target_routes_and_empty_configuration(self):
        for target in ("logistics-info", "order-info"):
            with self.as_permissions():
                response = self.client.get(f'/api/settings/logistics-copy/resolve?target={target}')
                self.assertEqual(response.status_code, 403)
        with patch("utils.auth.get_current_user", return_value=None):
            self.assertEqual(self.client.get(
                '/api/settings/logistics-copy/resolve?target=logistics-info'
            ).status_code, 401)
        route = ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["orders"]
        with self.as_permissions(routes=[route]):
            self.assertEqual(self.client.get(
                '/api/settings/logistics-copy/resolve?target=invalid'
            ).status_code, 400)
            self.assertIsNone(self.client.get(
                '/api/settings/logistics-copy/resolve?target=order-info'
            ).json["data"]["fields"])
            self.assertEqual(self.client.get(
                '/api/settings/logistics-copy/resolve?target=logistics-info'
            ).status_code, 403)
        self.client.put('/api/settings/logistics-copy', json={
            "templates": [{"id": "empty", "name": "空模板", "fields": [],
                           "bindingTarget": "order-info", "boundUserIds": [1]}],
        })
        with self.as_permissions(routes=[route]):
            self.assertEqual(self.client.get(
                '/api/settings/logistics-copy/resolve?target=order-info'
            ).json["data"]["fields"], [])


if __name__ == '__main__':
    unittest.main()
