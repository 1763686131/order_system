"""
数据库连接模块（生产环境使用）
"""
import os
import sqlite3
from contextlib import contextmanager
from threading import Lock

# 数据库路径配置
# utils/db.py -> backend/utils/ -> backend/ -> project_root/
if os.path.exists('/app/frontend/index.html') and os.path.isdir('/app/data'):
    DB_PATH = '/app/data/order_system.db'
else:
    # 从 backend/utils/ 向上两级到项目根目录，再进入 data/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH = os.path.join(project_root, 'data', 'order_system.db')

_schema_lock = Lock()
_schema_ready = False
_units_schema_lock = Lock()
_units_schema_ready = False
_raw_material_schema_lock = Lock()
_raw_material_schema_ready = False
_stock_inbound_schema_lock = Lock()
_stock_inbound_schema_ready = False
_material_outbound_schema_lock = Lock()
_material_outbound_schema_ready = False
_return_schema_lock = Lock()
_return_schema_ready = False
_system_settings_schema_lock = Lock()
_system_settings_schema_ready = False
_bank_accounts_schema_lock = Lock()
_bank_accounts_schema_ready = False
_print_templates_schema_lock = Lock()
_print_templates_schema_ready = False

DEFAULT_PACKAGING_NAMES = ('无', '桶装', '纸箱', '托盘', '袋装')


def _ensure_units_schema(conn):
    """为单位表增加分组字段，并初始化默认包装。"""
    global _units_schema_ready
    if _units_schema_ready:
        return

    with _units_schema_lock:
        if _units_schema_ready:
            return

        cursor = conn.cursor()
        table_exists = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'units'"
        ).fetchone()

        if not table_exists:
            cursor.execute(
                """
                CREATE TABLE units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    unit_type TEXT NOT NULL DEFAULT 'measurement',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        else:
            existing_columns = {
                row["name"] for row in cursor.execute("PRAGMA table_info(units)")
            }
            if "unit_type" not in existing_columns:
                cursor.execute(
                    "ALTER TABLE units ADD COLUMN unit_type TEXT DEFAULT 'measurement'"
                )

        cursor.execute(
            """
            UPDATE units
            SET unit_type = 'measurement'
            WHERE unit_type IS NULL OR trim(unit_type) = ''
            """
        )

        for packaging_name in DEFAULT_PACKAGING_NAMES:
            cursor.execute(
                """
                INSERT INTO units (name, unit_type)
                SELECT ?, 'packaging'
                WHERE NOT EXISTS (
                    SELECT 1 FROM units
                    WHERE name = ? AND unit_type = 'packaging'
                )
                """,
                (packaging_name, packaging_name),
            )

        conn.commit()
        _units_schema_ready = True


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
                share_expire TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_reports_path ON hr_reports(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_reports_token ON hr_reports(share_token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_reports_type ON hr_reports(file_type)")

        conn.commit()


def _ensure_system_settings_schema(conn):
    """Create the small key/value store used by server-side system settings."""
    global _system_settings_schema_ready
    if _system_settings_schema_ready:
        return

    with _system_settings_schema_lock:
        if _system_settings_schema_ready:
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL DEFAULT '',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_settings_updated "
            "ON system_settings(updated_at)"
        )
        conn.commit()
        _system_settings_schema_ready = True


def _ensure_bank_accounts_schema(conn):
    """Create the bank account table used by settlement-account selectors."""
    global _bank_accounts_schema_ready
    if _bank_accounts_schema_ready:
        return

    with _bank_accounts_schema_lock:
        if _bank_accounts_schema_ready:
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                account_name TEXT NOT NULL,
                account_number TEXT NOT NULL,
                bank_name TEXT NOT NULL,
                bank_code TEXT NOT NULL DEFAULT '',
                balance REAL NOT NULL DEFAULT 0,
                is_default INTEGER NOT NULL DEFAULT 0,
                card_color TEXT NOT NULL DEFAULT '#1a1a1a',
                card_bg_image TEXT NOT NULL DEFAULT '',
                bank_icon TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        columns = {
            row["name"]
            for row in cursor.execute("PRAGMA table_info(bank_accounts)").fetchall()
        }
        if "is_default" not in columns:
            cursor.execute(
                "ALTER TABLE bank_accounts ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0"
            )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bank_accounts_store
            ON bank_accounts(store_id, is_default DESC, id)
            """
        )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_bank_accounts_store_number
            ON bank_accounts(store_id, account_number)
            WHERE trim(account_number) <> ''
            """
        )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_bank_accounts_store_default
            ON bank_accounts(store_id)
            WHERE is_default = 1
            """
        )
        cursor.execute(
            """
            UPDATE bank_accounts
            SET is_default = 1
            WHERE is_default = 0
              AND id IN (
                SELECT MIN(id)
                FROM bank_accounts
                GROUP BY store_id
              )
              AND NOT EXISTS (
                SELECT 1
                FROM bank_accounts existing_default
                WHERE existing_default.store_id = bank_accounts.store_id
                  AND existing_default.is_default = 1
              )
            """
        )
        conn.commit()
        _bank_accounts_schema_ready = True


