"""Authenticated GuGu chat endpoints for the admin workspace."""

from flask import Blueprint, jsonify, request

from utils import ai_client, ai_config, ai_order_draft, ai_order_tools
from utils.ai_secrets import decrypt_api_key
from utils.auth import require_admin_access, require_admin_permission


ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.route("/status", methods=["GET"])
@require_admin_access
def get_ai_status():
    try:
        data = ai_config.config_status()
    except RuntimeError as error:
        return jsonify({"success": False, "message": str(error)}), 409
    response = jsonify({"success": True, "data": data})
    response.headers["Cache-Control"] = "no-store"
    return response


@ai_bp.route("/chat", methods=["POST"])
@require_admin_access
def chat_with_nomi():
    if request.content_length and request.content_length > ai_client.MAX_REQUEST_BYTES:
        return jsonify({"success": False, "message": "对话请求过大"}), 413
    data = request.get_json(silent=True)
    try:
        if not isinstance(data, dict):
            raise ValueError("请提交有效的对话内容")
        messages = ai_client.normalize_messages(data.get("messages"))
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400

    try:
        config = ai_config.get_config()
        api_key = decrypt_api_key(config["encryptedApiKey"])
    except RuntimeError as error:
        return jsonify(
            {"success": False, "code": "invalid_api_key", "message": str(error)}
        ), 409
    if not api_key:
        return jsonify({
            "success": False,
            "code": "missing_api_key",
            "message": "尚未配置 AI 接口，请先在系统设置中配置服务商和 API 密钥。",
        }), 409
    order_query_used = False

    def execute_order_tool(name, arguments):
        nonlocal order_query_used
        result = ai_order_tools.execute_tool(name, arguments)
        if result.get("success"):
            order_query_used = True
        return result

    try:
        result = ai_client.chat(
            config, api_key, messages,
            tools=ai_order_tools.available_tools(),
            execute_tool=execute_order_tool,
        )
    except ai_client.AIProviderError as error:
        return jsonify({
            "success": False, "code": error.code, "message": str(error)
        }), error.status
    result["orderQueryUsed"] = order_query_used
    return jsonify({"success": True, "data": result})


@ai_bp.route("/order-draft", methods=["POST"])
@require_admin_permission("admin.sales.order.create")
def parse_order_draft():
    if request.content_length and request.content_length > ai_client.MAX_REQUEST_BYTES:
        return jsonify({"success": False, "message": "订单草稿请求过大"}), 413
    data = request.get_json(silent=True)
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str) or not text.strip():
        return jsonify({"success": False, "message": "请输入客户下单内容"}), 400
    if len(text) > ai_order_draft.ORDER_DRAFT_MAX_LENGTH:
        return jsonify({
            "success": False,
            "message": f"订单内容不能超过 {ai_order_draft.ORDER_DRAFT_MAX_LENGTH} 个字符",
        }), 400

    try:
        config = ai_config.get_config()
        api_key = decrypt_api_key(config["encryptedApiKey"])
    except RuntimeError as error:
        return jsonify({
            "success": False, "code": "invalid_api_key", "message": str(error)
        }), 409
    if not api_key:
        return jsonify({
            "success": False,
            "code": "missing_api_key",
            "message": "尚未配置 AI 接口，请先在系统设置中配置 API 密钥",
        }), 409

    try:
        result = ai_order_draft.parse_order_draft(config, api_key, text)
    except ValueError as error:
        return jsonify({"success": False, "message": str(error)}), 400
    except ai_client.AIProviderError as error:
        return jsonify({
            "success": False, "code": error.code, "message": str(error)
        }), error.status
    return jsonify({"success": True, "data": result})
