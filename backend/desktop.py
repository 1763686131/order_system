"""Windows launcher for the standalone demo."""

import argparse
import errno
import logging
import msvcrt
import os
import sys
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from desktop_dialog import dialog, notice
from desktop_network import local_server, private_interfaces
from utils.runtime_paths import configure_desktop


TITLE = "订单与进销存管理系统"
LOCAL = 100
LAN = 101
OPEN = 102
EXIT = 2


class AlreadyRunning(Exception):
    pass


@contextmanager
def instance_lock(root):
    with (root / "desktop.lock").open("a+b") as lock_file:
        lock_file.seek(0)
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            if error.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            raise AlreadyRunning from error
        yield


def prepare_app(root):
    resources = Path(__file__).resolve().parent
    frontend = resources / "frontend" if getattr(sys, "frozen", False) else resources.parent / "dist"
    if not (frontend / "index.html").is_file():
        raise RuntimeError("找不到前端资源，请重新构建或下载演示版。")

    configure_desktop(root, frontend)

    # These modules resolve some of their storage paths at import time.
    from app import app
    from utils.base_schema import initialize_base_schema
    from utils.db import DB_PATH, get_db

    app.config.update(
        SESSION_COOKIE_NAME="order_system_demo",
        SESSION_COOKIE_SECURE=False,
        BOOTSTRAP_LOOPBACK_ONLY=True,
    )
    initialize_base_schema(DB_PATH)
    with get_db():
        pass
    return app


def show_launcher(urls, worker, auto_open):
    url = urls[0]

    def open_page():
        try:
            os.startfile(url)
        except OSError:
            logging.exception("Could not open the default browser")
            notice(TITLE, f"无法打开默认浏览器。请手动访问\n{url}", error=True)

    def handle_click(button):
        if button != OPEN:
            return False
        if worker.is_alive():
            open_page()
        else:
            notice(TITLE, "服务已停止，请退出后重新启动。", error=True)
        return True

    body = f"本机访问\n{url}\n"
    if len(urls) > 1:
        body += "\n同一局域网内的设备可在浏览器打开\n" + "\n".join(urls[1:]) + "\n"
    body += "\n首次使用请在本机创建管理员。关闭此窗口将停止服务。"
    if auto_open:
        open_page()
    dialog(TITLE, "局域网服务运行中" if len(urls) > 1 else "本机服务运行中", body,
           [(OPEN, "打开网页"), (EXIT, "退出")], default=OPEN, on_click=handle_click)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lan", action="store_true", help="start in LAN mode")
    parser.add_argument("--no-browser", action="store_true", help="do not open the default browser")
    parser.add_argument("--serve-only", action="store_true", help="run the service without dialogs")
    args = parser.parse_args()
    local = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    root = Path(local) / "OrderSystemDemo"

    try:
        root.mkdir(parents=True, exist_ok=True)
        with instance_lock(root):
            handler = RotatingFileHandler(root / "desktop.log", maxBytes=1024 * 1024, backupCount=1, encoding="utf-8")
            logging.basicConfig(handlers=[handler], level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

            if args.lan or args.serve_only:
                mode = LAN if args.lan else LOCAL
            else:
                mode = dialog(TITLE, "选择启动方式", "选择局域网启动后，同一网络的设备也可以用浏览器访问。",
                              [(LOCAL, "仅本机"), (LAN, "局域网启动"), (EXIT, "取消")], default=LOCAL)
            if mode == EXIT:
                return 0

            interfaces = private_interfaces() if mode == LAN else ()
            if mode == LAN and not interfaces:
                raise RuntimeError("未找到可用的内网 IPv4 地址，请先连接局域网。")

            with local_server(prepare_app(root), interfaces) as (urls, worker):
                if args.serve_only:
                    worker.join()
                else:
                    show_launcher(urls, worker, auto_open=not args.no_browser)
    except AlreadyRunning:
        if not args.serve_only:
            notice(TITLE, "演示版已经在运行，请使用已打开的启动窗口。")
        return 1
    except Exception as error:
        logging.exception("Could not start the desktop app")
        if not args.serve_only:
            notice(TITLE, f"启动失败：{error}\n日志位于 {root / 'desktop.log'}", error=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
