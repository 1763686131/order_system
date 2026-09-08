"""
将 SQLite 数据库导出回 JSON 格式（用于备份）
"""
import json
import os
import sys
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from models import get_db

# 备份目录
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'backup')
os.makedirs(BACKUP_DIR, exist_ok=True)


def export_to_json():
    """导出所有数据到 JSON"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    with get_db() as conn:
        cursor = conn.cursor()

        # 导出订单
        cursor.execute('SELECT * FROM orders ORDER BY id')
        orders = []
        for row in cursor.fetchall():
            order = dict(row)
            # 解析 JSON 字段，物流服务兼容旧数组和新字符串。
            for field in ['logistics_service', 'order_goods', 'freight_costs']:
                raw_value = order.get(field)
                if not raw_value:
                    continue
                try:
                    order[field] = json.loads(raw_value)
                except (TypeError, ValueError, json.JSONDecodeError):
                    order[field] = raw_value
            orders.append(order)

        orders_file = os.path.join(BACKUP_DIR, f'orders_backup_{timestamp}.json')
        with open(orders_file, 'w', encoding='utf-8') as f:
            json.dump({'orders': orders}, f, ensure_ascii=False, indent=2)
        print(f"[OK] 订单备份完成: {orders_file}")

        # 导出商品
        cursor.execute('SELECT * FROM products ORDER BY id')
        products = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT * FROM units ORDER BY id')
        measurements = []
        packagings = []
        for row in cursor.fetchall():
            unit = dict(row)
            unit['createdAt'] = unit.pop('created_at', None)
            unit_type = unit.pop('unit_type', 'measurement') or 'measurement'
            if unit_type == 'packaging':
                packagings.append(unit)
            else:
                measurements.append(unit)

        cursor.execute('SELECT * FROM inventory')
        inventory = {}
        for row in cursor.fetchall():
            inv = dict(row)
            inventory[str(inv['product_id'])] = {
                'stock': inv['stock'],
                'minStock': inv['min_stock'],
                'maxStock': inv['max_stock'],
                'updatedAt': inv['updated_at']
            }

        products_file = os.path.join(BACKUP_DIR, f'products_backup_{timestamp}.json')
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump({
                'units': {
                    'measurements': measurements,
                    'packagings': packagings
                },
                'products': products,
                'inventory': inventory
            }, f, ensure_ascii=False, indent=2)
        print(f"[OK] 商品备份完成: {products_file}")

        print(f"\n[OK] 所有数据已备份到: {BACKUP_DIR}")


if __name__ == '__main__':
    export_to_json()
