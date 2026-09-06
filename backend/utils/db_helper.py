"""
SQLite 数据库操作辅助函数（替代原 db_helper.py）
"""
import sqlite3
import json
from contextlib import contextmanager
from threading import Lock
from utils.db import get_db

# 线程锁
orders_lock = Lock()
users_lock = Lock()
products_lock = Lock()


# ==========================================
# 用户相关
# ==========================================

def read_users():
    """读取所有用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        rows = cursor.fetchall()

        users = []
        for row in rows:
            user = dict(row)
            # 解析 permissions JSON
            if user.get('permissions'):
                user['permissions'] = json.loads(user['permissions'])
            else:
                user['permissions'] = []
            users.append(user)
        return users


def write_users(users_list):
    """批量写入用户（用于兼容旧代码）"""
    with get_db() as conn:
        cursor = conn.cursor()
        # 清空表
        cursor.execute('DELETE FROM users')

        for user in users_list:
            permissions_json = json.dumps(user.get('permissions', []))
            cursor.execute('''
            INSERT INTO users (username, password, role, name, permissions)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                user.get('username'),
                user.get('password'),
                user.get('role', 'employee'),
                user.get('name', user.get('username')),
                permissions_json
            ))


# ==========================================
# 门店相关
# ==========================================

def read_stores():
    """读取所有门店"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stores ORDER BY id')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def write_stores(stores_list):
    """批量写入门店"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM stores')

        for store in stores_list:
            cursor.execute('''
            INSERT INTO stores (id, name, address, phone)
            VALUES (?, ?, ?, ?)
            ''', (
                store.get('id'),
                store.get('name'),
                store.get('address', ''),
                store.get('phone', '')
            ))


# ==========================================
# 仓库相关
# ==========================================

def read_warehouses():
    """读取所有仓库"""
    import json
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM warehouses ORDER BY id')
        rows = cursor.fetchall()
        warehouses = []
        for row in rows:
            warehouse = dict(row)
            # 将 store_id 转换为 storeId (前端使用驼峰命名)
            if 'store_id' in warehouse:
                warehouse['storeId'] = warehouse.pop('store_id')
            # 解析 categories JSON 字符串
            if 'categories' in warehouse and warehouse['categories']:
                try:
                    warehouse['categories'] = json.loads(warehouse['categories'])
                except:
                    warehouse['categories'] = []
            else:
                warehouse['categories'] = []
            warehouses.append(warehouse)
        return warehouses


def write_warehouses(warehouses_list):
    """批量写入仓库"""
    import json
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM warehouses')

        for warehouse in warehouses_list:
            # 处理 storeId -> store_id 转换
            store_id = warehouse.get('storeId') or warehouse.get('store_id')

            # 处理 categories
            categories = warehouse.get('categories', [])
            if isinstance(categories, list):
                categories = json.dumps(categories, ensure_ascii=False)

            cursor.execute('''
            INSERT INTO warehouses (
                id, code, name, store_id, address, manager, phone,
                status, remark, categories, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                warehouse.get('id'),
                warehouse.get('code', ''),
                warehouse.get('name'),
                store_id,
                warehouse.get('address', ''),
                warehouse.get('manager', ''),
                warehouse.get('phone', ''),
                warehouse.get('status', 'active'),
                warehouse.get('remark', ''),
                categories,
                warehouse.get('created_at', ''),
                warehouse.get('updated_at', '')
            ))


# ==========================================
# 商品相关
# ==========================================

def read_products():
    """读取商品数据（兼容 JSON 格式）"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 读取单位
        cursor.execute('SELECT * FROM units ORDER BY id')
        units = [dict(row) for row in cursor.fetchall()]

        # 读取属性
        cursor.execute('SELECT * FROM attributes ORDER BY id')
        attributes = []
        for row in cursor.fetchall():
            attr = dict(row)
            if attr.get('options'):
                attr['options'] = json.loads(attr['options'])
            attributes.append(attr)

        # 读取商品
        cursor.execute('SELECT * FROM products ORDER BY id')
        products = []
        for row in cursor.fetchall():
            product = dict(row)
            # 解析 JSON 字段
            for field in ['storeIds', 'warehouseCategories', 'unitConversions', 'attributeCombinations']:
                json_field = 'store_ids' if field == 'storeIds' else \
                            'warehouse_categories' if field == 'warehouseCategories' else \
                            'unit_conversions' if field == 'unitConversions' else \
                            'attribute_combinations'
                if product.get(json_field):
                    product[field] = json.loads(product[json_field])
                else:
                    product[field] = [] if field != 'warehouseCategories' else {}

            # 字段名转换（数据库用下划线，JSON 用驼峰）
            product['unitId'] = product.pop('unit_id')
            product['enableMultiUnit'] = product.pop('enable_multi_unit')
            product['warehouseId'] = product.pop('warehouse_id')
            product['enableAttributes'] = product.pop('enable_attributes')
            product['createdAt'] = product.pop('created_at')
            product['updatedAt'] = product.pop('updated_at', None)

            products.append(product)

        # 读取库存
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

        return {
            'units': units,
            'attributes': attributes,
            'products': products,
            'inventory': inventory
        }


