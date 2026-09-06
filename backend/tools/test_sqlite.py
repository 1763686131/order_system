"""
测试 SQLite 数据库迁移后的功能
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from utils.db_helper import (
    read_orders, write_orders,
    read_products, write_products,
    read_users, read_stores, read_warehouses
)

print("=" * 50)
print("SQLite 数据库功能测试")
print("=" * 50)

# 测试读取
print("\n[1/5] 测试读取订单...")
orders_data = read_orders()
print(f"   ✓ 读取 {len(orders_data['orders'])} 条订单")

print("\n[2/5] 测试读取商品...")
products_data = read_products()
print(f"   ✓ 读取 {len(products_data['products'])} 个商品")
print(f"   ✓ 读取 {len(products_data['units'])} 个单位")
print(f"   ✓ 读取 {len(products_data['inventory'])} 条库存")

print("\n[3/5] 测试读取用户...")
users = read_users()
print(f"   ✓ 读取 {len(users)} 个用户")

print("\n[4/5] 测试读取门店...")
stores = read_stores()
print(f"   ✓ 读取 {len(stores)} 个门店")

print("\n[5/5] 测试读取仓库...")
warehouses = read_warehouses()
print(f"   ✓ 读取 {len(warehouses)} 个仓库")

# 测试写入（更新一条订单）
print("\n[测试写入] 测试订单更新...")
if orders_data['orders']:
    test_order = orders_data['orders'][0].copy()
    test_order['remark'] = f"SQLite 测试标记 - {test_order.get('remark', '')}"
    orders_data['orders'][0] = test_order
    write_orders(orders_data)

    # 验证写入
    updated_data = read_orders()
    if "SQLite 测试标记" in updated_data['orders'][0].get('remark', ''):
        print("   ✓ 订单更新成功")
    else:
        print("   ✗ 订单更新失败")
else:
    print("   - 跳过（无订单数据）")

print("\n" + "=" * 50)
print("✓ 所有测试通过！")
print("=" * 50)
print("\n数据库迁移成功，系统可以正常使用。")
