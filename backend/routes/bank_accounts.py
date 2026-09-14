"""银行账户 CRUD、结算账户选项与银行卡图片上传接口。"""

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os
import threading
import uuid

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from utils.db import get_db
from utils.system_settings import (
    DEFAULT_BANK_CARD_BG_PATH,
    DEFAULT_BANK_ICON_PATH,
    get_setting,
    normalize_server_path,
)


bank_accounts_bp = Blueprint(
    "bank_accounts",
    __name__,
    url_prefix="/api/bank-accounts",
)

upload_bp = Blueprint("bank_account_upload", __name__, url_prefix="/api/upload")

MONEY_QUANT = Decimal("0.01")
_write_lock = threading.Lock()
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
UPLOAD_TYPES = {
    "background": {
        "setting_key": "bank_cards.bg_path",
        "default_path": DEFAULT_BANK_CARD_BG_PATH,
        "url_prefix": "/uploads/bank-cards/backgrounds",
        "file_prefix": "bank_card_bg",
        "max_size": 5 * 1024 * 1024,
    },
    "icon": {
        "setting_key": "bank_cards.icon_path",
        "default_path": DEFAULT_BANK_ICON_PATH,
        "url_prefix": "/uploads/bank-cards/icons",
        "file_prefix": "bank_icon",
        "max_size": 2 * 1024 * 1024,
    },
}


def _money(value, field_name="账户余额"):
    try:
        amount = Decimal(str(value if value not in (None, "") else 0))
        if not amount.is_finite():
            raise InvalidOperation
        return amount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name}必须是有效数字")


def _text(value, max_length=200):
    return str(value or "").strip()[:max_length]


def _payload_value(data, camel, snake, default=None):
    if camel in data:
        return data.get(camel)
    if snake in data:
        return data.get(snake)
    return default


def _serialize(row):
    if not row:
        return None
    item = dict(row)
    return {
        "id": item["id"],
        "storeId": item.get("store_id"),
        "storeName": item.get("store_name") or "",
        "accountName": item.get("account_name") or "",
        "accountNumber": item.get("account_number") or "",
        "bankName": item.get("bank_name") or "",
        "bankCode": item.get("bank_code") or "",
        "balance": round(float(item.get("balance") or 0), 2),
        "cardColor": item.get("card_color") or "#1a1a1a",
        "cardBgImage": item.get("card_bg_image") or "",
        "bankIcon": item.get("bank_icon") or "",
        "createdAt": item.get("created_at") or "",
        "updatedAt": item.get("updated_at") or "",
    }


def _account_row(conn, account_id):
    return conn.execute(
        """
        SELECT a.*, s.name AS store_name
        FROM bank_accounts a
        LEFT JOIN stores s ON s.id = a.store_id
        WHERE a.id = ?
        """,
        (account_id,),
    ).fetchone()


def _validate_payload(conn, data, existing=None):
    store_value = _payload_value(
        data,
        "storeId",
        "store_id",
        existing["store_id"] if existing else None,
    )
    try:
        store_id = int(store_value)
    except (TypeError, ValueError):
        raise ValueError("请选择所属门店")

    store = conn.execute(
        "SELECT id, name, status FROM stores WHERE id = ?",
        (store_id,),
    ).fetchone()
    if not store:
        raise ValueError("所选门店不存在")
    if str(store["status"] or "active") == "inactive":
        raise ValueError("所选门店已停用")

    account_name = _text(
        _payload_value(
            data,
            "accountName",
            "account_name",
            existing["account_name"] if existing else "",
        ),
        120,
    )
    account_number = _text(
        _payload_value(
            data,
            "accountNumber",
            "account_number",
            existing["account_number"] if existing else "",
        ),
        80,
    )
    bank_name = _text(
        _payload_value(
            data,
            "bankName",
            "bank_name",
            existing["bank_name"] if existing else "",
        ),
        160,
    )
    if not account_name or not account_number or not bank_name:
        raise ValueError("账户名称、银行账号和开户行不能为空")

    balance = _money(
        _payload_value(
            data,
            "balance",
            "balance",
            existing["balance"] if existing else 0,
        ),
        "账户余额",
    )
    if balance < 0:
        raise ValueError("账户余额不能小于0")

    duplicate = conn.execute(
        """
        SELECT id
        FROM bank_accounts
        WHERE store_id = ? AND account_number = ? AND id <> ?
        """,
        (store_id, account_number, existing["id"] if existing else 0),
    ).fetchone()
    if duplicate:
        raise ValueError("该门店已存在相同银行账号")

    return {
        "store_id": store_id,
        "account_name": account_name,
        "account_number": account_number,
        "bank_name": bank_name,
        "bank_code": _text(
            _payload_value(
                data,
                "bankCode",
                "bank_code",
                existing["bank_code"] if existing else "",
            ),
            80,
        ),
        "balance": balance,
        "card_color": _text(
            _payload_value(
                data,
                "cardColor",
                "card_color",
                existing["card_color"] if existing else "#1a1a1a",
            ),
            20,
        )
        or "#1a1a1a",
        "card_bg_image": _text(
            _payload_value(
                data,
                "cardBgImage",
                "card_bg_image",
                existing["card_bg_image"] if existing else "",
            ),
            500,
        ),
        "bank_icon": _text(
            _payload_value(
                data,
                "bankIcon",
                "bank_icon",
                existing["bank_icon"] if existing else "",
            ),
            500,
        ),
    }


