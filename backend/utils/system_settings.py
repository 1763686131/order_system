"""Helpers for settings that are shared by the admin UI and backend services."""

import os
from datetime import datetime

from utils.db import get_db


REPORT_PATH_KEY = "reports.path"
DEFAULT_DOCUMENT_PATH = "/var/data/documents"
DEFAULT_RECEIPT_PATH = "/var/data/receipts"


def get_default_report_path():
    """Return the path used before an administrator chooses a custom folder."""
    if os.path.exists("/app/frontend/index.html") and os.path.isdir("/app/uploads"):
        return "/app/uploads/hr_reports"

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, "uploads", "hr_reports")


def get_setting(key, default=""):
    with get_db() as conn:
        row = conn.execute(
            "SELECT setting_value FROM system_settings WHERE setting_key = ?",
            (key,),
        ).fetchone()
    return row["setting_value"] if row else default


def set_setting(key, value):
    value = "" if value is None else str(value).strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO system_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (key, value, now),
        )
        conn.commit()
    return value


def get_report_path():
    configured = get_setting(REPORT_PATH_KEY, "").strip()
    return configured or get_default_report_path()


def normalize_server_path(path):
    """Normalize a path without touching the filesystem."""
    if path is None:
        return ""
    value = os.path.expanduser(str(path).strip())
    if not value:
        return ""
    return os.path.abspath(os.path.normpath(value))


def inspect_directory(path):
    """Return a safe, user-facing status for a server-side directory."""
    normalized = normalize_server_path(path)
    if not normalized:
        return {
            "path": "",
            "exists": False,
            "is_directory": False,
            "readable": False,
            "writable": False,
            "message": "路径不能为空",
        }

    exists = os.path.exists(normalized)
    is_directory = os.path.isdir(normalized)
    readable = os.access(normalized, os.R_OK) if is_directory else False
    writable = os.access(normalized, os.W_OK) if is_directory else False

    if not exists:
        message = "服务器上不存在该目录"
    elif not is_directory:
        message = "路径不是文件夹"
    elif not readable:
        message = "目录不可读取"
    else:
        message = "路径可用"

    return {
        "path": normalized,
        "exists": exists,
        "is_directory": is_directory,
        "readable": readable,
        "writable": writable,
        "message": message,
    }


def get_browse_roots():
    """Directories shown when the server-side folder browser is opened."""
    configured = os.environ.get(
        "REPORTS_BROWSE_ROOTS",
        "/mnt,/media,/volume1,/data,/app/uploads",
    )
    roots = []
    for raw_path in configured.split(","):
        path = normalize_server_path(raw_path)
        if path and path not in roots and os.path.isdir(path):
            roots.append(path)

    # On a local Windows development server, expose available drive roots.
    if os.name == "nt":
        import string

        for drive in string.ascii_uppercase:
            drive_path = f"{drive}:\\"
            if os.path.isdir(drive_path) and drive_path not in roots:
                roots.append(drive_path)
    return roots


def list_directories(path=None):
    """List child directories visible to the server process."""
    if path:
        current = normalize_server_path(path)
        status = inspect_directory(current)
        if not status["is_directory"] or not status["readable"]:
            return {
                "path": current,
                "parent_path": os.path.dirname(current),
                "directories": [],
                "message": status["message"],
            }
        candidates = [current]
    else:
        candidates = get_browse_roots()
        if not candidates:
            return {
                "path": "",
                "parent_path": "",
                "directories": [],
                "message": "没有可浏览的服务器目录，请直接输入容器内路径",
            }

    directories = []
    if path:
        current = candidates[0]
        try:
            for entry in sorted(os.scandir(current), key=lambda item: item.name.lower()):
                if entry.is_dir(follow_symlinks=False):
                    directories.append(
                        {
                            "name": entry.name,
                            "path": os.path.abspath(entry.path),
                        }
                    )
        except OSError as exc:
            return {
                "path": current,
                "parent_path": os.path.dirname(current),
                "directories": [],
                "message": f"读取目录失败: {exc}",
            }

        return {
            "path": current,
            "parent_path": os.path.dirname(current) if os.path.dirname(current) != current else "",
            "directories": directories,
            "message": "读取成功",
        }

    return {
        "path": "",
        "parent_path": "",
        "directories": [{"name": path, "path": path} for path in candidates],
        "message": "请选择服务器目录",
    }

