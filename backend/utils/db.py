"""
数据库连接模块（生产环境使用）
"""
import os
import sqlite3
from contextlib import contextmanager
from threading import Lock

# 数据库路径配置
# utils/db.py -> backend/utils/ -> backend/ -> project_root/
if os.path.exists('/app/data'):
    DB_PATH = '/app/data/order_system.db'
else:
    # 从 backend/utils/ 向上两级到项目根目录，再进入 data/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH = os.path.join(project_root, 'data', 'order_system.db')

_schema_lock = Lock()
_schema_ready = False


def _ensure_hr_reports_schema(conn):
    """创建人事检测报告表"""
    cursor = conn.cursor()

    # 检查表是否存在
    table_exists = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'hr_reports'"
    ).fetchone()

    if not table_exists:
        cursor.execute("""
            CREATE TABLE hr_reports (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_hash TEXT,
                file_size INTEGER,
                file_type TEXT,
                uploader TEXT,
                share_token TEXT,
                share_expire TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_reports_path ON hr_reports(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_reports_token ON hr_reports(share_token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_reports_type ON hr_reports(file_type)")

        conn.commit()


def _ensure_customer_schema(conn):
    """Migrate the legacy customers table to the fields used by the API."""
    global _schema_ready
    if _schema_ready:
        return

    with _schema_lock:
        if _schema_ready:
            return

        cursor = conn.cursor()
        table_exists = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'customers'"
        ).fetchone()

        if not table_exists:
            cursor.execute(
                """
                CREATE TABLE customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code TEXT,
                    customer_name TEXT NOT NULL,
                    store_id INTEGER,
                    contact_person TEXT,
                    phone TEXT,
                    address TEXT,
                    balance REAL DEFAULT 0,
                    receivable REAL DEFAULT 0,
                    bank_name TEXT,
                    bank_account TEXT,
                    bank_code TEXT,
                    tax_number TEXT,
                    remark TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        else:
            existing_columns = {
                row["name"] for row in cursor.execute("PRAGMA table_info(customers)")
            }
            columns_to_add = {
                "customer_code": "TEXT",
                "store_id": "INTEGER",
                "phone": "TEXT",
                "address": "TEXT",
                "balance": "REAL DEFAULT 0",
                "bank_name": "TEXT",
                "bank_account": "TEXT",
                "bank_code": "TEXT",
                "tax_number": "TEXT",
                "remark": "TEXT",
                "status": "TEXT DEFAULT 'active'",
            }
            for column, definition in columns_to_add.items():
                if column not in existing_columns:
                    cursor.execute(
                        f"ALTER TABLE customers ADD COLUMN {column} {definition}"
                    )

            if "contact_phone" in existing_columns:
                cursor.execute(
                    """
                    UPDATE customers
                    SET phone = contact_phone
                    WHERE (phone IS NULL OR phone = '')
                      AND contact_phone IS NOT NULL
                    """
                )
            if "contact_address" in existing_columns:
                cursor.execute(
                    """
                    UPDATE customers
                    SET address = contact_address
                    WHERE (address IS NULL OR address = '')
                      AND contact_address IS NOT NULL
                    """
                )

        cursor.execute(
            """
            UPDATE customers
            SET customer_code = printf('%03d', id)
            WHERE customer_code IS NULL OR trim(customer_code) = ''
            """
        )
        cursor.execute(
            """
            UPDATE customers
            SET balance = COALESCE(balance, 0),
                receivable = COALESCE(receivable, 0),
                status = COALESCE(NULLIF(status, ''), 'active')
            """
        )

        orders_exists = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'orders'"
        ).fetchone()
        if orders_exists:
            cursor.execute(
                """
                UPDATE customers
                SET store_id = (
                    SELECT o.store_id
                    FROM orders o
                    WHERE o.customer_id = customers.id
                      AND o.store_id IS NOT NULL
                    GROUP BY o.store_id
                    ORDER BY COUNT(*) DESC, o.store_id
                    LIMIT 1
                )
                WHERE store_id IS NULL
                  AND EXISTS (
                    SELECT 1
                    FROM orders o2
                    WHERE o2.customer_id = customers.id
                      AND o2.store_id IS NOT NULL
                  )
                """
            )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_customers_store_id ON customers(store_id)"
        )
        conn.commit()
        _schema_ready = True


@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_customer_schema(conn)
        _ensure_hr_reports_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
