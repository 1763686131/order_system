"""Authenticated Nomi chat endpoints for the admin workspace."""

from flask import Blueprint, jsonify, request

from utils import deepseek
from utils.ai_secrets import get_deepseek_api_key
from utils.auth import require_admin_access


ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.route("/status", methods=["GET"])
@require_admin_access
def get_ai_status():
    response = jsonify({"success": True, "data": deepseek.config_status()})
    response.headers["Cache-Control"] = "no-store"
    return response


@ai_bp.route("/chat", methods=["POST"])
@require_admin_access
def chat_with_nomi():
    if request.content_length and request.content_length > deepseek.MAX_REQUEST_BYTES:
        return jsonify({"success": False, "message": "对话请求过大"}), 413
    data = request.get_json(silent=True)
    try:
        if not isinstance(data, dict):
            raise ValueError("请提交有效的对话内容")
        messages = deepseek.normalize_messages(data.get("messages"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    try:
        api_key = get_deepseek_api_key()
    except RuntimeError as error:
        return jsonify(
            {"success": False, "code": "invalid_api_key", "message": str(error)}
        ), 409
    if not api_key:
        return jsonify({
            "success": False,
            "code": "missing_api_key",
            "message": "尚未配置 DeepSeek API，请先在系统设置中配置密钥。",
        }), 409
    try:
        result = deepseek.chat(api_key, messages)
    except deepseek.DeepSeekError as error:
        return jsonify({
            "success": False, "code": error.code, "message": str(error)
        }), error.status
    return jsonify({"success": True, "data": result})
