"""Company qualification directories and customizable data files."""

import json
import sqlite3

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.permission_catalog import ADMIN_ROUTE_BRANCH_PERMISSIONS


hr_qualifications_bp = Blueprint(
    "hr_qualifications", __name__, url_prefix="/api/hr/qualifications"
)
QUALIFICATION_PERMISSION = ADMIN_ROUTE_BRANCH_PERMISSIONS["hr"]["qualifications"]
FOLDER_NAME_MAX_LENGTH = 100
FILE_TITLE_MAX_LENGTH = 200
FIELD_LABEL_MAX_LENGTH = 100
FIELD_VALUE_MAX_LENGTH = 5000
MAX_FIELDS = 50


def _parse_folder_id(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("请从有效的文件夹内新建文件")
    try:
        folder_id = int(value)
    except (TypeError, ValueError):
        raise ValueError("请从有效的文件夹内新建文件") from None
    if not 0 < folder_id <= 9223372036854775807:
        raise ValueError("请从有效的文件夹内新建文件")
    return folder_id


def _validate_folder_name(data):
    if not isinstance(data, dict):
        raise ValueError("请提交有效的文件夹信息")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("文件夹名称不能为空")
    name = name.strip()
    if len(name) > FOLDER_NAME_MAX_LENGTH:
        raise ValueError("文件夹名称不能超过100个字符")
    return name


def _validate_payload(data):
    if not isinstance(data, dict):
        raise ValueError("请提交有效的资质信息")
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("文件名称不能为空")
    if len(title.strip()) > FILE_TITLE_MAX_LENGTH:
        raise ValueError("文件名称不能超过200个字符")
    fields = data.get("fields")
    if not isinstance(fields, list) or not 1 <= len(fields) <= MAX_FIELDS:
        raise ValueError("请填写1至50个字段")
    normalized_fields = []
    for index, field in enumerate(fields, 1):
        if not isinstance(field, dict):
            raise ValueError(f"第{index}个字段格式无效")
        label, value = field.get("label"), field.get("value")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"第{index}个字段的标题不能为空")
        if len(label.strip()) > FIELD_LABEL_MAX_LENGTH:
            raise ValueError(f"第{index}个字段的标题不能超过100个字符")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"第{index}个字段的内容不能为空")
        if len(value.strip()) > FIELD_VALUE_MAX_LENGTH:
            raise ValueError(f"第{index}个字段的内容不能超过5000个字符")
        normalized_fields.append({"label": label.strip(), "value": value.strip()})
    return {
        "folder_id": _parse_folder_id(data.get("folderId")),
        "title": title.strip(),
        "fields_json": json.dumps(normalized_fields, ensure_ascii=False),
    }


def _serialize(row):
    return {
        "id": row["id"],
        "folderId": row["folder_id"],
        "folderName": row["folder_name"],
        "title": row["title"],
        "fields": json.loads(row["fields_json"]),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _find(conn, qualification_id):
    return conn.execute(
        """
        SELECT q.id, q.folder_id, f.name AS folder_name, q.title, q.fields_json,
               q.created_at, q.updated_at
        FROM hr_company_qualifications AS q
        INNER JOIN hr_qualification_folders AS f ON f.id = q.folder_id
        WHERE q.id = ?
        """,
        (qualification_id,),
    ).fetchone()


def _folder(conn, folder_id):
    return conn.execute(
        "SELECT id, name, created_at, updated_at "
        "FROM hr_qualification_folders WHERE id = ?",
        (folder_id,),
    ).fetchone()


def _serialize_folder(conn, row):
    file_count = conn.execute(
        "SELECT COUNT(*) AS total FROM hr_company_qualifications WHERE folder_id = ?",
        (row["id"],),
    ).fetchone()["total"]
    return {
        "id": row["id"],
        "name": row["name"],
        "fileCount": file_count,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


@hr_qualifications_bp.route("/folders", methods=["GET"])
@require_admin_permission(QUALIFICATION_PERMISSION)
def list_folders():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, created_at, updated_at
            FROM hr_qualification_folders
            ORDER BY name COLLATE NOCASE, id
            """
        ).fetchall()
        data = [_serialize_folder(conn, row) for row in rows]
    return jsonify({"success": True, "data": data})


@hr_qualifications_bp.route("/folders", methods=["POST"])
@require_admin_permission(QUALIFICATION_PERMISSION)
def create_folder():
    try:
        name = _validate_folder_name(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    creator = current_identity()
    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO hr_qualification_folders (name, created_by)
                VALUES (?, ?)
                """,
                (name, creator),
            )
            row = _folder(conn, cursor.lastrowid)
            data = _serialize_folder(conn, row)
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "文件夹名称已存在"}), 409
    return jsonify({"success": True, "message": "文件夹已创建", "data": data}), 201


