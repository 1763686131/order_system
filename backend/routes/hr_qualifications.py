"""Company qualification directories and certificate files."""

from datetime import date
import sqlite3

from flask import Blueprint, jsonify, request

from utils.auth import current_identity, require_admin_permission
from utils.db import get_db
from utils.permission_catalog import ADMIN_ROUTE_BRANCH_PERMISSIONS


hr_qualifications_bp = Blueprint(
    "hr_qualifications", __name__, url_prefix="/api/hr/qualifications"
)
QUALIFICATION_PERMISSION = ADMIN_ROUTE_BRANCH_PERMISSIONS["hr"]["qualifications"]
CERTIFICATE_STATUSES = {"有效", "暂停", "撤销", "注销", "过期"}
FIELDS = {
    "certificateNo": ("certificate_no", "证书编号", 100),
    "companyName": ("company_name", "中文名称", 200),
    "certificationBasis": ("certification_basis", "认证依据", 500),
    "registeredAddress": ("registered_address", "注册地址", 1000),
    "auditAddress": ("audit_address", "审核地址", 1000),
    "certificationScope": ("certification_scope", "认证范围", 5000),
    "issueDate": ("issue_date", "发证日期", 10),
    "validUntil": ("valid_until", "有效日期", 10),
    "certificateStatus": ("certificate_status", "证书状态", 20),
}
FOLDER_NAME_MAX_LENGTH = 100


def _parse_folder_id(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("请选择有效的所属文件夹")
    try:
        folder_id = int(value)
    except (TypeError, ValueError):
        raise ValueError("请选择有效的所属文件夹") from None
    if not 0 < folder_id <= 9223372036854775807:
        raise ValueError("请选择有效的所属文件夹")
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
    values = {}
    values["folder_id"] = _parse_folder_id(data.get("folderId"))
    for key, (column, label, max_length) in FIELDS.items():
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label}不能为空")
        value = value.strip()
        if len(value) > max_length:
            raise ValueError(f"{label}不能超过{max_length}个字符")
        values[column] = value
    for column, label in (("issue_date", "发证日期"), ("valid_until", "有效日期")):
        try:
            parsed = date.fromisoformat(values[column])
            if parsed.isoformat() != values[column]:
                raise ValueError
        except ValueError:
            raise ValueError(f"{label}格式无效，请使用YYYY-MM-DD") from None
    if values["valid_until"] < values["issue_date"]:
        raise ValueError("有效日期不能早于发证日期")
    if values["certificate_status"] not in CERTIFICATE_STATUSES:
        raise ValueError("证书状态无效")
    return values


def _serialize(row):
    return {
        "id": row["id"],
        "folderId": row["folder_id"],
        "folderName": row["folder_name"],
        **{key: row[column] for key, (column, _, _) in FIELDS.items()},
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _find(conn, qualification_id):
    return conn.execute(
        """
        SELECT q.id, q.folder_id, f.name AS folder_name,
               q.certificate_no, q.company_name, q.certification_basis,
               q.registered_address, q.audit_address, q.certification_scope,
               q.issue_date, q.valid_until, q.certificate_status,
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
            SELECT q.id, q.folder_id, f.name AS folder_name,
                   q.certificate_no, q.company_name, q.certification_basis,
                   q.registered_address, q.audit_address, q.certification_scope,
                   q.issue_date, q.valid_until, q.certificate_status,
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
                INSERT INTO hr_company_qualifications (
                    folder_id, folder_name, certificate_no, company_name, certification_basis,
                    registered_address, audit_address, certification_scope,
                    issue_date, valid_until, certificate_status, created_by
                ) VALUES (
                    :folder_id, :folder_name, :certificate_no, :company_name, :certification_basis,
                    :registered_address, :audit_address, :certification_scope,
                    :issue_date, :valid_until, :certificate_status, :created_by
                )
                """,
                {**values, "folder_name": folder["name"], "created_by": creator},
            )
            data = _serialize(_find(conn, cursor.lastrowid))
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "证书编号已存在，请勿重复录入"}), 409
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
                SET folder_id = :folder_id, folder_name = :folder_name,
                    certificate_no = :certificate_no,
                    company_name = :company_name, certification_basis = :certification_basis,
                    registered_address = :registered_address, audit_address = :audit_address,
                    certification_scope = :certification_scope, issue_date = :issue_date,
                    valid_until = :valid_until, certificate_status = :certificate_status,
                    updated_at = datetime('now', 'localtime')
                WHERE id = :id
                """,
                {**values, "folder_name": folder["name"], "id": qualification_id},
            )
            data = _serialize(_find(conn, qualification_id))
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "证书编号已存在，请勿重复录入"}), 409
    return jsonify({"success": True, "message": "公司资质已更新", "data": data})
