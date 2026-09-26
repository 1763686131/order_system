"""Shared logistics copy field configuration."""

import json

from flask import Blueprint, jsonify, request

from utils import auth
from utils.db import get_db
from utils.permission_catalog import (
    ADMIN_LOGISTICS_COPY_PERMISSIONS as COPY_PERMISSIONS,
    ADMIN_ROUTE_BRANCH_PERMISSIONS,
)


logistics_copy_bp = Blueprint(
    "logistics_copy", __name__, url_prefix="/api/settings/logistics-copy"
)

BUILTIN_KEYS = {
    "title", "receiver_name", "receiver_phone", "receiver_address",
    "goods_name", "goods_weight", "goods_quantity", "goods_packaging",
    "logistics_service", "remark",
}
COPY_BINDING_TARGETS = {
    "logistics-info",
    "order-info",
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
        binding_target = template.get("bindingTarget", "")
        bound_user_ids = template.get("boundUserIds", [])
        fields, error = _normalize_fields(template.get("fields"))
        normalized_user_ids = []
        if isinstance(bound_user_ids, list) and len(bound_user_ids) <= 100:
            for user_id in bound_user_ids:
                if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
                    error = "模板绑定人信息不正确"
                    break
                if user_id not in normalized_user_ids:
                    normalized_user_ids.append(user_id)
        else:
            error = "模板绑定人信息不正确"
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
            or binding_target not in ("", *COPY_BINDING_TARGETS)
            or error
        ):
            return None, error or "模板内容不正确或存在重复编号"
        seen.add(template_id)
        normalized.append({
            "id": template_id,
            "name": name.strip(),
            "description": description.strip(),
            "bindingTarget": binding_target,
            "boundUserIds": normalized_user_ids,
            "fields": fields,
        })

    binding_pairs = set()
    for template in normalized:
        for user_id in template["boundUserIds"]:
            pair = (template["bindingTarget"], user_id)
            if not template["bindingTarget"] or pair in binding_pairs:
                if pair in binding_pairs:
                    return None, "同一个账号在同一个复制按钮上只能绑定一个模板"
                continue
            binding_pairs.add(pair)
    return normalized, None


def _stored_fields(row):
    if not row or row["fields_json"] == "null":
        return None
    return _parse_json_array(row["fields_json"])


def _template_content(template):
    return {**template, "boundUserIds": sorted(template["boundUserIds"])}


@logistics_copy_bp.route("", methods=["GET"])
@auth.require_admin_permission(COPY_PERMISSIONS["entry"])
@auth.require_admin_permission(COPY_PERMISSIONS["read"])
def get_logistics_copy_settings():
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT fields_json, templates_json, updated_at
            FROM logistics_copy_settings
            WHERE id = 1
            """
        ).fetchone()
        binding_users = conn.execute(
            """
            SELECT users.id, users.display_name, users.username, users.avatar_url,
                   employees.display_name AS employee_name
            FROM users
            LEFT JOIN employees ON employees.user_id = users.id
            WHERE users.status = 'active'
            ORDER BY COALESCE(NULLIF(employees.display_name, ''), users.display_name), users.id
            """
        ).fetchall()
    return jsonify({
        "success": True,
        "data": {
            "fields": _stored_fields(row),
            "templates": (
                _parse_json_array(row["templates_json"])
                if row and row["templates_json"] is not None
                else None
            ),
            "updatedAt": row["updated_at"] if row else None,
            "bindingUsers": [
                {
                    "id": user["id"],
                    "name": user["employee_name"] or user["display_name"] or user["username"],
                    "username": user["username"],
                    "avatarUrl": user["avatar_url"] or "",
                }
                for user in binding_users
            ],
        },
    })


@logistics_copy_bp.route("/resolve", methods=["GET"])
@auth.require_admin_access
def resolve_logistics_copy_settings():
    target = request.args.get("target")
    if target not in COPY_BINDING_TARGETS:
        return jsonify({"success": False, "message": "复制入口不正确"}), 400

    route_code = ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"][
        "orders" if target == "order-info" else "logistics"
    ]
    if not auth.admin_permission_granted(route_code):
        return jsonify({
            "success": False,
            "message": "当前账号没有执行此操作的权限",
            "permission": route_code,
        }), 403

    user_id = auth.get_current_user()["id"]
    with get_db() as conn:
        row = conn.execute(
            "SELECT fields_json, templates_json, updated_at FROM logistics_copy_settings WHERE id = 1"
        ).fetchone()
    fields = _stored_fields(row)
    templates = _parse_json_array(row["templates_json"]) if row else []
    for template in templates:
        if (
            template.get("bindingTarget") == target
            and user_id in template.get("boundUserIds", [])
        ):
            fields = template["fields"]
            break
    return jsonify({
        "success": True,
        "data": {
            "fields": fields,
            "updatedAt": row["updated_at"] if row else None,
        },
    })


@logistics_copy_bp.route("", methods=["PUT"])
@auth.require_admin_permission(COPY_PERMISSIONS["entry"])
@auth.require_admin_permission(COPY_PERMISSIONS["read"])
@auth.require_any_admin_permission(
    COPY_PERMISSIONS["create"], COPY_PERMISSIONS["edit"], COPY_PERMISSIONS["delete"]
)
def save_logistics_copy_settings():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not ({"fields", "templates"} & body.keys()):
        return jsonify({"success": False, "message": "请提交字段配置或模板列表"}), 400
    fields_provided = "fields" in body
    normalized = None
    if fields_provided:
        normalized, error = _normalize_fields(body["fields"])
        if error:
            return jsonify({"success": False, "message": error}), 400

    templates_provided = "templates" in body
    normalized_templates = None
    if templates_provided:
        normalized_templates, error = _normalize_templates(body.get("templates"))
        if error:
            return jsonify({"success": False, "message": error}), 400

    with get_db() as conn:
        # Check changes and save under the same lock so permissions use the latest state.
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT fields_json, templates_json FROM logistics_copy_settings WHERE id = 1"
        ).fetchone()
        existing_fields = _stored_fields(existing)
        existing_templates, error = _normalize_templates(
            _parse_json_array(existing["templates_json"]) if existing else []
        )
        if error:
            return jsonify({"success": False, "message": "已存模板格式错误，请联系管理员"}), 500
        if not fields_provided:
            normalized = existing_fields
        if normalized_templates is None:
            normalized_templates = existing_templates

        old_templates = {item["id"]: item for item in existing_templates}
        new_templates = {item["id"]: item for item in normalized_templates}
        required_actions = []
        if new_templates.keys() - old_templates.keys():
            required_actions.append("create")
        if old_templates.keys() - new_templates.keys():
            required_actions.append("delete")
        if normalized != existing_fields or any(
            _template_content(new_templates[key]) != _template_content(old_templates[key])
            for key in old_templates.keys() & new_templates.keys()
        ):
            required_actions.append("edit")
        for action in required_actions:
            permission = COPY_PERMISSIONS[action]
            if not auth.admin_permission_granted(permission):
                return jsonify({
                    "success": False,
                    "message": "当前账号没有执行此操作的权限",
                    "permission": permission,
                }), 403

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
            "fields": _stored_fields(row),
            "templates": _parse_json_array(row["templates_json"]),
            "updatedAt": row["updated_at"],
        },
    })
