"""Managed storage helpers for employee avatar images."""

import base64
import binascii
import os
import re
import uuid
from datetime import datetime


MAX_AVATAR_BYTES = 5 * 1024 * 1024
AVATAR_DIRECTORY_NAME = "employee-avatars"
AVATAR_URL_PREFIX = f"/uploads/{AVATAR_DIRECTORY_NAME}/"

_DATA_URL_PATTERN = re.compile(
    r"^data:(image/(?:jpeg|jpg|png|webp|gif));base64,(.+)$",
    re.IGNORECASE | re.DOTALL,
)


def _upload_root():
    if os.path.exists("/app/frontend/index.html") and os.path.isdir("/app/uploads"):
        return "/app/uploads"
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, "uploads")


UPLOAD_ROOT = _upload_root()
AVATAR_ROOT = os.path.join(UPLOAD_ROOT, AVATAR_DIRECTORY_NAME)


def _image_extension(content):
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    raise ValueError("头像仅支持 JPG、PNG、WebP 或 GIF 图片")


def _validate_content(content):
    if not content:
        raise ValueError("头像文件不能为空")
    if len(content) > MAX_AVATAR_BYTES:
        raise ValueError("头像图片不能超过 5MB")
    return _image_extension(content)


def _save_content(content, employee_id=None):
    extension = _validate_content(content)
    now = datetime.now()
    month = now.strftime("%Y-%m")
    target_dir = os.path.join(AVATAR_ROOT, month)
    os.makedirs(target_dir, exist_ok=True)

    employee_part = f"employee_{employee_id}_" if employee_id else "avatar_"
    filename = (
        f"{employee_part}{now.strftime('%Y%m%d%H%M%S')}_"
        f"{uuid.uuid4().hex[:10]}{extension}"
    )
    target_path = os.path.join(target_dir, filename)
    temporary_path = f"{target_path}.tmp"
    try:
        with open(temporary_path, "xb") as avatar_file:
            avatar_file.write(content)
        os.replace(temporary_path, target_path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)

    return f"{AVATAR_URL_PREFIX}{month}/{filename}"


def save_avatar_upload(file_storage, employee_id):
    if not file_storage or not file_storage.filename:
        raise ValueError("请选择头像图片")
    content = file_storage.stream.read(MAX_AVATAR_BYTES + 1)
    return _save_content(content, employee_id)


def save_avatar_data_url(data_url, employee_id=None):
    match = _DATA_URL_PATTERN.match(str(data_url or "").strip())
    if not match:
        raise ValueError("历史头像数据格式无效")
    encoded_content = match.group(2)
    if len(encoded_content) > ((MAX_AVATAR_BYTES + 2) // 3) * 4:
        raise ValueError("历史头像图片不能超过 5MB")
    try:
        content = base64.b64decode(encoded_content, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("历史头像数据无法解码")
    return _save_content(content, employee_id)


def is_managed_avatar_url(value):
    avatar_url = str(value or "").strip()
    if not avatar_url.startswith(AVATAR_URL_PREFIX):
        return False
    relative_path = avatar_url[len(AVATAR_URL_PREFIX):]
    if (
        not relative_path
        or "\\" in relative_path
        or relative_path.startswith("/")
        or ".." in relative_path.split("/")
    ):
        return False
    extension = os.path.splitext(relative_path)[1].lower()
    return extension in {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def normalize_avatar_url(value):
    avatar_url = str(value or "").strip()
    if not avatar_url:
        return ""
    if len(avatar_url) > 500 or not is_managed_avatar_url(avatar_url):
        raise ValueError("请通过头像上传接口上传图片")
    return avatar_url


def delete_managed_avatar(avatar_url):
    if not is_managed_avatar_url(avatar_url):
        return False

    relative_path = str(avatar_url)[len(AVATAR_URL_PREFIX):].replace("/", os.sep)
    avatar_root = os.path.abspath(AVATAR_ROOT)
    target_path = os.path.abspath(os.path.join(avatar_root, relative_path))
    try:
        if os.path.commonpath([avatar_root, target_path]) != avatar_root:
            return False
    except ValueError:
        return False

    if not os.path.isfile(target_path):
        return False
    os.remove(target_path)
    return True


def migrate_avatar_data_urls(conn):
    """Move legacy Base64 avatars to one managed file per employee/account."""
    employee_rows = conn.execute(
        """
        SELECT id, user_id, avatar_url
        FROM employees
        WHERE avatar_url LIKE 'data:image/%;base64,%'
        """
    ).fetchall()
    for row in employee_rows:
        data_url = row["avatar_url"]
        try:
            avatar_url = save_avatar_data_url(data_url, row["id"])
        except ValueError:
            avatar_url = ""
        except OSError:
            continue
        conn.execute(
            """
            UPDATE employees
            SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (avatar_url, row["id"]),
        )
        if row["user_id"]:
            conn.execute(
                """
                UPDATE users
                SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (avatar_url, row["user_id"]),
            )

    user_rows = conn.execute(
        """
        SELECT id, avatar_url
        FROM users
        WHERE avatar_url LIKE 'data:image/%;base64,%'
        """
    ).fetchall()
    for row in user_rows:
        try:
            avatar_url = save_avatar_data_url(row["avatar_url"])
        except ValueError:
            avatar_url = ""
        except OSError:
            continue
        conn.execute(
            """
            UPDATE users
            SET avatar_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (avatar_url, row["id"]),
        )