def _ensure_raw_material_products_schema(conn):
    """创建与成品结构一致、但独立存储的原材料商品表。"""
    global _raw_material_schema_ready
    if _raw_material_schema_ready:
        return

    with _raw_material_schema_lock:
        if _raw_material_schema_ready:
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_material_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT NOT NULL,
                specification TEXT,
                category INTEGER,
                unit_id INTEGER,
                enable_multi_unit INTEGER DEFAULT 0,
                notes TEXT,
                enabled INTEGER DEFAULT 1,
                warehouse_id INTEGER,
                store_ids TEXT,
                warehouse_categories TEXT,
                unit_conversions TEXT,
                enable_attributes INTEGER DEFAULT 0,
                attribute_combinations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_material_products_code "
            "ON raw_material_products(code)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_material_products_name "
            "ON raw_material_products(name)"
        )
        conn.commit()
        _raw_material_schema_ready = True


def _ensure_stock_inbound_schema(conn):
    """Create the independent stock-in document, supplier and balance tables."""
    global _stock_inbound_schema_ready
    if _stock_inbound_schema_ready:
        return

    with _stock_inbound_schema_lock:
        if _stock_inbound_schema_ready:
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_code TEXT,
                supplier_name TEXT NOT NULL,
                store_id INTEGER,
                contact_person TEXT,
                phone TEXT,
                address TEXT,
                tax_number TEXT,
                bank_name TEXT,
                bank_account TEXT,
                remark TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code "
            "ON suppliers(supplier_code) "
            "WHERE supplier_code IS NOT NULL AND trim(supplier_code) <> ''"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_suppliers_store_status "
            "ON suppliers(store_id, status)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_inbounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_no TEXT NOT NULL UNIQUE,
                document_date TEXT,
                receipt_type TEXT NOT NULL,
                store_id INTEGER,
                warehouse_id INTEGER,
                supplier_id INTEGER,
                workshop TEXT,
                inspector TEXT,
                quality_no TEXT,
                remark TEXT,
                attachments TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                total_quantity REAL NOT NULL DEFAULT 0,
                total_tax REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                posted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_inbounds_filter "
            "ON stock_inbounds(receipt_type, status, document_date DESC)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_inbound_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inbound_id INTEGER NOT NULL,
                line_no INTEGER NOT NULL,
                product_type TEXT NOT NULL,
                product_id INTEGER,
                product_code TEXT,
                product_name TEXT,
                specification TEXT,
                unit TEXT,
                expected_qty REAL,
                received_qty REAL,
                bin_code TEXT,
                batch_no TEXT,
                unit_price REAL,
                tax_rate REAL NOT NULL DEFAULT 0,
                tax_amount REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                remark TEXT,
                FOREIGN KEY(inbound_id) REFERENCES stock_inbounds(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_inbound_items_inbound "
            "ON stock_inbound_items(inbound_id, line_no)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_type TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL DEFAULT 0,
                store_id INTEGER NOT NULL DEFAULT 0,
                bin_code TEXT NOT NULL DEFAULT '',
                batch_no TEXT NOT NULL DEFAULT '',
                quantity REAL NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_type, product_id, warehouse_id, store_id, bin_code, batch_no)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_balances_lookup "
            "ON stock_balances(product_type, product_id, warehouse_id)"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_type TEXT NOT NULL,
                receipt_type TEXT NOT NULL,
                source_document_id INTEGER NOT NULL,
                source_document_no TEXT NOT NULL,
                source_item_id INTEGER,
                product_type TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL DEFAULT 0,
                store_id INTEGER NOT NULL DEFAULT 0,
                bin_code TEXT NOT NULL DEFAULT '',
                batch_no TEXT NOT NULL DEFAULT '',
                quantity REAL NOT NULL,
                unit_price REAL,
                tax_rate REAL,
                total_amount REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product "
            "ON stock_movements(product_type, product_id, warehouse_id, created_at DESC)"
        )
        conn.commit()
        _stock_inbound_schema_ready = True


