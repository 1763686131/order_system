import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from routes.logistics_copy import logistics_copy_bp
from utils import db


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
            "id": 1, "canAccessAdmin": True
        })
        self.user.start()
        self.app = Flask(__name__)
        self.app.register_blueprint(logistics_copy_bp)
        self.client = self.app.test_client()

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


if __name__ == '__main__':
    unittest.main()
