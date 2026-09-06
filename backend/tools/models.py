"""
数据库模型定义（仅用于初始化和迁移工具）
生产环境请使用 backend/db.py 中的 get_db() 函数
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os
import json

# 数据库文件路径
# tools/models.py -> backend/tools/ -> backend/ -> project_root/
if os.path.exists('/app/data'):
    DB_PATH = '/app/data/order_system.db'
else:
    # 从 backend/tools/ 向上两级到项目根目录，再进入 data/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DB_PATH = os.path.join(project_root, 'data', 'order_system.db')


@contextmanager
def get_db():
    """
    数据库连接上下文管理器
    注意：此函数仅供 tools/ 目录下的迁移和备份脚本使用
    生产环境请使用 backend/db.py 中的 get_db()
    """
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


def init_db():
    """初始化数据库表结构"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT,
            permissions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 门店表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            remark TEXT,
            color TEXT,
            text_color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')

        # 仓库表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            manager TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 客户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            contact_person TEXT,
            contact_phone TEXT,
            contact_address TEXT,
            receivable REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')

        # 商品单位表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 商品属性表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            options TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        ''')

        # 商品表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
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
            updated_at TIMESTAMP,
            FOREIGN KEY (unit_id) REFERENCES units(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
        ''')

        # 库存表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            product_id INTEGER PRIMARY KEY,
            stock REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            max_stock REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        ''')

        # 订单表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            status TEXT DEFAULT 'pending',
            type INTEGER DEFAULT 0,
            date TIMESTAMP,
            completed_date TIMESTAMP,
            shipped_date TIMESTAMP,
            shipping_method INTEGER,
            shipping_custom TEXT,
            logistics_no TEXT,
            audit_state INTEGER DEFAULT 0,
            store_id INTEGER,
            order_client TEXT,
            receiver_name TEXT,
            receiver_phone TEXT,
            receiver_address TEXT,
            goods_name TEXT,
            goods_weight TEXT,
            goods_quantity TEXT,
            goods_packaging TEXT,
            logistics_service TEXT,
            remark TEXT,
            customer_id INTEGER,
            warehouse_id INTEGER,
            order_number TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            contact_address TEXT,
            project_name TEXT,
            sales_person TEXT,
            creator TEXT,
            settlement_account TEXT,
            order_goods TEXT,
            subtotal_amount REAL,
            tax_amount REAL,
            total_amount REAL,
            discount_amount REAL,
            other_fees REAL,
            should_receive REAL,
            current_payment REAL,
            current_debt REAL,
            customer_receivable REAL,
            receipt_img_url TEXT,
            freight_costs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (store_id) REFERENCES stores(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
        ''')

        # 物流记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS freight_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            carrier TEXT,
            amount REAL,
            paid_amount REAL DEFAULT 0,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
        ''')

        # 备用金表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reserve_funds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 原材料记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            used REAL DEFAULT 0,
            produced REAL DEFAULT 0,
            remark TEXT,
            date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 运营商标签表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS carrier_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 备注标签表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS remark_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_code ON products(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)')

        conn.commit()
        print("[OK] 数据库表结构创建成功")


if __name__ == '__main__':
    init_db()