def write_products(products_data):
    """写入商品数据"""
    with products_lock:
        with get_db() as conn:
            cursor = conn.cursor()

            # 更新商品（如果有变化）
            if 'products' in products_data:
                for product in products_data['products']:
                    cursor.execute('''
                    UPDATE products SET
                        code = ?, name = ?, specification = ?, category = ?,
                        unit_id = ?, enable_multi_unit = ?, notes = ?, enabled = ?,
                        warehouse_id = ?, store_ids = ?, warehouse_categories = ?,
                        unit_conversions = ?, enable_attributes = ?, attribute_combinations = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''', (
                        product.get('code'),
                        product.get('name'),
                        product.get('specification'),
                        product.get('category'),
                        product.get('unitId'),
                        product.get('enableMultiUnit', False),
                        product.get('notes', ''),
                        product.get('enabled', True),
                        product.get('warehouseId'),
                        json.dumps(product.get('storeIds', [])),
                        json.dumps(product.get('warehouseCategories', {})),
                        json.dumps(product.get('unitConversions', [])),
                        product.get('enableAttributes', False),
                        json.dumps(product.get('attributeCombinations', [])),
                        product.get('id')
                    ))

            # 更新库存
            if 'inventory' in products_data:
                inventory = products_data['inventory']
                for product_id, inv in inventory.items():
                    cursor.execute('''
                    INSERT OR REPLACE INTO inventory (product_id, stock, min_stock, max_stock, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        int(product_id),
                        inv.get('stock', 0),
                        inv.get('minStock', 0),
                        inv.get('maxStock', 0),
                        inv.get('updatedAt', 'CURRENT_TIMESTAMP')
                    ))


# ==========================================
# 订单相关
# ==========================================

def read_orders():
    """读取订单数据（兼容 JSON 格式）"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders ORDER BY id DESC')
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            order = dict(row)

            # 解析 JSON 字段
            for field in ['logistics_service', 'order_goods', 'freight_costs']:
                if order.get(field):
                    order[field] = json.loads(order[field])
                else:
                    order[field] = []

            # 字段名转换（数据库用下划线，前端用驼峰）
            order_converted = {
                'id': order['id'],
                'title': order['title'],
                'status': order['status'],
                'type': order['type'],
                'date': order['date'],
                'completed_date': order['completed_date'],
                'shipped_date': order['shipped_date'],
                'shipping_method': order['shipping_method'],
                'shipping_custom': order['shipping_custom'],
                'logistics_no': order['logistics_no'],
                'audit_state': order['audit_state'],
                'store_id': order['store_id'],
                'order_client': order['order_client'],
                'receiver_name': order['receiver_name'],
                'receiver_phone': order['receiver_phone'],
                'receiver_address': order['receiver_address'],
                'goods_name': order['goods_name'],
                'goods_weight': order['goods_weight'],
                'goods_quantity': order['goods_quantity'],
                'goods_packaging': order['goods_packaging'],
                'logistics_service': order['logistics_service'],
                'remark': order['remark'],
                'customer_id': order['customer_id'],
                'warehouse_id': order['warehouse_id'],
                'order_number': order['order_number'],
                'contact_person': order['contact_person'],
                'contact_phone': order['contact_phone'],
                'contact_address': order['contact_address'],
                'project_name': order['project_name'],
                'sales_person': order['sales_person'],
                'creator': order['creator'],
                'settlement_account': order['settlement_account'],
                'order_goods': order['order_goods'],
                'subtotal_amount': order['subtotal_amount'],
                'tax_amount': order['tax_amount'],
                'total_amount': order['total_amount'],
                'discount_amount': order['discount_amount'],
                'other_fees': order['other_fees'],
                'should_receive': order['should_receive'],
                'current_payment': order['current_payment'],
                'current_debt': order['current_debt'],
                'customer_receivable': order['customer_receivable'],
                'receipt_img_url': order['receipt_img_url'],
                'freight_costs': order['freight_costs']
            }

            orders.append(order_converted)

        return {'orders': orders}


def write_orders(orders_data):
    """写入订单数据"""
    with orders_lock:
        with get_db() as conn:
            cursor = conn.cursor()

            orders = orders_data.get('orders', [])
            for order in orders:
                # 检查订单是否存在
                cursor.execute('SELECT id FROM orders WHERE id = ?', (order['id'],))
                exists = cursor.fetchone()

                if exists:
                    # 更新订单
                    cursor.execute('''
                    UPDATE orders SET
                        title = ?, status = ?, type = ?, date = ?, completed_date = ?,
                        shipped_date = ?, shipping_method = ?, shipping_custom = ?,
                        logistics_no = ?, audit_state = ?, store_id = ?, order_client = ?,
                        receiver_name = ?, receiver_phone = ?, receiver_address = ?,
                        goods_name = ?, goods_weight = ?, goods_quantity = ?,
                        goods_packaging = ?, logistics_service = ?, remark = ?,
                        customer_id = ?, warehouse_id = ?, order_number = ?,
                        contact_person = ?, contact_phone = ?, contact_address = ?,
                        project_name = ?, sales_person = ?, creator = ?,
                        settlement_account = ?, order_goods = ?, subtotal_amount = ?,
                        tax_amount = ?, total_amount = ?, discount_amount = ?,
                        other_fees = ?, should_receive = ?, current_payment = ?,
                        current_debt = ?, customer_receivable = ?, receipt_img_url = ?,
                        freight_costs = ?
                    WHERE id = ?
                    ''', (
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
                        order.get('goods_name', ''),
                        order.get('goods_weight', ''),
                        order.get('goods_quantity', ''),
                        order.get('goods_packaging', ''),
                        json.dumps(order.get('logistics_service', [])),
                        order.get('remark', ''),
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
                        json.dumps(order.get('freight_costs', [])),
                        order['id']
                    ))
                else:
                    # 插入新订单
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
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
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
                        order.get('goods_name', ''),
                        order.get('goods_weight', ''),
                        order.get('goods_quantity', ''),
                        order.get('goods_packaging', ''),
                        json.dumps(order.get('logistics_service', [])),
                        order.get('remark', ''),
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


# ==========================================
# 原材料相关
# ==========================================

def read_materials():
    """读取原材料数据"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 读取所有记录
        cursor.execute('SELECT * FROM material_records ORDER BY date DESC')
        rows = cursor.fetchall()
        records = [dict(row) for row in rows]

        # 计算总库存：produced - used
        total_stock = sum(r.get('produced', 0) - r.get('used', 0) for r in records)

        # 读取备注标签
        cursor.execute('SELECT DISTINCT tag FROM remark_tags ORDER BY id')
        tags = [row['tag'] for row in cursor.fetchall()]

        return {
            'total_stock': total_stock,
            'records': records,
            'remark_tags': tags
        }


def write_materials(data):
    """写入原材料数据"""
    with get_db() as conn:
        cursor = conn.cursor()

        # 更新或插入记录
        records = data.get('records', [])
        for record in records:
            record_id = record.get('id')
            if record_id:
                # 检查记录是否存在
                cursor.execute('SELECT id FROM material_records WHERE id = ?', (record_id,))
                if cursor.fetchone():
                    # 更新
                    cursor.execute('''
                    UPDATE material_records
                    SET used = ?, produced = ?, remark = ?, date = ?
                    WHERE id = ?
                    ''', (
                        record.get('used', 0),
                        record.get('produced', 0),
                        record.get('remark', ''),
                        record.get('date'),
                        record_id
                    ))
                else:
                    # 插入
                    cursor.execute('''
                    INSERT INTO material_records (id, used, produced, remark, date)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        record_id,
                        record.get('used', 0),
                        record.get('produced', 0),
                        record.get('remark', ''),
                        record.get('date')
                    ))

        # 更新备注标签
        tags = data.get('remark_tags', [])
        if tags:
            # 清空旧标签并插入新标签
            cursor.execute('DELETE FROM remark_tags')
            for tag in tags:
                cursor.execute('INSERT INTO remark_tags (tag) VALUES (?)', (tag,))