def _stored_file_path(public_path):
    """Resolve only files served through our bank-card URL aliases."""
    value = str(public_path or "").strip()
    for kind, config in UPLOAD_TYPES.items():
        prefix = config["url_prefix"] + "/"
        if not value.startswith(prefix):
            continue
        filename = value[len(prefix):].replace("/", os.sep)
        root = os.path.abspath(_upload_directory(kind, create=False))
        target = os.path.abspath(os.path.join(root, filename))
        try:
            if os.path.commonpath([root, target]) == root:
                return target
        except ValueError:
            return None
    return None


def _remove_stored_file(public_path):
    target = _stored_file_path(public_path)
    if target and os.path.isfile(target):
        try:
            os.remove(target)
        except OSError:
            pass


def _upload_directory(kind, create=True):
    config = UPLOAD_TYPES[kind]
    configured = get_setting(config["setting_key"], config["default_path"]).strip()
    path = normalize_server_path(configured or config["default_path"])
    if create:
        os.makedirs(path, exist_ok=True)
    return path


def _save_image(kind):
    config = UPLOAD_TYPES[kind]
    file = request.files.get("file") or request.files.get("image")
    if not file or not file.filename:
        return jsonify({"success": False, "message": "请选择图片文件"}), 400
    if request.content_length and request.content_length > config["max_size"] + 256 * 1024:
        return jsonify({"success": False, "message": "图片文件超过大小限制"}), 413

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"success": False, "message": "仅支持jpg、png、webp或gif图片"}), 400
    if file.mimetype and file.mimetype not in ALLOWED_IMAGE_MIMES:
        return jsonify({"success": False, "message": "上传文件不是有效图片"}), 400

    target_dir = _upload_directory(kind)
    safe_name = secure_filename(os.path.splitext(file.filename)[0]) or "image"
    filename = (
        f"{config['file_prefix']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_"
        f"{uuid.uuid4().hex[:10]}_{safe_name}{extension}"
    )
    target = os.path.join(target_dir, filename)
    file.save(target)
    public_path = f"{config['url_prefix']}/{filename}"
    return jsonify(
        {
            "success": True,
            "message": "图片上传成功",
            "data": {"path": public_path, "url": public_path},
            "path": public_path,
            "url": public_path,
        }
    )


@bank_accounts_bp.route("", methods=["GET"])
def list_bank_accounts():
    store_id = request.args.get("storeId", type=int)
    with get_db() as conn:
        sql = """
            SELECT a.*, s.name AS store_name
            FROM bank_accounts a
            LEFT JOIN stores s ON s.id = a.store_id
            WHERE 1 = 1
        """
        params = []
        if store_id is not None:
            sql += " AND a.store_id = ?"
            params.append(store_id)
        sql += " ORDER BY a.store_id, a.id"
        rows = conn.execute(sql, params).fetchall()
    items = [_serialize(row) for row in rows]
    return jsonify({"success": True, "data": items, "items": items, "total": len(items)})


@bank_accounts_bp.route("/options", methods=["GET"])
def list_bank_account_options():
    """Return the small payload used by settlement-account selectors."""
    store_id = request.args.get("storeId", type=int)
    with get_db() as conn:
        sql = """
            SELECT a.id, a.store_id, a.account_name, a.account_number,
                   a.bank_name, s.name AS store_name
            FROM bank_accounts a
            LEFT JOIN stores s ON s.id = a.store_id
            WHERE 1 = 1
        """
        params = []
        if store_id is not None:
            sql += " AND a.store_id = ?"
            params.append(store_id)
        sql += " ORDER BY a.store_id, a.id"
        rows = conn.execute(sql, params).fetchall()
    items = [
        {
            "id": row["id"],
            "storeId": row["store_id"],
            "storeName": row["store_name"] or "",
            "accountName": row["account_name"],
            "accountNumber": row["account_number"],
            "bankName": row["bank_name"],
            "label": f"{row['account_name']}（{row['bank_name']}）",
            "value": row["account_name"],
        }
        for row in rows
    ]
    return jsonify({"success": True, "data": items, "items": items})


