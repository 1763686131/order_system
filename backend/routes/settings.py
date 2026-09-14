"""System settings endpoints used by the administrator settings page."""

from flask import Blueprint, jsonify, request

from utils.system_settings import (
    DEFAULT_BANK_CARD_BG_PATH,
    DEFAULT_BANK_ICON_PATH,
    DEFAULT_DOCUMENT_PATH,
    DEFAULT_RECEIPT_PATH,
    REPORT_PATH_KEY,
    get_browse_roots,
    get_default_report_path,
    get_report_path,
    get_setting,
    inspect_directory,
    list_directories,
    normalize_server_path,
    set_setting,
)


settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


def _save_directory_setting(key, value, default_path, label):
    normalized = normalize_server_path(value or default_path)
    try:
        # 路径配置保存时自动创建目录，之后测试和上传接口都能直接使用。
        import os

        os.makedirs(normalized, exist_ok=True)
    except OSError as error:
        raise ValueError(f"{label}不可用：{error}")
    status = inspect_directory(normalized)
    if not status["is_directory"] or not status["readable"] or not status["writable"]:
        raise ValueError(f"{label}不可用：{status['message']}")
    set_setting(key, normalized)
    return normalized, status


@settings_bp.route("/paths", methods=["GET"])
def get_path_settings():
    configured_report_path = get_setting(REPORT_PATH_KEY, "").strip()
    report_path = get_report_path()
    report_status = inspect_directory(report_path)

    return jsonify(
        {
            "success": True,
            "data": {
                "reportPath": report_path,
                "documentPath": get_setting("documents.path", DEFAULT_DOCUMENT_PATH),
                "receiptPath": get_setting("receipts.path", DEFAULT_RECEIPT_PATH),
                "bankCardBgPath": get_setting(
                    "bank_cards.bg_path", DEFAULT_BANK_CARD_BG_PATH
                ),
                "bankIconPath": get_setting(
                    "bank_cards.icon_path", DEFAULT_BANK_ICON_PATH
                ),
                "reportPathConfigured": bool(configured_report_path),
                "reportPathDefault": get_default_report_path(),
                "reportStatus": report_status,
            },
        }
    )


@settings_bp.route("/paths", methods=["PUT"])
def save_path_settings():
    data = request.get_json(silent=True) or {}
    report_path = normalize_server_path(data.get("reportPath", ""))

    # An empty value explicitly restores the deployment default.
    if report_path:
        report_status = inspect_directory(report_path)
        if not report_status["is_directory"] or not report_status["readable"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"检测报告路径不可用：{report_status['message']}",
                        "data": report_status,
                    }
                ),
                400,
            )
        set_setting(REPORT_PATH_KEY, report_path)
    else:
        set_setting(REPORT_PATH_KEY, "")

    document_path = str(data.get("documentPath", DEFAULT_DOCUMENT_PATH)).strip()
    receipt_path = str(data.get("receiptPath", DEFAULT_RECEIPT_PATH)).strip()
    set_setting("documents.path", document_path)
    set_setting("receipts.path", receipt_path)

    try:
        bank_bg_path, bank_bg_status = _save_directory_setting(
            "bank_cards.bg_path",
            data.get(
                "bankCardBgPath",
                get_setting("bank_cards.bg_path", DEFAULT_BANK_CARD_BG_PATH),
            ),
            DEFAULT_BANK_CARD_BG_PATH,
            "银行卡背景图路径",
        )
        bank_icon_path, bank_icon_status = _save_directory_setting(
            "bank_cards.icon_path",
            data.get(
                "bankIconPath",
                get_setting("bank_cards.icon_path", DEFAULT_BANK_ICON_PATH),
            ),
            DEFAULT_BANK_ICON_PATH,
            "银行图标路径",
        )
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    return jsonify(
        {
            "success": True,
            "message": "路径配置已保存",
            "data": {
                "reportPath": get_report_path(),
                "documentPath": document_path,
                "receiptPath": receipt_path,
                "bankCardBgPath": bank_bg_path,
                "bankIconPath": bank_icon_path,
                "reportStatus": inspect_directory(get_report_path()),
                "bankCardBgStatus": bank_bg_status,
                "bankIconStatus": bank_icon_status,
            },
        }
    )


@settings_bp.route("/paths/test", methods=["POST"])
def test_path():
    data = request.get_json(silent=True) or {}
    status = inspect_directory(data.get("path", ""))
    return jsonify(
        {
            "success": status["is_directory"] and status["readable"],
            "message": status["message"],
            "data": status,
        }
    )


@settings_bp.route("/directories", methods=["GET"])
def browse_directories():
    path = request.args.get("path")
    data = list_directories(path)
    if not path:
        data["roots"] = get_browse_roots()
    return jsonify({"success": True, "data": data})
