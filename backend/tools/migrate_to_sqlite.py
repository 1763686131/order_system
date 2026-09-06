"""
将 JSON 数据迁移到 SQLite 数据库
"""
import json
import os
import sys
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from models import init_db, get_db

# 数据文件路径
# tools/migrate_to_sqlite.py -> backend/tools/ -> backend/ -> project_root/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders_db.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products_db.json')
USERS_FILE = os.path.join(DATA_DIR, 'users_db.json')
STORES_FILE = os.path.join(DATA_DIR, 'stores_db.json')
WAREHOUSES_FILE = os.path.join(DATA_DIR, 'warehouses_db.json')
CUSTOMERS_FILE = os.path.join(DATA_DIR, 'customers.json')  # 注意：文件名是 customers.json 不是 customers_db.json
MATERIAL_FILE = os.path.join(DATA_DIR, 'material_db.json')


def load_json(file_path):
    """加载 JSON 文件"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def migrate_users():
    """迁移用户数据"""
    data = load_json(USERS_FILE)
    if not data or 'users' not in data:
        return

    users = data['users']
    with get_db() as conn:
        cursor = conn.cursor()
        for user in users:
            cursor.execute('''
            INSERT INTO users (id, username, password, name, role, phone, email, avatar, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.get('id'),
                user.get('username'),
                user.get('password'),
                user.get('name'),
                user.get('role'),
                user.get('phone', ''),
                user.get('email', ''),
                user.get('avatar', ''),
                user.get('status', 'active')
            ))
        print(f"✅ 迁移 {len(users)} 个用户")


def migrate_stores():
    """迁移门店数据"""
    data = load_json(STORES_FILE)
    if not data or 'stores' not in data:
        return

    stores = data['stores']
    with get_db() as conn:
        cursor = conn.cursor()
        for store in stores:
            cursor.execute('''
            INSERT INTO stores (id, name, address, phone, manager)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                store.get('id'),
                store.get('name'),
                store.get('address', ''),
                store.get('phone', ''),
                store.get('manager', '')
            ))
        print(f"✅ 迁移 {len(stores)} 个门店")


def migrate_warehouses():
    """迁移仓库数据"""
    data = load_json(WAREHOUSES_FILE)
    if not data or 'warehouses' not in data:
        return

    warehouses = data['warehouses']
    with get_db() as conn:
        cursor = conn.cursor()
        for warehouse in warehouses:
            cursor.execute('''
            INSERT INTO warehouses (id, name, address, phone, manager)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                warehouse.get('id'),
                warehouse.get('name'),
                warehouse.get('address', ''),
                warehouse.get('phone', ''),
                warehouse.get('manager', '')
            ))
        print(f"✅ 迁移 {len(warehouses)} 个仓库")


def migrate_customers():
    """迁移客户数据"""
    data = load_json(CUSTOMERS_FILE)
    if not data or 'customers' not in data:
        return

    customers = data['customers']
    with get_db() as conn:
        cursor = conn.cursor()
        for customer in customers:
            cursor.execute('''
            INSERT INTO customers (id, customer_name, contact_person, contact_phone, contact_address, receivable, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer.get('id'),
                customer.get('customerName'),
                customer.get('contactPerson', ''),
                customer.get('phone', ''),
                customer.get('address', ''),
                customer.get('receivable', 0),
                customer.get('createdAt'),
                customer.get('updatedAt')
            ))
        print(f"✅ 迁移 {len(customers)} 个客户")


def migrate_products():
    """迁移商品数据"""
    data = load_json(PRODUCTS_FILE)
    if not data:
        return

    # 迁移单位
    units = data.get('units', [])
    with get_db() as conn:
        cursor = conn.cursor()
        for unit in units:
            cursor.execute('''
            INSERT INTO units (id, name)
            VALUES (?, ?)
            ''', (unit.get('id'), unit.get('name')))
        print(f"✅ 迁移 {len(units)} 个单位")

    # 迁移属性
    attributes = data.get('attributes', [])
    with get_db() as conn:
        cursor = conn.cursor()
        for attr in attributes:
            cursor.execute('''
            INSERT INTO attributes (id, name)
            VALUES (?, ?)
            ''', (attr.get('id'), attr.get('name')))
        print(f"✅ 迁移 {len(attributes)} 个属性")

    # 迁移商品
    products = data.get('products', [])
    with get_db() as conn:
        cursor = conn.cursor()
        for product in products:
            cursor.execute('''
            INSERT INTO products (
                id, code, name, specification, category, unit_id,
                enable_multi_unit, notes, enabled, warehouse_id,
                store_ids, warehouse_categories, unit_conversions,
                enable_attributes, attribute_combinations
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.get('id'),
                product.get('code', ''),
                product.get('name'),
                product.get('specification', ''),
                product.get('category'),
                product.get('unitId'),
                1 if product.get('enableMultiUnit') else 0,
                product.get('notes', ''),
                1 if product.get('enabled', True) else 0,
                product.get('warehouseId'),
                json.dumps(product.get('storeIds', [])),
                json.dumps(product.get('warehouseCategories', {})),
                json.dumps(product.get('unitConversions', {})),
                1 if product.get('enableAttributes') else 0,
                json.dumps(product.get('attributeCombinations', []))
            ))
        print(f"✅ 迁移 {len(products)} 个商品")

    # 迁移库存
    inventory = data.get('inventory', {})
    with get_db() as conn:
        cursor = conn.cursor()
        for product_id, inv in inventory.items():
            cursor.execute('''
            INSERT INTO inventory (product_id, stock, min_stock, max_stock, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                int(product_id),
                inv.get('stock', 0),
                inv.get('minStock', 0),
                inv.get('maxStock', 0),
                inv.get('updatedAt', datetime.now().isoformat())
            ))
        print(f"✅ 迁移 {len(inventory)} 条库存记录")


def migrate_orders():
    """迁移订单数据"""
    data = load_json(ORDERS_FILE)
    if not data or 'orders' not in data:
        return

    orders = data['orders']
    print(f"📦 开始迁移订单数据...")

    with get_db() as conn:
        cursor = conn.cursor()
        for idx, order in enumerate(orders, 1):
            # 将 goods_name 追加到 remark 中
            goods_name = order.get('goods_name', '').strip()
            original_remark = order.get('remark', '').strip()

            # 如果 goods_name 有内容，则追加到 remark
            if goods_name:
                if original_remark:
                    combined_remark = f"{original_remark}\n[商品名称]: {goods_name}"
                else:
                    combined_remark = f"[商品名称]: {goods_name}"
            else:
                combined_remark = original_remark

            cursor.execute('''
            INSERT INTO orders (
                id, title, status, type, date, completed_date, shipped_date,
                shipping_method, shipping_custom, logistics_no, audit_state,
                store_id, order_client, receiver_name, receiver_phone,
                receiver_address, goods_name, goods_weight, goods_quantity,
                goods_packaging, logistics_service, remark, customer_id,
                warehouse_id, order_number, contact_person, contact_phone,
                contact_address, project_name, sales_person, creator,
                settlement_account, order_goods, subtotal_amount, tax_amount,
                total_amount, discount_amount, other_fees, should_receive,
                current_payment, current_debt, customer_receivable,
                receipt_img_url, freight_costs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.get('id'),
                order.get('title', ''),
                order.get('status', 'pending'),
                order.get('type', 0),
                order.get('date'),
                order.get('completed_date'),
                order.get('shipped_date'),
                order.get('shipping_method'),
                order.get('shipping_custom', ''),
                order.get('logistics_no', ''),
                order.get('audit_state', 0),
                order.get('store_id'),
                order.get('order_client', ''),
                order.get('receiver_name', ''),
                order.get('receiver_phone', ''),
                order.get('receiver_address', ''),
                goods_name,  # 保留原始 goods_name
                order.get('goods_weight', ''),
                order.get('goods_quantity', ''),
                order.get('goods_packaging', ''),
                json.dumps(order.get('logistics_service', [])),
                combined_remark,  # 使用合并后的备注
                order.get('customer_id'),
                order.get('warehouse_id'),
                order.get('order_number', ''),
                order.get('contact_person', ''),
                order.get('contact_phone', ''),
                order.get('contact_address', ''),
                order.get('project_name', ''),
                order.get('sales_person', ''),
                order.get('creator', ''),
                order.get('settlement_account', ''),
                json.dumps(order.get('order_goods', [])),
                order.get('subtotal_amount'),
                order.get('tax_amount'),
                order.get('total_amount'),
                order.get('discount_amount'),
                order.get('other_fees'),
                order.get('should_receive'),
                order.get('current_payment'),
                order.get('current_debt'),
                order.get('customer_receivable'),
                order.get('receipt_img_url', ''),
                json.dumps(order.get('freight_costs', []))
            ))

            if idx % 100 == 0:
                print(f"  📊 已迁移 {idx}/{len(orders)} 条订单")

        print(f"  📊 已迁移 {len(orders)}/{len(orders)} 条订单")
        print(f"✅ 订单迁移完成，共 {len(orders)} 条")
        print(f"  ℹ️  goods_name 已追加到 remark 字段")


def migrate_materials():
    """迁移原材料数据"""
    data = load_json(MATERIAL_FILE)
    if not data:
        return

    records = data.get('records', [])
    with get_db() as conn:
        cursor = conn.cursor()
        for record in records:
            cursor.execute('''
            INSERT INTO material_records (id, used, produced, remark, date)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                record.get('id'),
                record.get('used', 0),
                record.get('produced', 0),
                record.get('remark', ''),
                record.get('date')
            ))
        print(f"✅ 迁移 {len(records)} 条原材料记录")

    # 迁移备注标签
    tags = data.get('remark_tags', [])
    if tags:
        with get_db() as conn:
            cursor = conn.cursor()
            for tag in tags:
                cursor.execute('INSERT INTO remark_tags (tag) VALUES (?)', (tag,))
            print(f"✅ 迁移 {len(tags)} 个运营商标签")


def main():
    print("\n开始数据迁移...")
    print("=" * 50)

    print("\n>> 步骤 1: 创建数据库表结构")
    init_db()
    print("[OK] 数据库表结构创建成功")

    print("\n>> 步骤 2: 迁移基础数据")
    migrate_users()
    migrate_stores()
    migrate_warehouses()
    migrate_customers()

    print("\n>> 步骤 3: 迁移商品数据")
    migrate_products()

    print("\n>> 步骤 4: 迁移订单数据")
    migrate_orders()

    print("\n>> 步骤 5: 迁移其他数据")
    migrate_materials()

    print("\n" + "=" * 50)
    print(">> 数据迁移完成！")
    print(f"数据库文件: {os.path.join(DATA_DIR, 'order_system.db')}")


if __name__ == '__main__':
    main()
