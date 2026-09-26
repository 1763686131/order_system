"""Shared logistics copy field configuration."""

import json

from flask import Blueprint, jsonify, request

from utils.auth import require_admin_access
from utils.db import get_db


logistics_copy_bp = Blueprint(
    "logistics_copy", __name__, url_prefix="/api/settings/logistics-copy"
)

BUILTIN_KEYS = {
    "title", "receiver_name", "receiver_phone", "receiver_address",
    "goods_name", "goods_weight", "goods_quantity", "goods_packaging",
    "logistics_service", "remark",
}


@logistics_copy_bp.route("", methods=["GET"])
@require_admin_access
def get_logistics_copy_settings():
    with get_db() as conn:
        row = conn.execute(
            "SELECT fields_json, updated_at FROM logistics_copy_settings WHERE id = 1"
        ).fetchone()
    return jsonify({
        "success": True,
        "data": {
            "fields": json.loads(row["fields_json"]) if row else None,
            "updatedAt": row["updated_at"] if row else None,
        },
    })


@logistics_copy_bp.route("", methods=["PUT"])
@require_admin_access
def save_logistics_copy_settings():
    body = request.get_json(silent=True)
    fields = body.get("fields") if isinstance(body, dict) else None
    if not isinstance(fields, list) or len(fields) > 100:
        return jsonify({"success": False, "message": "字段列表格式不正确或超过100项"}), 400

    normalized = []
    seen = set()
    for field in fields:
        if not isinstance(field, dict):
            return jsonify({"success": False, "message": "字段格式不正确"}), 400
        key = field.get("key")
        name = field.get("name")
        template = field.get("template")
        enabled = field.get("enabled")
        if (
            not isinstance(key, str)
            or (key not in BUILTIN_KEYS and not (
                key.startswith("custom_") and len(key) <= 80
                and all(char.isascii() and (char.isalnum() or char == "_") for char in key)
            ))
            or key in seen
            or not isinstance(name, str) or len(name) > 80
            or not isinstance(template, str) or len(template) > 4000
            or not isinstance(enabled, bool)
        ):
            return jsonify({"success": False, "message": "字段内容不正确或存在重复键"}), 400
        seen.add(key)
        normalized.append({
            "key": key,
            "name": name,
            "template": template,
            "enabled": enabled,
            **({"custom": True} if key.startswith("custom_") else {}),
        })

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO logistics_copy_settings (id, fields_json, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                fields_json = excluded.fields_json,
                updated_at = excluded.updated_at
            """,
            (json.dumps(normalized, ensure_ascii=False),),
        )
        row = conn.execute(
            "SELECT updated_at FROM logistics_copy_settings WHERE id = 1"
        ).fetchone()
    return jsonify({
        "success": True,
        "message": "复制字段设置已保存",
        "data": {"fields": normalized, "updatedAt": row["updated_at"]},
    })
