"""Per-user persistent chat history for the admin AI assistant."""

import json
import re


MAX_HISTORY_COUNT = 30
MAX_HISTORY_MESSAGES = 200
MAX_HISTORY_BYTES = 450 * 1024
HISTORY_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MESSAGE_FIELDS = {
    "id",
    "role",
    "content",
    "orderFlow",
    "question",
    "options",
    "summary",
    "orderQueryUsed",
    "truncated",
}


def ensure_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_chat_histories (
            id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            messages_json TEXT NOT NULL,
            message_count INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ai_chat_histories_user_updated
        ON ai_chat_histories(user_id, updated_at DESC)
        """
    )


def validate_history_id(history_id):
    if not isinstance(history_id, str) or not HISTORY_ID_PATTERN.fullmatch(history_id):
        raise ValueError("历史聊天编号无效")
    return history_id


def normalize_history(data):
    if not isinstance(data, dict):
        raise ValueError("请提交有效的历史聊天内容")

    title = data.get("title")
    messages = data.get("messages")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("历史聊天标题不能为空")
    if not isinstance(messages, list) or not 1 <= len(messages) <= MAX_HISTORY_MESSAGES:
        raise ValueError(f"聊天记录需包含 1 至 {MAX_HISTORY_MESSAGES} 条消息")

    normalized = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("聊天消息格式不正确")
        role = message.get("role")
        content = message.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            raise ValueError("聊天消息只支持用户和助手的文字内容")
        limit = 4000 if role == "user" else 16000
        if len(content) > limit:
            raise ValueError(f"单条聊天内容不能超过 {limit} 个字符")
        item = {key: value for key, value in message.items() if key in MESSAGE_FIELDS}
        try:
            json.dumps(item, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ValueError("聊天消息包含不支持的数据格式") from error
        normalized.append(item)

    messages_json = json.dumps(normalized, ensure_ascii=False, allow_nan=False)
    if len(messages_json.encode("utf-8")) > MAX_HISTORY_BYTES:
        raise ValueError("聊天记录过长，无法保存")
    return title.strip()[:120], normalized, messages_json


def list_histories(conn, user_id):
    rows = conn.execute(
        """
        SELECT id, title, message_count, created_at, updated_at
        FROM ai_chat_histories
        WHERE user_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT ?
        """,
        (user_id, MAX_HISTORY_COUNT),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "messageCount": row["message_count"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }
        for row in rows
    ]


def get_history(conn, user_id, history_id):
    row = conn.execute(
        """
        SELECT id, title, messages_json, message_count, created_at, updated_at
        FROM ai_chat_histories
        WHERE user_id = ? AND id = ?
        """,
        (user_id, history_id),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "messages": json.loads(row["messages_json"]),
        "messageCount": row["message_count"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def save_history(conn, user_id, history_id, data):
    title, messages, messages_json = normalize_history(data)
    conn.execute(
        """
        INSERT INTO ai_chat_histories (
            id, user_id, title, messages_json, message_count, created_at, updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?,
            strftime('%Y-%m-%d %H:%M:%f', 'now'),
            strftime('%Y-%m-%d %H:%M:%f', 'now')
        )
        ON CONFLICT(user_id, id) DO UPDATE SET
            title = excluded.title,
            messages_json = excluded.messages_json,
            message_count = excluded.message_count,
            updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
        """,
        (history_id, user_id, title, messages_json, len(messages)),
    )
    conn.execute(
        """
        DELETE FROM ai_chat_histories
        WHERE user_id = ?
          AND id NOT IN (
              SELECT id FROM ai_chat_histories
              WHERE user_id = ?
              ORDER BY updated_at DESC, id DESC
              LIMIT ?
          )
        """,
        (user_id, user_id, MAX_HISTORY_COUNT),
    )
    return {
        "id": history_id,
        "title": title,
        "messageCount": len(messages),
    }
