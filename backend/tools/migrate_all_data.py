#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整数据迁移脚本 - 根据实际表结构迁移所有 JSON 数据
"""

import json
import sqlite3
import sys
import os
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.db import get_db

def migrate_stores():
    """迁移门店数据"""
    print("\n=== 迁移门店数据 ===")

    with open('../../data/stores_db.json', 'r', encoding='utf-8') as f:
        stores = json.load(f)

    with get_db() as conn:
        cursor = conn.cursor()

        # 清空旧数据
        cursor.execute("DELETE FROM stores")

        for store in stores:
            cursor.execute("""
                INSERT INTO stores (
                    id, code, name, status, remark,
                    color, text_color, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                store['id'],
                store.get('code', ''),
                store['name'],
                store.get('status', 'active'),
                store.get('remark', ''),
                store.get('color', ''),
                store.get('textColor', ''),
                store.get('createdAt', ''),
                store.get('updatedAt', '')
            ))

        conn.commit()
        print(f"✅ 已迁移 {len(stores)} 个门店")

def migrate_units():
    """迁移单位数据"""
    print("\n=== 迁移单位数据 ===")

    with open('../../data/products_db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    units = data.get('units', [])

    with get_db() as conn:
        cursor = conn.cursor()

        # 清空旧数据
        cursor.execute("DELETE FROM units")

        for unit in units:
            cursor.execute("""
                INSERT INTO units (id, name, created_at)
                VALUES (?, ?, ?)
            """, (
                unit['id'],
                unit['name'],
                unit.get('createdAt', '')
            ))

        conn.commit()
        print(f"✅ 已迁移 {len(units)} 个单位")

def migrate_attributes():
    """迁移属性数据"""
    print("\n=== 迁移属性数据 ===")

    with open('../../data/products_db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    attributes = data.get('attributes', [])

    with get_db() as conn:
        cursor = conn.cursor()

        # 清空旧数据
        cursor.execute("DELETE FROM attributes")

        for attr in attributes:
            cursor.execute("""
                INSERT INTO attributes (id, name, options, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                attr['id'],
                attr['name'],
                json.dumps(attr.get('options', []), ensure_ascii=False),
                attr.get('createdAt', ''),
                attr.get('updatedAt', '')
            ))

        conn.commit()
        print(f"✅ 已迁移 {len(attributes)} 个属性")

def migrate_products():
    """迁移商品数据"""
    print("\n=== 迁移商品数据 ===")

    with open('../../data/products_db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    products = data.get('products', [])

    with get_db() as conn:
        cursor = conn.cursor()

        # 清空旧数据
        cursor.execute("DELETE FROM products")

        for product in products:
            cursor.execute("""
                INSERT INTO products (
                    id, code, name, specification, category, unit_id,
                    enable_multi_unit, notes, enabled, warehouse_id,
                    store_ids, warehouse_categories, unit_conversions,
                    enable_attributes, attribute_combinations,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product['id'],
                product.get('code', ''),
                product['name'],
                product.get('specification', ''),
                product.get('category'),
                product.get('unitId'),
                1 if product.get('enableMultiUnit') else 0,
                product.get('notes', ''),
                1 if product.get('enabled', True) else 0,
                product.get('warehouseId'),
                json.dumps(product.get('storeIds', []), ensure_ascii=False),
                json.dumps(product.get('warehouseCategories', {}), ensure_ascii=False),
                json.dumps(product.get('unitConversions', []), ensure_ascii=False),
                1 if product.get('enableAttributes') else 0,
                json.dumps(product.get('attributeCombinations', []), ensure_ascii=False),
                product.get('createdAt', ''),
                product.get('updatedAt', '')
            ))

        conn.commit()
        print(f"✅ 已迁移 {len(products)} 个商品")

def migrate_warehouses():
    """迁移仓库数据"""
    print("\n=== 迁移仓库数据 ===")

    json_path = '../../data/warehouses_db.json'
    if not os.path.exists(json_path):
        print("⚠️ warehouses_db.json 不存在，跳过")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        warehouses = json.load(f)

    with get_db() as conn:
        cursor = conn.cursor()

        # 清空旧数据
        cursor.execute("DELETE FROM warehouses")

        for wh in warehouses:
            cursor.execute("""
                INSERT INTO warehouses (
                    id, name, address, manager, phone, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                wh['id'],
                wh['name'],
                wh.get('address', ''),
                wh.get('manager', ''),
                wh.get('phone', ''),
                wh.get('createdAt', '')
            ))

        conn.commit()
        print(f"✅ 已迁移 {len(warehouses)} 个仓库")

def migrate_users():
    """迁移用户数据"""
    print("\n=== 迁移用户数据 ===")

    json_path = '../../data/users_db.json'
    if not os.path.exists(json_path):
        print("⚠️ users_db.json 不存在，跳过")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        users = json.load(f)

    with get_db() as conn:
        cursor = conn.cursor()

        # 清空旧数据
        cursor.execute("DELETE FROM users")

        for user in users:
            # 用户数据没有 id，让数据库自动生成
            cursor.execute("""
                INSERT INTO users (
                    username, password, role, name, permissions, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user['username'],
                user['password'],
                user.get('role', ''),
                user.get('name', ''),
                json.dumps(user.get('permissions', []), ensure_ascii=False),
                ''  # 没有 createdAt
            ))

        conn.commit()
        print(f"✅ 已迁移 {len(users)} 个用户")

def verify_data():
    """验证迁移结果"""
    print("\n" + "="*50)
    print("=== 验证迁移结果 ===")
    print("="*50)

    with get_db() as conn:
        cursor = conn.cursor()

        tables = [
            ('stores', '门店'),
            ('units', '单位'),
            ('attributes', '属性'),
            ('products', '商品'),
            ('warehouses', '仓库'),
            ('users', '用户'),
            ('orders', '订单')
        ]

        for table, name in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {name}({table}): {count} 条记录")

if __name__ == '__main__':
    print("="*50)
    print("开始迁移所有数据（除订单外）")
    print("="*50)

    from utils.db import DB_PATH
    print(f"\n数据库路径: {DB_PATH}")
    print(f"数据库存在: {os.path.exists(DB_PATH)}")
    if os.path.exists(DB_PATH):
        print(f"数据库大小: {os.path.getsize(DB_PATH) / 1024:.1f} KB\n")

    try:
        migrate_stores()
        migrate_units()
        migrate_attributes()
        migrate_products()
        migrate_warehouses()
        migrate_users()

        verify_data()

        print("\n" + "="*50)
        print("✅ 所有数据迁移完成！")
        print("="*50)

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