def _ensure_material_outbound_schema(conn):
    """Create touch-entry material outbound documents and their settings."""
    global _material_outbound_schema_ready
    if _material_outbound_schema_ready:
        return

    with _material_outbound_schema_lock:
        if _material_outbound_schema_ready:
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS material_outbound_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                default_store_id INTEGER,
                default_warehouse_id INTEGER,
                default_product_id INTEGER,
                allowed_product_ids TEXT NOT NULL DEFAULT '[]',
                deduction_strategy TEXT NOT NULL DEFAULT 'fifo',
                allow_insufficient_draft INTEGER NOT NULL DEFAULT 1,
                show_current_stock INTEGER NOT NULL DEFAULT 1,
                updated_by TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO material_outbound_settings (
                id, allowed_product_ids, deduction_strategy,
                allow_insufficient_draft, show_current_stock
            ) VALUES (1, '[]', 'fifo', 1, 1)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS material_outbounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_no TEXT NOT NULL UNIQUE,
                document_date TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                store_name TEXT NOT NULL DEFAULT '',
                warehouse_id INTEGER NOT NULL,
                warehouse_name TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'draft',
                total_quantity REAL NOT NULL DEFAULT 0,
                produced_quantity REAL NOT NULL DEFAULT 0,
                remark TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'touch',
                created_by TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                audited_by TEXT,
                audited_at TEXT,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_material_outbounds_filter
            ON material_outbounds(status, document_date DESC, id DESC)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS material_outbound_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                outbound_id INTEGER NOT NULL,
                line_no INTEGER NOT NULL DEFAULT 1,
                product_id INTEGER NOT NULL,
                product_code TEXT,
                product_name TEXT NOT NULL,
                specification TEXT,
                unit TEXT,
                quantity REAL NOT NULL,
                remark TEXT,
                FOREIGN KEY(outbound_id) REFERENCES material_outbounds(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_material_outbound_items_document
            ON material_outbound_items(outbound_id, line_no)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS material_remark_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT NOT NULL UNIQUE,
                use_count INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_material_remark_tags_usage
            ON material_remark_tags(use_count DESC, updated_at DESC)
            """
        )
        legacy_tags_exist = cursor.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'remark_tags'
            """
        ).fetchone()
        if legacy_tags_exist:
            cursor.execute(
                """
                INSERT OR IGNORE INTO material_remark_tags (
                    tag, use_count, created_at, updated_at
                )
                SELECT trim(tag), 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                FROM remark_tags
                WHERE tag IS NOT NULL AND trim(tag) <> ''
                """
            )
        conn.commit()
        _material_outbound_schema_ready = True


def _ensure_print_templates_schema(conn):
    """创建打印模板表"""
    global _print_templates_schema_ready
    if _print_templates_schema_ready:
        return

    with _print_templates_schema_lock:
        if _print_templates_schema_ready:
            return

        cursor = conn.cursor()

        # 检查表是否存在
        table_exists = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'print_templates'"
        ).fetchone()

        if not table_exists:
            # 创建打印模板表
            cursor.execute('''
                CREATE TABLE print_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    business_type TEXT NOT NULL,
                    paper_type TEXT,
                    page_width INTEGER NOT NULL,
                    page_height INTEGER NOT NULL,
                    is_default INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    content TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            ''')

            # 创建索引
            cursor.execute('''
                CREATE INDEX idx_print_templates_business_type
                ON print_templates(business_type)
            ''')

            cursor.execute('''
                CREATE INDEX idx_print_templates_is_default
                ON print_templates(is_default)
            ''')

            # 插入默认模板
            cursor.execute('''
                INSERT INTO print_templates (
                    name, business_type, paper_type,
                    page_width, page_height, is_default, enabled
                ) VALUES
                ('销售出库单-标准模板', 'sale', '二等分', 210, 140, 1, 1),
                ('采购入库单-标准模板', 'purchase', '二等分', 210, 140, 1, 1),
                ('退货单-标准模板', 'return', '二等分', 210, 140, 1, 1)
            ''')

            conn.commit()

        _print_templates_schema_ready = True


