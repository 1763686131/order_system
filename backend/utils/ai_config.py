"""Provider presets and encrypted configuration for Nomi."""

import json
from urllib.parse import urlsplit, urlunsplit

from utils.ai_secrets import (
    DEEPSEEK_API_KEY_SETTING,
    decrypt_api_key,
    encrypt_api_key,
)
from utils.system_settings import get_setting, set_setting


SETTINGS_PERMISSION = "admin.route.system.settings"
CONFIG_SETTING = "ai.providers_config"
DEFAULT_PROVIDER = "deepseek"
PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "baseUrl": "https://api.deepseek.com",
        "model": "deepseek-flash",
    },
    "qwen": {
        "name": "通义千问 · 阿里云百炼",
        "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
    },
    "kimi": {
        "name": "Kimi · 月之暗面",
        "baseUrl": "https://api.moonshot.cn/v1",
        "model": "kimi-k2.6",
    },
    "zhipu": {
        "name": "智谱 GLM",
        "baseUrl": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-5.3",
    },
    "doubao": {
        "name": "豆包 · 火山方舟",
        "baseUrl": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "",
        "modelPlaceholder": "模型 ID 或接入点 ID（ep-...）",
    },
    "siliconflow": {
        "name": "硅基流动",
        "baseUrl": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V4-Flash",
    },
    "openai": {
        "name": "OpenAI",
        "baseUrl": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
    },
    "custom": {
        "name": "自定义（OpenAI 兼容）",
        "baseUrl": "",
        "model": "",
        "modelPlaceholder": "输入服务商提供的模型 ID",
    },
}


def validate_provider(provider):
    if not isinstance(provider, str) or provider not in PROVIDERS:
        raise ValueError("请选择有效的 AI 服务商")
    return provider


def normalize_base_url(value):
    if not isinstance(value, str):
        raise ValueError("请填写有效的 API 接口地址")
    value = value.strip().rstrip("/")
    if not value or len(value) > 2048 or any(
        char.isspace() or ord(char) < 33 or ord(char) > 126 for char in value
    ):
        raise ValueError("API 接口地址格式不正确")
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.port == 0
        ):
            raise ValueError
    except ValueError:
        raise ValueError(
            "接口地址需以 http:// 或 https:// 开头，且不能包含账号、密码或查询参数"
        ) from None
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        path = path[:-len("/chat/completions")]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), path, "", ""))


def validate_config(provider, base_url, model):
    provider = validate_provider(provider)
    if not isinstance(model, str):
        raise ValueError("请填写模型 ID")
    model = model.strip()
    if not model or len(model) > 200 or any(
        char.isspace() or ord(char) < 33 or ord(char) > 126 for char in model
    ):
        raise ValueError("模型 ID 需为 1 至 200 个非空白字符")
    return {
        "provider": provider,
        "baseUrl": normalize_base_url(base_url),
        "model": model,
    }


def _load_profiles():
    stored = get_setting(CONFIG_SETTING, "")
    if not stored:
        return {"activeProvider": DEFAULT_PROVIDER, "profiles": {}}
    try:
        document = json.loads(stored)
        if (
            not isinstance(document, dict)
            or document.get("activeProvider") not in PROVIDERS
            or not isinstance(document.get("profiles"), dict)
            or any(
                key not in PROVIDERS
                or not isinstance(profile, dict)
                or any(
                    not isinstance(profile.get(field, ""), str)
                    for field in ("baseUrl", "model", "apiKey")
                )
                for key, profile in document["profiles"].items()
            )
        ):
            raise ValueError
        return document
    except (TypeError, ValueError):
        raise RuntimeError("Nomi 服务商配置无法读取，请检查数据库中的 AI 配置") from None


def get_config(provider=None):
    document = _load_profiles()
    provider = validate_provider(
        document["activeProvider"] if provider is None else provider
    )
    preset = PROVIDERS[provider]
    profile = document["profiles"].get(provider)
    if profile is None:
        profile = {
            "baseUrl": preset["baseUrl"],
            "model": preset["model"],
            # Read legacy credentials without changing the existing database.
            "apiKey": get_setting(DEEPSEEK_API_KEY_SETTING, "")
            if provider == DEFAULT_PROVIDER
            else "",
        }
    return {
        "provider": provider,
        "baseUrl": profile.get("baseUrl", preset["baseUrl"]),
        "model": profile.get("model", preset["model"]),
        "encryptedApiKey": profile.get("apiKey", ""),
    }


def config_status(provider=None, include_settings=False):
    config = get_config(provider)
    try:
        api_key = decrypt_api_key(config["encryptedApiKey"])
        configuration_error = ""
    except RuntimeError as error:
        api_key = ""
        configuration_error = str(error)
    data = {
        "provider": config["provider"],
        "providerName": PROVIDERS[config["provider"]]["name"],
        "model": config["model"],
        "configured": bool(api_key),
        "configurationError": configuration_error,
    }
    if include_settings:
        active_config = get_config()
        try:
            active_configured = bool(decrypt_api_key(active_config["encryptedApiKey"]))
        except RuntimeError:
            active_configured = False
        data.update({
            "baseUrl": config["baseUrl"],
            "maskedApiKey": f"****{api_key[-4:]}" if api_key else "",
            "activeProvider": active_config["provider"],
            "activeConfigured": active_configured,
            "providers": [
                {"id": key, **preset} for key, preset in PROVIDERS.items()
            ],
        })
    return data


def save_config(config, api_key):
    document = _load_profiles()
    document["profiles"][config["provider"]] = {
        "baseUrl": config["baseUrl"],
        "model": config["model"],
        "apiKey": encrypt_api_key(api_key),
    }
    document["activeProvider"] = config["provider"]
    # One database write keeps the active provider, endpoint and key together.
    set_setting(CONFIG_SETTING, json.dumps(document, ensure_ascii=False))


def clear_api_key(provider):
    config = get_config(provider)
    document = _load_profiles()
    document["profiles"][provider] = {
        "baseUrl": config["baseUrl"],
        "model": config["model"],
        "apiKey": "",
    }
    set_setting(CONFIG_SETTING, json.dumps(document, ensure_ascii=False))
    if provider == DEFAULT_PROVIDER:
        set_setting(DEEPSEEK_API_KEY_SETTING, "")