# ==========================================
# 物流记录相关
# ==========================================

def read_freight_records():
    """读取物流记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM freight_records ORDER BY created_at DESC')
        rows = cursor.fetchall()
        freight_records = [dict(row) for row in rows]

        cursor.execute('SELECT * FROM reserve_funds ORDER BY created_at DESC')
        rows = cursor.fetchall()
        reserve_funds = [dict(row) for row in rows]

        return {
            'freight_records': freight_records,
            'reserve_funds': reserve_funds
        }


def write_freight_records(data):
    """写入物流记录"""
    pass


# ==========================================
# 客户相关
# ==========================================

def read_customers():
    """读取所有客户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY id DESC')
        rows = cursor.fetchall()
        customers = []
        for row in rows:
            customer = dict(row)
            # 转换字段名：customer_code -> customerCode
            customer['customerCode'] = customer.pop('customer_code', '')
            customer['customerName'] = customer.pop('customer_name', '')
            customer['storeId'] = customer.pop('store_id', None)
            customer['contactPerson'] = customer.pop('contact_person', '')
            customer['bankName'] = customer.pop('bank_name', '')
            customer['bankAccount'] = customer.pop('bank_account', '')
            customer['bankCode'] = customer.pop('bank_code', '')
            customer['taxNumber'] = customer.pop('tax_number', '')
            customer['createdAt'] = customer.pop('created_at', '')
            customer['updatedAt'] = customer.pop('updated_at', '')
            customers.append(customer)
        return {'customers': customers}


