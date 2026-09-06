"""
数据库连接模块（生产环境使用）
"""
import os
import sqlite3
from contextlib import contextmanager

# 数据库路径配置
# backend/db.py -> backend/ -> project_root/
if os.path.exists('/app/data'):
    DB_PATH = '/app/data/order_system.db'
else:
    # 从 backend/ 向上一级到项目根目录，再进入 data/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(project_root, 'data', 'order_system.db')


@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
