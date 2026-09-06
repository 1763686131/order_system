# 数据库工具集

这个目录包含 SQLite 数据库相关的工具和脚本。

## 文件说明

### 核心工具

#### 1. backup_json.py
**数据备份工具** - 将 SQLite 数据库导出为 JSON 格式

```bash
# 使用方法
cd E:\order_system\backend
py tools/backup_json.py

# 输出位置
# data/backup/orders_db.json
# data/backup/products_db.json
# data/backup/customers_db.json
# ... 等
```

**使用场景**：
- 定期数据备份
- 数据迁移到其他系统
- 人工审查数据内容

---

#### 2. test_sqlite.py
**数据库测试工具** - 验证数据库完整性和功能

```bash
# 使用方法
cd E:\order_system\backend
py tools/test_sqlite.py

# 测试内容
# - 订单读取（209条）
# - 商品读取（15个）
# - 客户读取（4个）
# - 原材料读取（55条）
# - 库存读取（6条）
```

**使用场景**：
- 迁移后验证数据
- 数据库损坏检查
- 功能测试

---

### 参考文档

#### 3. models.py
**数据库表结构定义** - 完整的 SQLite 表结构

包含所有表的字段定义：
- `orders` - 订单表
- `products` - 商品表
- `inventory` - 库存表
- `customers` - 客户表
- `materials` - 原材料表
- `stores` - 门店表
- `warehouses` - 仓库表
- `users` - 用户表
- 以及其他辅助表

**使用场景**：
- 查看表结构
- 数据库设计参考
- 重建数据库

---

#### 4. migrate_to_sqlite.py
**数据迁移脚本** - 从 JSON 迁移到 SQLite

```bash
# 使用方法（仅在需要重新迁移时）
cd E:\order_system\backend
py tools/migrate_to_sqlite.py

# 注意：会删除现有数据库！
```

**使用场景**：
- 数据库损坏需要重建
- 从 JSON 备份恢复
- 调整数据结构后重新迁移

**警告**：运行此脚本会删除现有的 `order_system.db`！

---

#### 5. db.py
**数据库操作封装** - SQLite 操作函数集合

这个文件的内容已经合并到 `utils/db_helper.py`，主要作为备份保留。

包含的函数：
- `read_orders()` - 读取订单
- `write_orders()` - 写入订单
- `read_products()` - 读取商品
- `update_inventory()` - 更新库存
- 等等...

**使用场景**：
- 代码参考
- db_helper.py 出问题时的备份

---

## 快速操作指南

### 数据备份
```bash
cd E:\order_system\backend
py tools/backup_json.py
```

### 数据验证
```bash
cd E:\order_system\backend
py tools/test_sqlite.py
```

### 查看表结构
```bash
# 打开 models.py 查看
# 或使用 SQLite 工具
sqlite3 data/order_system.db ".schema"
```

### 从备份恢复
```bash
# 1. 确保有 JSON 备份文件在 data/ 目录
# 2. 运行迁移脚本
cd E:\order_system\backend
py tools/migrate_to_sqlite.py
```

---

## 维护建议

### 定期备份
建议每周或每月运行一次备份：
```bash
py tools/backup_json.py
```

### 数据验证
在以下情况运行测试：
- 数据库迁移后
- 发现数据异常时
- 重要更新前

### 文件保留
- ✅ **必须保留**: backup_json.py, test_sqlite.py
- ⚠️ **建议保留**: models.py, migrate_to_sqlite.py
- 🔶 **可选保留**: db.py

---

## 注意事项

1. **不要直接修改这些工具文件**，除非你知道自己在做什么
2. **备份文件会覆盖** data/backup/ 目录下的同名文件
3. **迁移脚本会删除现有数据库**，使用前请确认已备份
4. 所有工具都需要在 `backend` 目录下运行

---

## 相关文档

- [README_SQLITE.md](../../README_SQLITE.md) - SQLite 使用指南
- [MIGRATION_SQLITE.md](../../MIGRATION_SQLITE.md) - 迁移详细文档
- [API接口文档.md](../../docs/API接口文档.md) - API 接口说明