def write_customers(customers_data):
    """写入客户数据（批量更新）"""
    customers_list = customers_data.get('customers', [])

    with get_db() as conn:
        cursor = conn.cursor()
        # 清空表
        cursor.execute('DELETE FROM customers')

        for customer in customers_list:
            cursor.execute('''
            INSERT INTO customers (
                id, customer_code, customer_name, store_id,
                contact_person, phone, address,
                balance, receivable,
                bank_name, bank_account, bank_code, tax_number,
                remark, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer.get('id'),
                customer.get('customerCode', ''),
                customer.get('customerName', ''),
                customer.get('storeId'),
                customer.get('contactPerson', ''),
                customer.get('phone', ''),
                customer.get('address', ''),
                customer.get('balance', 0),
                customer.get('receivable', 0),
                customer.get('bankName', ''),
                customer.get('bankAccount', ''),
                customer.get('bankCode', ''),
                customer.get('taxNumber', ''),
                customer.get('remark', ''),
                customer.get('status', 'active'),
                customer.get('createdAt', ''),
                customer.get('updatedAt', '')
            ))
        conn.commit()


# ==========================================
# 承运商标签相关
# ==========================================

def read_carrier_tags():
    """读取承运商标签"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT tag FROM carrier_tags ORDER BY id DESC LIMIT 20')
        rows = cursor.fetchall()
        return [row['tag'] for row in rows]


def write_carrier_tags(tags):
    """写入承运商标签"""
    with get_db() as conn:
        cursor = conn.cursor()
        # 清空表
        cursor.execute('DELETE FROM carrier_tags')

        # 插入标签
        for tag in tags:
            cursor.execute('INSERT INTO carrier_tags (tag) VALUES (?)', (tag,))

        conn.commit()