@hr_qualifications_bp.route("", methods=["GET"])
@require_admin_permission(QUALIFICATION_PERMISSION)
def list_qualifications():
    folder_id = request.args.get("folder_id")
    if folder_id is not None:
        try:
            folder_id = _parse_folder_id(folder_id)
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
    with get_db() as conn:
        if folder_id is not None and not _folder(conn, folder_id):
            return jsonify({"success": False, "message": "文件夹不存在"}), 404
        query = """
            SELECT q.id, q.folder_id, f.name AS folder_name, q.title, q.fields_json,
                   q.created_at, q.updated_at
            FROM hr_company_qualifications AS q
            INNER JOIN hr_qualification_folders AS f ON f.id = q.folder_id
        """
        params = ()
        if folder_id is not None:
            query += " WHERE q.folder_id = ?"
            params = (folder_id,)
        query += " ORDER BY q.id DESC"
        rows = conn.execute(query, params).fetchall()
        data = [_serialize(row) for row in rows]
    return jsonify({"success": True, "data": data})


@hr_qualifications_bp.route("/<int:qualification_id>", methods=["GET"])
@require_admin_permission(QUALIFICATION_PERMISSION)
def get_qualification(qualification_id):
    with get_db() as conn:
        row = _find(conn, qualification_id)
        if not row:
            return jsonify({"success": False, "message": "公司资质不存在"}), 404
        data = _serialize(row)
    return jsonify({"success": True, "data": data})


@hr_qualifications_bp.route("", methods=["POST"])
@require_admin_permission(QUALIFICATION_PERMISSION)
def create_qualification():
    try:
        values = _validate_payload(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    creator = current_identity()
    try:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            folder = _folder(conn, values["folder_id"])
            if not folder:
                return jsonify({"success": False, "message": "所属文件夹不存在"}), 400
            cursor = conn.execute(
                """
                INSERT INTO hr_company_qualifications (folder_id, title, fields_json, created_by)
                VALUES (:folder_id, :title, :fields_json, :created_by)
                """,
                {**values, "created_by": creator},
            )
            data = _serialize(_find(conn, cursor.lastrowid))
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "文件夹已变更，请刷新后重试"}), 409
    return jsonify({"success": True, "message": "公司资质已创建", "data": data}), 201


@hr_qualifications_bp.route("/<int:qualification_id>", methods=["PUT"])
@require_admin_permission(QUALIFICATION_PERMISSION)
def update_qualification(qualification_id):
    try:
        values = _validate_payload(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    try:
        with get_db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if not _find(conn, qualification_id):
                return jsonify({"success": False, "message": "公司资质不存在"}), 404
            folder = _folder(conn, values["folder_id"])
            if not folder:
                return jsonify({"success": False, "message": "所属文件夹不存在"}), 400
            conn.execute(
                """
                UPDATE hr_company_qualifications
                SET folder_id = :folder_id, title = :title, fields_json = :fields_json,
                    updated_at = datetime('now', 'localtime')
                WHERE id = :id
                """,
                {**values, "id": qualification_id},
            )
            data = _serialize(_find(conn, qualification_id))
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "文件夹已变更，请刷新后重试"}), 409
    return jsonify({"success": True, "message": "公司资质已更新", "data": data})
