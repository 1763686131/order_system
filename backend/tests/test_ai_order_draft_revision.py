import json
import unittest
from unittest.mock import patch

from utils import ai_client, ai_order_draft


class OrderDraftRevisionTests(unittest.TestCase):
    def setUp(self):
        self.draft = {
            "storeName": "A门店",
            "warehouseName": "A仓库",
            "customerName": "客户甲",
            "contactPerson": "张三",
            "contactPhone": "13800000000",
            "contactAddress": "浙江省杭州市",
            "projectName": "项目",
            "orderRemark": "旧备注",
            "items": [{
                "label": "胶 · 20kg/件",
                "packages": 50,
                "quantity": 1000,
                "unit": "公斤",
                "remark": "明细备注",
                "packageConversions": [{"unit": "件", "rate": 20}],
            }],
        }

    def test_revision_sends_current_draft_and_recent_context(self):
        messages = [
            {"role": "user", "content": "收货地址要修改一下"},
            {"role": "assistant", "content": "请告诉我新的收货地址"},
            {"role": "user", "content": "北京市"},
        ]
        content = json.dumps({
            "reply": "已更新收货地址并清空备注。",
            "updates": [
                {"field": "contactAddress", "value": "北京市"},
                {"field": "orderRemark", "value": ""},
                {"itemIndex": 0, "field": "quantity", "value": 800},
            ],
        }, ensure_ascii=False)
        with patch.object(
            ai_client,
            "chat",
            return_value={
                "content": content,
                "model": "test-model",
                "truncated": False,
            },
        ) as chat:
            result = ai_order_draft.revise_order_draft(
                {"model": "test-model"}, "secret", self.draft, messages
            )

        self.assertEqual(result["updates"][1]["value"], "")
        self.assertEqual(result["updates"][2]["value"], 800)
        request = json.loads(chat.call_args.args[2][0]["content"])
        self.assertEqual(request["recentConversation"], messages)
        self.assertEqual(
            request["currentDraft"]["items"][0]["packageConversions"],
            [{"unit": "件", "rate": 20}],
        )

    def test_revision_can_ask_for_missing_value_without_updates(self):
        content = json.dumps({
            "reply": "请告诉我新的收货地址。",
            "updates": [],
        }, ensure_ascii=False)
        with patch.object(
            ai_client,
            "chat",
            return_value={
                "content": content,
                "model": "test-model",
                "truncated": False,
            },
        ):
            result = ai_order_draft.revise_order_draft(
                {"model": "test-model"},
                "secret",
                self.draft,
                [{"role": "user", "content": "收货地址要修改一下"}],
            )
        self.assertEqual(result["updates"], [])
        self.assertIn("新的收货地址", result["reply"])

    def test_revision_rejects_unsafe_or_invalid_updates(self):
        invalid_documents = [
            {"reply": "ok", "updates": [{"field": "customerId", "value": 99}]},
            {"reply": "ok", "updates": [{"itemIndex": 0, "field": "quantity", "value": 0}]},
            {
                "reply": "ok",
                "updates": [
                    {"field": "orderRemark", "value": ""},
                    {"field": "orderRemark", "value": "重复修改"},
                ],
            },
            {
                "reply": "ok",
                "updates": [{"field": "contactAddress", "value": "北京市", "customerId": 99}],
            },
            {
                "reply": "ok",
                "updates": [{"itemIndex": 1, "field": "packages", "value": 4}],
            },
        ]
        for document in invalid_documents:
            with self.subTest(document=document):
                with self.assertRaises(ValueError):
                    ai_order_draft.normalize_revision_result(document, 1)


if __name__ == "__main__":
    unittest.main()
