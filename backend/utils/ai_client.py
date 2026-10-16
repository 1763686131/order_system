"""OpenAI-compatible transport shared by Nomi chat and verification."""

import json
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from utils.ai_config import PROVIDERS


TIMEOUT_SECONDS = 45
MAX_MESSAGE_COUNT = 20
MAX_USER_MESSAGE_LENGTH = 4000
MAX_ASSISTANT_MESSAGE_LENGTH = 16000
MAX_CONTEXT_LENGTH = 60000
MAX_REQUEST_BYTES = 512 * 1024


class AIProviderError(Exception):
    def __init__(self, message, code="provider_error", status=502):
        super().__init__(message)
        self.code = code
        self.status = status


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an administrator's credential to a redirect target.
        return None


def normalize_messages(raw_messages):
    if (
        not isinstance(raw_messages, list)
        or not raw_messages
        or len(raw_messages) > MAX_MESSAGE_COUNT
    ):
        raise ValueError("请提交 1 至 20 条有效的对话消息")
    messages = []
    for item in raw_messages:
        if not isinstance(item, dict):
            raise ValueError("对话消息格式不正确")
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            raise ValueError("对话只支持用户和助手的文字消息")
        content = content.strip()
        limit = (
            MAX_USER_MESSAGE_LENGTH
            if role == "user"
            else MAX_ASSISTANT_MESSAGE_LENGTH
        )
        if not content or len(content) > limit:
            label = "提问" if role == "user" else "回复"
            raise ValueError(f"每条{label}需为 1 至 {limit} 个字符")
        messages.append({"role": role, "content": content})
    if messages[-1]["role"] != "user":
        raise ValueError("最后一条消息必须是本次提问")
    if sum(len(item["content"]) for item in messages) > MAX_CONTEXT_LENGTH:
        raise ValueError("对话内容过长，请清空对话后重新提问")
    return messages


def chat(config, api_key, messages, max_tokens=2048):
    provider = config["provider"]
    provider_name = PROVIDERS[provider]["name"]
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是订单管理系统后台的 固固 智能助手。默认用简洁清晰的中文回答，"
                    "可以帮助用户整理文字、分析问题、起草内容。"
                    "目前没有接入订单、库存、客户或任何业务查询与写入工具；"
                    "你看不到系统实时数据，不得编造查询结果或声称已经执行了业务操作。"
                ),
            },
            *messages,
        ],
        "stream": False,
    }
    token_field = "max_completion_tokens" if provider == "openai" else "max_tokens"
    payload[token_field] = max_tokens
    if provider in ("deepseek", "kimi", "zhipu", "doubao"):
        payload["thinking"] = {"type": "disabled"}
    elif provider in ("qwen", "siliconflow"):
        payload["enable_thinking"] = False
    provider_request = Request(
        f"{config['baseUrl']}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with build_opener(_NoRedirect()).open(
            provider_request, timeout=TIMEOUT_SECONDS
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        # Provider errors may echo request details; only return known messages.
        error.close()
        if error.code in (401, 403):
            raise AIProviderError(
                f"{provider_name} API 密钥无效或无权调用，请在系统设置中更新",
                "invalid_api_key",
            ) from None
        if error.code == 402:
            raise AIProviderError(
                f"{provider_name} 账户余额不足，请充值后重试", "insufficient_balance"
            ) from None
        if error.code == 429:
            raise AIProviderError(
                f"{provider_name} 请求过于频繁，请稍后重试", "rate_limited", 429
            ) from None
        if error.code in (400, 404, 422):
            raise AIProviderError(
                f"{provider_name} 拒绝请求，请检查接口地址、模型 ID 及模型调用权限",
                "invalid_provider_config",
                400,
            ) from None
        if 300 <= error.code < 400:
            raise AIProviderError(
                "API 地址发生跳转，请在系统设置中填写最终接口地址",
                "provider_redirect",
                400,
            ) from None
        raise AIProviderError(f"{provider_name} 服务暂时不可用，请稍后重试") from None
    except TimeoutError:
        raise AIProviderError(
            f"等待 {provider_name} 回复超时，请重试", "provider_timeout", 504
        ) from None
    except URLError:
        raise AIProviderError(
            f"无法连接 {provider_name}，请检查接口地址和后端服务器网络",
            "provider_unavailable",
        ) from None
    except (HTTPException, OSError, UnicodeDecodeError, ValueError):
        raise AIProviderError(f"{provider_name} 响应异常，请稍后重试") from None

    choices = result.get("choices") if isinstance(result, dict) else None
    choice = choices[0] if isinstance(choices, list) and choices else None
    message = choice.get("message") if isinstance(choice, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise AIProviderError(f"{provider_name} 没有返回有效回复，请重试")
    return {
        "content": content.strip(),
        "model": config["model"],
        "truncated": choice.get("finish_reason") == "length",
    }
