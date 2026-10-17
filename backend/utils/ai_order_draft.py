"""Structured order-draft extraction for the GuGu admin assistant."""

import json
import math
import re

from utils import ai_client


ORDER_DRAFT_MAX_LENGTH = 4000
ORDER_DRAFT_SYSTEM_PROMPT = """
你是订单录入助手，只负责把用户提供的散乱下单文字整理成新增销售订单草稿。
不要创建、修改或提交订单，不要调用工具，不要补猜用户没有明确提供的信息。
只返回一个合法 JSON 对象，不要 Markdown，不要解释，不要代码块。

输出字段必须严格使用以下结构：
{
  "customerName": "",
  "contactPerson": "",
  "contactPhone": "",
  "contactAddress": "",
  "projectName": "",
  "remark": "",
  "items": [
    {
      "name": "",
      "spec": "",
      "unit": "",
      "quantity": null,
      "packages": null,
      "notes": ""
    }
  ]
}

规则：
1. name 是商品大类或商品名称；spec 是明确写出的型号、规格、等级或属性，不能根据常识猜测。
2. quantity 是商品数量，例如“1500公斤”应为 1500，unit 应为“公斤”。
3. packages 只填写明确出现的件、桶、箱、包、套等包装件数。只有数量没有件数时必须为 null，不能把数量当成件数。
4. 如果文本提到客户简称、口语称呼或客户全称，把原文中用于指代客户的称呼原样填入 customerName；不要因为不是完整工商名称就留空。收货人、联系人、电话和地址分别填到最合适的字段；无法确定的字段留空。
5. 一种商品一行。没有识别到商品时，items 必须为空数组。
6. 所有 null、数字和字符串都必须符合 JSON 语法，禁止 NaN、Infinity 和额外字段。最多整理 30 行明细，超出时不要合并或省略商品。
"""


def _clean_text(value, limit=240):
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return value.strip()[:limit]


def _number(value):
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return int(number) if number.is_integer() else number


def _extract_json(content):
    text = str(content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI 没有返回有效的订单草稿 JSON")
    return json.loads(text[start:end + 1])


def normalize_order_draft(document):
    if not isinstance(document, dict):
        raise ValueError("AI 返回的订单草稿格式不正确")

    raw_items = document.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("AI 返回的订单明细格式不正确")
    if len(raw_items) > 30:
        raise ValueError("一次最多整理 30 行商品明细，请拆分下单内容")

    items = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError("AI 返回的订单明细格式不正确，请重新分析")
        name = _clean_text(raw_item.get("name"), 160)
        if not name:
            raise ValueError("有商品缺少名称，请补充下单内容后重新分析")
        quantity = _number(raw_item.get("quantity"))
        packages = _number(raw_item.get("packages"))
        items.append({
            "name": name,
            "spec": _clean_text(raw_item.get("spec"), 160),
            "unit": _clean_text(raw_item.get("unit"), 40),
            "quantity": quantity,
            "packages": packages,
            "notes": _clean_text(raw_item.get("notes"), 300),
        })

    if not items:
        raise ValueError("没有识别到可用的商品明细，请补充商品名称和数量")

    return {
        "customerName": _clean_text(document.get("customerName")),
        "contactPerson": _clean_text(document.get("contactPerson"), 80),
        "contactPhone": _clean_text(document.get("contactPhone"), 80),
        "contactAddress": _clean_text(document.get("contactAddress"), 500),
        "projectName": _clean_text(document.get("projectName"), 160),
        "remark": _clean_text(document.get("remark"), 500),
        "items": items,
    }


def parse_order_draft(config, api_key, text):
    source = _clean_text(text, ORDER_DRAFT_MAX_LENGTH)
    if not source:
        raise ValueError("请输入客户下单内容")
    result = ai_client.chat(
        config,
        api_key,
        [{"role": "user", "content": source}],
        max_tokens=1800,
        system_prompt=ORDER_DRAFT_SYSTEM_PROMPT,
    )
    try:
        if result.get("truncated"):
            raise ValueError("AI 返回的订单内容不完整，请缩短下单内容后重试")
        document = _extract_json(result.get("content"))
        draft = normalize_order_draft(document)
    except (TypeError, ValueError) as error:
        raise ai_client.AIProviderError(
            f"订单草稿解析失败：{error}",
            "invalid_order_draft",
            502,
        ) from error
    return {
        "draft": draft,
        "model": result.get("model", config.get("model", "")),
        "truncated": bool(result.get("truncated")),
    }
