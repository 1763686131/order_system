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


def _parse_json_array(value, fallback=None):
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback if fallback is not None else []
    return parsed if isinstance(parsed, list) else (fallback if fallback is not None else [])


def _normalize_fields(fields):
    if not isinstance(fields, list) or len(fields) > 100:
        return None, "字段列表格式不正确或超过100项"

    normalized = []
    seen = set()
    for field in fields:
        if not isinstance(field, dict):
            return None, "字段格式不正确"
        key = field.get("key")
        name = field.get("name")
        template = field.get("template")
        enabled = field.get("enabled")
        is_custom = isinstance(key, str) and key.startswith("custom_")
        if (
            not isinstance(key, str)
            or (key not in BUILTIN_KEYS and not (
                is_custom and len(key) <= 80
                and all(char.isascii() and (char.isalnum() or char == "_") for char in key)
            ))
            or key in seen
            or not isinstance(name, str) or len(name) > 80
            or not isinstance(template, str) or len(template) > 4000
            or not isinstance(enabled, bool)
        ):
            return None, "字段内容不正确或存在重复键"
        seen.add(key)
        normalized.append({
            "key": key,
            "name": name,
            "template": template,
            "enabled": enabled,
            **({"custom": True} if is_custom else {}),
        })
    return normalized, None


def _normalize_templates(templates):
    if not isinstance(templates, list) or len(templates) > 100:
        return None, "模板列表格式不正确或超过100项"

    normalized = []
    seen = set()
    for template in templates:
        if not isinstance(template, dict):
            return None, "模板格式不正确"
        template_id = template.get("id")
        name = template.get("name")
        description = template.get("description", "")
        fields, error = _normalize_fields(template.get("fields"))
        if (
            not isinstance(template_id, str)
            or not template_id
            or len(template_id) > 80
            or not all(
                char.isascii() and (char.isalnum() or char in "_-")
                for char in template_id
            )
            or template_id in seen
            or not isinstance(name, str)
            or not name.strip()
            or len(name) > 80
            or not isinstance(description, str)
            or len(description) > 240
            or error
        ):
            return None, error or "模板内容不正确或存在重复编号"
        seen.add(template_id)
        normalized.append({
            "id": template_id,
            "name": name.strip(),
            "description": description.strip(),
            "fields": fields,
        })
    return normalized, None


@logistics_copy_bp.route("", methods=["GET"])
@require_admin_access
def get_logistics_copy_settings():
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT fields_json, templates_json, updated_at
            FROM logistics_copy_settings
            WHERE id = 1
            """
        ).fetchone()
    return jsonify({
        "success": True,
        "data": {
            "fields": _parse_json_array(row["fields_json"]) if row else None,
            "templates": (
                _parse_json_array(row["templates_json"])
                if row and row["templates_json"] is not None
                else None
            ),
            "updatedAt": row["updated_at"] if row else None,
        },
    })


@logistics_copy_bp.route("", methods=["PUT"])
@require_admin_access
def save_logistics_copy_settings():
    body = request.get_json(silent=True)
    fields = body.get("fields") if isinstance(body, dict) else None
    normalized, error = _normalize_fields(fields)
    if error:
        return jsonify({"success": False, "message": error}), 400

    templates_provided = isinstance(body, dict) and "templates" in body
    normalized_templates = None
    if templates_provided:
        normalized_templates, error = _normalize_templates(body.get("templates"))
        if error:
            return jsonify({"success": False, "message": error}), 400

    with get_db() as conn:
        existing = conn.execute(
            "SELECT templates_json FROM logistics_copy_settings WHERE id = 1"
        ).fetchone()
        if normalized_templates is None:
            normalized_templates = _parse_json_array(
                existing["templates_json"] if existing and existing["templates_json"] is not None else None,
                [],
            )
        conn.execute(
            """
            INSERT INTO logistics_copy_settings (
                id, fields_json, templates_json, updated_at
            )
            VALUES (1, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                fields_json = excluded.fields_json,
                templates_json = excluded.templates_json,
                updated_at = excluded.updated_at
            """,
            (
                json.dumps(normalized, ensure_ascii=False),
                json.dumps(normalized_templates, ensure_ascii=False),
            ),
        )
        row = conn.execute(
            """
            SELECT fields_json, templates_json, updated_at
            FROM logistics_copy_settings
            WHERE id = 1
            """
        ).fetchone()
    return jsonify({
        "success": True,
        "message": "复制字段设置已保存",
        "data": {
            "fields": _parse_json_array(row["fields_json"]),
            "templates": _parse_json_array(row["templates_json"]),
            "updatedAt": row["updated_at"],
        },
    })
