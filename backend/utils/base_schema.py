"""Schema for legacy business tables that predate the incremental migrations."""

import sqlite3
from contextlib import closing


def initialize_base_schema(database):
    """Create the missing tables without importing business records."""
    with closing(sqlite3.connect(database)) as connection:
        connection.executescript("""
            BEGIN;

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
            );

            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT NOT NULL,
                store_id INTEGER REFERENCES stores(id),
                address TEXT,
                manager TEXT,
                phone TEXT,
                status TEXT DEFAULT 'active',
                remark TEXT,
                categories TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT NOT NULL,
                specification TEXT,
                category INTEGER,
                unit_id INTEGER REFERENCES units(id),
                enable_multi_unit INTEGER DEFAULT 0,
                notes TEXT,
                enabled INTEGER DEFAULT 1,
                warehouse_id INTEGER REFERENCES warehouses(id),
                store_ids TEXT,
                warehouse_categories TEXT,
                unit_conversions TEXT,
                enable_attributes INTEGER DEFAULT 0,
                attribute_combinations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_products_code ON products(code);
            CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

            CREATE TABLE IF NOT EXISTS inventory (
                product_id INTEGER PRIMARY KEY REFERENCES products(id),
                stock REAL DEFAULT 0,
                min_stock REAL DEFAULT 0,
                max_stock REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attributes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                options TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS carrier_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

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
                store_id INTEGER REFERENCES stores(id),
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
                customer_id INTEGER REFERENCES customers(id),
                warehouse_id INTEGER REFERENCES warehouses(id),
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
                balance_applied REAL NOT NULL DEFAULT 0,
                total_packages REAL,
                audit_by TEXT,
                audit_date TEXT,
                completed_by TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
            CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(date);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

            COMMIT;
        """)
