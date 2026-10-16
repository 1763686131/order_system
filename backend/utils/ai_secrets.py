"""Encryption helpers for server-side AI provider credentials."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

from utils.system_settings import get_setting, set_setting


DEEPSEEK_API_KEY_SETTING = "ai.deepseek_api_key"
ENCRYPTED_PREFIX = "fernet:v1:"


def _cipher():
    secret_key = current_app.config["SECRET_KEY"]
    if isinstance(secret_key, str):
        secret_key = secret_key.encode("utf-8")
    derived_key = hashlib.sha256(
        b"order-system:ai-credentials:v1:" + secret_key
    ).digest()
    return Fernet(base64.urlsafe_b64encode(derived_key))


def decrypt_api_key(stored_value):
    if not stored_value:
        return ""
    try:
        if not isinstance(stored_value, str) or not stored_value.startswith(ENCRYPTED_PREFIX):
            raise ValueError("Unsupported credential format")
        encrypted_value = stored_value[len(ENCRYPTED_PREFIX):].encode("ascii")
        return _cipher().decrypt(encrypted_value).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError) as error:
        raise RuntimeError(
            "Nomi API 密钥无法解密，请在系统设置中重新保存密钥"
        ) from error


def encrypt_api_key(api_key):
    value = str(api_key or "").strip()
    return (
        f"{ENCRYPTED_PREFIX}{_cipher().encrypt(value.encode('utf-8')).decode('ascii')}"
        if value
        else ""
    )


def get_deepseek_api_key():
    return decrypt_api_key(get_setting(DEEPSEEK_API_KEY_SETTING, ""))


def set_deepseek_api_key(api_key):
    value = str(api_key or "").strip()
    stored_value = encrypt_api_key(value)
    set_setting(DEEPSEEK_API_KEY_SETTING, stored_value)
    return value