def _ensure_return_schema(conn):
    """Create the reusable sales/raw-material return document tables."""
    global _return_schema_ready
    if _return_schema_ready:
        return

    with _return_schema_lock:
        if _return_schema_ready:
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS return_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT NOT NULL UNIQUE,
                original_order_number TEXT NOT NULL DEFAULT '',
                return_date TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                product_type TEXT NOT NULL DEFAULT 'finished-product',
                tax_enabled INTEGER NOT NULL DEFAULT 0,
                total_quantity REAL NOT NULL DEFAULT 0,
                total_packages REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                total_tax_amount REAL NOT NULL DEFAULT 0,
                total_tax_included_amount REAL NOT NULL DEFAULT 0,
                refund_amount REAL NOT NULL DEFAULT 0,
                writeoff_amount REAL NOT NULL DEFAULT 0,
                debt_before REAL NOT NULL DEFAULT 0,
                debt_after REAL NOT NULL DEFAULT 0,
                settlement_account TEXT NOT NULL DEFAULT '',
                sales_person TEXT NOT NULL DEFAULT '',
                creator TEXT NOT NULL DEFAULT '',
                packaging TEXT NOT NULL DEFAULT '',
                remark TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'completed',
                account_transaction_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS return_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                line_no INTEGER NOT NULL,
                product_type TEXT NOT NULL DEFAULT 'finished-product',
                product_id INTEGER,
                product_code TEXT NOT NULL DEFAULT '',
                goods_name TEXT NOT NULL DEFAULT '',
                specification TEXT NOT NULL DEFAULT '',
                unit TEXT NOT NULL DEFAULT '',
                warehouse_id INTEGER,
                packages REAL NOT NULL DEFAULT 0,
                quantity REAL NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0,
                amount REAL NOT NULL DEFAULT 0,
                tax_rate REAL NOT NULL DEFAULT 0,
                tax_included_price REAL NOT NULL DEFAULT 0,
                tax_amount REAL NOT NULL DEFAULT 0,
                tax_included_amount REAL NOT NULL DEFAULT 0,
                remark TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(return_id) REFERENCES return_orders(id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_return_orders_filter
            ON return_orders(store_id, return_date DESC, id DESC)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_return_orders_customer
            ON return_orders(customer_id, return_date DESC, id DESC)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_return_order_items_return
            ON return_order_items(return_id, line_no)
            """
        )
        conn.commit()
        _return_schema_ready = True


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
                    balance_at TEXT,
                    initial_receivable REAL DEFAULT 0,
                    initial_receivable_at TEXT,
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
                "balance_at": "TEXT",
                "initial_receivable": "REAL",
                "initial_receivable_at": "TEXT",
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
                initial_receivable = COALESCE(initial_receivable, receivable, 0),
                receivable = COALESCE(receivable, 0),
                status = COALESCE(NULLIF(status, ''), 'active')
            """
        )
        cursor.execute(
            """
            UPDATE customers
            SET balance_at = COALESCE(NULLIF(balance_at, ''), created_at)
            WHERE balance > 0
              AND (balance_at IS NULL OR trim(balance_at) = '')
            """
        )
        cursor.execute(
            """
            UPDATE customers
            SET initial_receivable_at = COALESCE(
                    NULLIF(initial_receivable_at, ''),
                    created_at
                )
            WHERE initial_receivable > 0
              AND (
                    initial_receivable_at IS NULL
                    OR trim(initial_receivable_at) = ''
              )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_account_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_id INTEGER,
                order_number TEXT,
                payment_id INTEGER,
                payment_number TEXT,
                transaction_type TEXT NOT NULL,
                source_transaction_id INTEGER,
                order_receivable REAL NOT NULL DEFAULT 0,
                stored_balance_applied REAL NOT NULL DEFAULT 0,
                receivable_increase REAL NOT NULL DEFAULT 0,
                debt_recovered REAL NOT NULL DEFAULT 0,
                discount_amount REAL NOT NULL DEFAULT 0,
                balance_change REAL NOT NULL DEFAULT 0,
                receivable_change REAL NOT NULL DEFAULT 0,
                balance_after REAL NOT NULL DEFAULT 0,
                receivable_after REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                operator TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reversed_at TEXT
            )
            """
        )
        account_columns = {
            row["name"]
            for row in cursor.execute(
                "PRAGMA table_info(customer_account_transactions)"
            )
        }
        if "payment_id" not in account_columns:
            cursor.execute(
                """
                ALTER TABLE customer_account_transactions
                ADD COLUMN payment_id INTEGER
                """
            )
        if "payment_number" not in account_columns:
            cursor.execute(
                """
                ALTER TABLE customer_account_transactions
                ADD COLUMN payment_number TEXT
                """
            )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_customer_account_customer
            ON customer_account_transactions(customer_id, created_at DESC)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_customer_account_order
            ON customer_account_transactions(order_id, transaction_type, status)
            """
        )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_account_active_order_audit
            ON customer_account_transactions(order_id)
            WHERE transaction_type = 'order_audit' AND status = 'active'
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_customer_account_payment
            ON customer_account_transactions(payment_id, transaction_type, status)
            """
        )
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_account_active_payment
            ON customer_account_transactions(payment_id)
            WHERE transaction_type = 'customer_payment' AND status = 'active'
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_no TEXT NOT NULL UNIQUE,
                document_date TEXT NOT NULL,
                store_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                settlement_account TEXT NOT NULL DEFAULT '',
                payment_method TEXT NOT NULL DEFAULT '',
                payment_amount REAL NOT NULL DEFAULT 0,
                discount_amount REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                writeoff_amount REAL NOT NULL DEFAULT 0,
                advance_amount REAL NOT NULL DEFAULT 0,
                debt_before REAL NOT NULL DEFAULT 0,
                debt_after REAL NOT NULL DEFAULT 0,
                balance_before REAL NOT NULL DEFAULT 0,
                balance_after REAL NOT NULL DEFAULT 0,
                creator TEXT NOT NULL DEFAULT '',
                remark TEXT NOT NULL DEFAULT '',
                attachment_url TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'draft',
                account_transaction_id INTEGER,
                audited_by TEXT,
                audited_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_payment_receipts_store_date
            ON payment_receipts(store_id, document_date DESC, id DESC)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_payment_receipts_customer
            ON payment_receipts(customer_id, document_date DESC, id DESC)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_payment_receipts_status
            ON payment_receipts(status, document_date DESC, id DESC)
            """
        )
        for table_name, column_name in (
            ("payment_receipts", "audited_by"),
            ("customer_account_transactions", "operator"),
        ):
            cursor.execute(
                f"""
                UPDATE {table_name}
                SET {column_name} = (
                    SELECT COALESCE(
                        NULLIF(trim(users.name), ''),
                        CAST(users.username AS TEXT)
                    )
                    FROM users
                    WHERE CAST(users.username AS TEXT) =
                          trim({table_name}.{column_name})
                    LIMIT 1
                )
                WHERE {column_name} IS NOT NULL
                  AND trim({column_name}) <> ''
                  AND EXISTS (
                      SELECT 1
                      FROM users
                      WHERE CAST(users.username AS TEXT) =
                            trim({table_name}.{column_name})
                  )
                """
            )

        orders_exists = cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'orders'"
        ).fetchone()
        if orders_exists:
            order_columns = {
                row["name"] for row in cursor.execute("PRAGMA table_info(orders)")
            }
            if "balance_applied" not in order_columns:
                cursor.execute(
                    """
                    ALTER TABLE orders
                    ADD COLUMN balance_applied REAL NOT NULL DEFAULT 0
                    """
                )
            if "total_packages" not in order_columns:
                cursor.execute(
                    """
                    ALTER TABLE orders
                    ADD COLUMN total_packages REAL
                    """
                )
            if "audit_by" not in order_columns:
                cursor.execute(
                    """
                    ALTER TABLE orders
                    ADD COLUMN audit_by TEXT
                    """
                )
            if "audit_date" not in order_columns:
                cursor.execute(
                    """
                    ALTER TABLE orders
                    ADD COLUMN audit_date TEXT
                    """
                )
            cursor.execute(
                """
                UPDATE orders
                SET audit_by = (
                    SELECT COALESCE(
                        NULLIF(trim(users.name), ''),
                        CAST(users.username AS TEXT)
                    )
                    FROM users
                    WHERE CAST(users.username AS TEXT) = trim(orders.audit_by)
                    LIMIT 1
                )
                WHERE audit_by IS NOT NULL
                  AND trim(audit_by) <> ''
                  AND EXISTS (
                      SELECT 1
                      FROM users
                      WHERE CAST(users.username AS TEXT) = trim(orders.audit_by)
                  )
                """
            )
            cursor.execute(
                """
                UPDATE orders
                SET balance_applied = COALESCE(balance_applied, 0)
                """
            )
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
        _ensure_units_schema(conn)
        _ensure_customer_schema(conn)
        _ensure_hr_reports_schema(conn)
        _ensure_system_settings_schema(conn)
        _ensure_bank_accounts_schema(conn)
        _ensure_raw_material_products_schema(conn)
        _ensure_stock_inbound_schema(conn)
        _ensure_material_outbound_schema(conn)
        _ensure_return_schema(conn)
        _ensure_print_templates_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