@bank_accounts_bp.route("/<int:account_id>", methods=["GET"])
def get_bank_account(account_id):
    with get_db() as conn:
        account = _serialize(_account_row(conn, account_id))
    if not account:
        return jsonify({"success": False, "message": "银行账户不存在"}), 404
    return jsonify({"success": True, "data": account, "account": account})


@bank_accounts_bp.route("", methods=["POST"])
def create_bank_account():
    data = request.get_json(silent=True) or {}
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                values = _validate_payload(conn, data)
                now = datetime.now().isoformat(timespec="seconds")
                cursor = conn.execute(
                    """
                    INSERT INTO bank_accounts (
                        store_id, account_name, account_number, bank_name,
                        bank_code, balance, card_color, card_bg_image,
                        bank_icon, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        values["store_id"],
                        values["account_name"],
                        values["account_number"],
                        values["bank_name"],
                        values["bank_code"],
                        float(values["balance"]),
                        values["card_color"],
                        values["card_bg_image"],
                        values["bank_icon"],
                        now,
                        now,
                    ),
                )
                account = _serialize(_account_row(conn, cursor.lastrowid))
        return jsonify(
            {"success": True, "message": "银行账户创建成功", "data": account, "account": account}
        ), 201
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    except Exception as error:
        return jsonify({"success": False, "message": f"创建银行账户失败：{error}"}), 500


@bank_accounts_bp.route("/<int:account_id>", methods=["PUT"])
def update_bank_account(account_id):
    old_images = []
    new_images = []
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                existing = conn.execute(
                    "SELECT * FROM bank_accounts WHERE id = ?",
                    (account_id,),
                ).fetchone()
                if not existing:
                    return jsonify({"success": False, "message": "银行账户不存在"}), 404
                values = _validate_payload(conn, request.get_json(silent=True) or {}, existing)
                old_images = [existing["card_bg_image"], existing["bank_icon"]]
                new_images = [values["card_bg_image"], values["bank_icon"]]
                now = datetime.now().isoformat(timespec="seconds")
                conn.execute(
                    """
                    UPDATE bank_accounts
                    SET store_id = ?, account_name = ?, account_number = ?,
                        bank_name = ?, bank_code = ?, balance = ?,
                        card_color = ?, card_bg_image = ?, bank_icon = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        values["store_id"],
                        values["account_name"],
                        values["account_number"],
                        values["bank_name"],
                        values["bank_code"],
                        float(values["balance"]),
                        values["card_color"],
                        values["card_bg_image"],
                        values["bank_icon"],
                        now,
                        account_id,
                    ),
                )
                account = _serialize(_account_row(conn, account_id))
        for old_image, new_image in zip(old_images, new_images):
            if old_image and old_image != new_image:
                _remove_stored_file(old_image)
        return jsonify({"success": True, "message": "银行账户修改成功", "data": account, "account": account})
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    except Exception as error:
        return jsonify({"success": False, "message": f"修改银行账户失败：{error}"}), 500


@bank_accounts_bp.route("/<int:account_id>", methods=["DELETE"])
def delete_bank_account(account_id):
    try:
        with _write_lock:
            with get_db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                account = conn.execute(
                    "SELECT * FROM bank_accounts WHERE id = ?",
                    (account_id,),
                ).fetchone()
                if not account:
                    return jsonify({"success": False, "message": "银行账户不存在"}), 404

                references = []
                match_values = [
                    account["account_name"],
                    account["account_number"],
                    account["bank_name"],
                ]
                for table in ("orders", "payment_receipts", "return_orders"):
                    try:
                        row = conn.execute(
                            f"""
                            SELECT COUNT(*) AS count
                            FROM {table}
                            WHERE settlement_account IN (?, ?, ?)
                            """,
                            match_values,
                        ).fetchone()
                        references.append(int(row["count"] or 0))
                    except Exception:
                        continue
                if sum(references):
                    return jsonify(
                        {
                            "success": False,
                            "message": "该账户已被业务单据引用，不能删除",
                        }
                    ), 409

                conn.execute("DELETE FROM bank_accounts WHERE id = ?", (account_id,))
                images = [account["card_bg_image"], account["bank_icon"]]
        for image in images:
            _remove_stored_file(image)
        return jsonify({"success": True, "message": "银行账户已删除"})
    except Exception as error:
        return jsonify({"success": False, "message": f"删除银行账户失败：{error}"}), 500


@upload_bp.route("/bank-card-background", methods=["POST"])
def upload_bank_card_background():
    return _save_image("background")


@upload_bp.route("/bank-icon", methods=["POST"])
def upload_bank_icon():
    return _save_image("icon")
