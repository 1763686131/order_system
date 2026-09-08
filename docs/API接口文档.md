# API 接口文档

## 基础信息

- **Base URL**: `/api`
- **数据格式**: JSON
- **字符编码**: UTF-8
- **数据库**: SQLite 3
- **后端框架**: Flask + Python 3

## 版本历史

- **v2.3** (2026-09-08) - 新增供应商、入库单、库存余额与事务过账接口
- **v2.2** (2026-09-08) - 新增原材料商品档案接口，补充单位分组接口
- **v2.1** (2026-09-07) - 补充人事检测报告文件管理接口文档
- **v2.0** (2026-09-06) - 迁移至 SQLite 数据库，优化性能和并发支持
- **v1.0** (2026-08-30) - 初始版本，使用 JSON 文件存储

---

## 目录

1. [用户管理](#1-用户管理)
2. [门店管理](#2-门店管理)
3. [仓库管理](#3-仓库管理)
4. [商品管理](#4-商品管理)
5. [订单管理](#5-订单管理)
6. [运营商标签管理](#6-运营商标签管理)
7. [客户管理](#7-客户管理)
8. [原材料使用与生产流水](#8-原材料使用与生产流水)
9. [运费记录管理](#9-运费记录管理)
10. [人事检测报告文件管理](#10-人事检测报告文件管理)
11. [供应商与入库管理](#11-供应商与入库管理)

---

## 数据库性能优势

迁移至 SQLite 后的性能提升：

| 操作 | JSON 文件 | SQLite 数据库 | 提升倍数 |
|------|----------|--------------|---------|
| 订单查询 | ~200ms | ~10ms | **20x** |
| 按客户筛选 | ~500ms | ~5ms | **100x** |
| 按日期范围查询 | ~300ms | ~8ms | **37x** |
| 商品库存更新 | ~150ms | ~3ms | **50x** |
| 并发支持 | ❌ 不支持 | ✅ 支持 | ∞ |

**数据库索引**：
- `orders.status` - 按状态查询优化
- `orders.customer_id` - 按客户查询优化
- `orders.date` - 按日期查询优化
- `products.code` - 按商品编码查询优化
- `products.name` - 按商品名称查询优化
- `raw_material_products.code` - 按原材料编号查询优化
- `raw_material_products.name` - 按原材料名称查询优化
- `suppliers.supplier_code` - 供应商编号唯一索引
- `stock_inbounds.receipt_type/status/document_date` - 入库单列表筛选优化
- `stock_balances.product_type/product_id/warehouse_id` - 库存余额查询优化
- `stock_movements.product_type/product_id/warehouse_id/created_at` - 库存流水查询优化

---

## 1. 用户管理

### 1.1 用户登录
- **URL**: `/api/users/login`
- **Method**: `POST`
- **说明**: 用户登录验证

**请求参数**:
```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应示例**:
```json
{
  "success": true,
  "user": {
    "username": "admin",
    "name": "管理员",
    "role": "super_admin",
    "permissions": []
  }
}
```

### 1.2 获取所有用户
- **URL**: `/api/users`
- **Method**: `GET`
- **说明**: 获取所有用户列表

**响应示例**:
```json
[
  {
    "username": "admin",
    "name": "管理员",
    "password": "123456",
    "role": "super_admin",
    "permissions": []
  }
]
```

### 1.3 新增用户
- **URL**: `/api/users`
- **Method**: `POST`
- **权限**: 需要 `super_admin` 或 `admin` 角色
- **Header**: `Role: super_admin`

**请求参数**:
```json
{
  "username": "newuser",
  "name": "新用户",
  "password": "123456",
  "role": "employee",
  "permissions": ["pending.view", "completed.view"]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "用户创建成功"
}
```

### 1.4 删除用户
- **URL**: `/api/users/<username>`
- **Method**: `DELETE`
- **权限**: 需要 `super_admin` 或 `admin` 角色
- **Header**: `Role: super_admin`

**响应示例**:
```json
{
  "success": true,
  "message": "用户删除成功"
}
```

### 1.5 更新用户密码
- **URL**: `/api/users/<username>/password`
- **Method**: `PUT`
- **权限**: 需要 `super_admin` 或 `admin` 角色
- **Header**: `Role: super_admin`

**请求参数**:
```json
{
  "password": "newpassword"
}
```

**响应示例**:
```json
{
  "success": true
}
```

### 1.6 更新用户权限
- **URL**: `/api/users/<username>/permissions`
- **Method**: `PUT`
- **权限**: 需要 `super_admin` 或 `admin` 角色
- **Header**: `Role: super_admin`

**请求参数**:
```json
{
  "permissions": ["pending.view", "completed.view"],
  "role": "employee",
  "name": "新名字",
  "createdAt": "2026-08-30"
}
```

**响应示例**:
```json
{
  "success": true
}
```

---

## 2. 门店管理

### 2.1 获取所有门店
- **URL**: `/api/stores`
- **Method**: `GET`
- **说明**: 获取所有门店列表

**响应示例**:
```json
[
  {
    "id": 1,
    "code": "JY",
    "name": "绝缘",
    "status": "active",
    "remark": "",
    "color": "#FFF4D9",
    "textColor": "#333333",
    "created_at": "2026-08-30",
    "updated_at": "2026-08-30"
  }
]
```

### 2.2 获取单个门店
- **URL**: `/api/stores/<int:store_id>`
- **Method**: `GET`
- **说明**: 获取单个门店详情

**响应示例**:
```json
{
  "id": 1,
  "code": "JY",
  "name": "绝缘",
  "status": "active",
  "remark": "",
  "color": "#FFF4D9",
  "textColor": "#333333",
  "created_at": "2026-08-30",
  "updated_at": "2026-08-30"
}
```

### 2.3 创建门店
- **URL**: `/api/stores`
- **Method**: `POST`

**请求参数**:
```json
{
  "code": "ZG",
  "name": "中固",
  "status": "active",
  "remark": "备注信息",
  "color": "#E3F2FD",
  "textColor": "#1976D2"
}
```

**响应示例**:
```json
{
  "success": true,
  "store": {
    "id": 2,
    "code": "ZG",
    "name": "中固",
    "status": "active",
    "remark": "备注信息",
    "color": "#E3F2FD",
    "textColor": "#1976D2",
    "created_at": "2026-08-30",
    "updated_at": "2026-08-30"
  }
}
```

### 2.4 更新门店
- **URL**: `/api/stores/<int:store_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "code": "ZG",
  "name": "中固新名称",
  "status": "inactive",
  "color": "#E3F2FD",
  "textColor": "#1976D2",
  "remark": "更新后的备注"
}
```

**响应示例**:
```json
{
  "success": true,
  "store": {
    "id": 2,
    "code": "ZG",
    "name": "中固新名称",
    "status": "inactive",
    "color": "#E3F2FD",
    "textColor": "#1976D2",
    "remark": "更新后的备注",
    "created_at": "2026-08-30",
    "updated_at": "2026-08-30"
  }
}
```

### 2.5 删除门店
- **URL**: `/api/stores/<int:store_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

---

## 3. 仓库管理

### 3.1 获取所有仓库
- **URL**: `/api/warehouses`
- **Method**: `GET`
- **Query参数**: `storeId` (可选) - 按门店ID筛选

**响应示例**:
```json
[
  {
    "id": 1,
    "code": "CK001",
    "name": "主仓库",
    "storeId": 1,
    "remark": "备注",
    "status": "active",
    "created_at": "2026-08-30",
    "updated_at": "2026-08-30",
    "categories": [
      {
        "id": 101,
        "name": "胶类",
        "code": "CAT101",
        "created_at": "2026-08-30"
      }
    ]
  }
]
```

### 3.2 获取单个仓库
- **URL**: `/api/warehouses/<int:warehouse_id>`
- **Method**: `GET`

**响应示例**: 同上

### 3.3 新增仓库
- **URL**: `/api/warehouses`
- **Method**: `POST`

**请求参数**:
```json
{
  "code": "CK002",
  "name": "副仓库",
  "storeId": 1,
  "remark": "备注信息"
}
```

**响应示例**:
```json
{
  "id": 2,
  "code": "CK002",
  "name": "副仓库",
  "storeId": 1,
  "remark": "备注信息",
  "status": "active",
  "created_at": "2026-08-30",
  "updated_at": "2026-08-30",
  "categories": []
}
```

### 3.4 更新仓库
- **URL**: `/api/warehouses/<int:warehouse_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "code": "CK002",
  "name": "副仓库更新",
  "storeId": 1,
  "remark": "更新备注",
  "status": "active"
}
```

**响应示例**: 返回更新后的仓库对象

### 3.5 删除仓库
- **URL**: `/api/warehouses/<int:warehouse_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "message": "删除成功"
}
```

### 3.6 新增仓库分类
- **URL**: `/api/warehouses/<int:warehouse_id>/categories`
- **Method**: `POST`

**请求参数**:
```json
{
  "name": "胶类",
  "code": "CAT101"
}
```

**响应示例**:
```json
{
  "id": 101,
  "name": "胶类",
  "code": "CAT101",
  "created_at": "2026-08-30"
}
```

### 3.7 更新仓库分类
- **URL**: `/api/warehouses/<int:warehouse_id>/categories/<int:category_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "name": "胶类更新",
  "code": "CAT102"
}
```

**响应示例**: 返回更新后的分类对象

### 3.8 删除仓库分类
- **URL**: `/api/warehouses/<int:warehouse_id>/categories/<int:category_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "message": "删除成功"
}
```

---

## 4. 商品管理

### 4.1 单位管理

单位统一存储在 `units` 表中，通过 `unit_type` 字段分为两组：

- `measurement`：计量单位，例如公斤、吨、件
- `packaging`：包装，例如无、桶装、纸箱、托盘、袋装

#### 4.1.1 获取全部单位分组
- **URL**: `/api/products/units`
- **Method**: `GET`
- **说明**: 同时返回计量单位和包装，两个数组相互独立

**响应示例**:
```json
{
  "measurements": [
    {
      "id": 1,
      "name": "公斤",
      "createdAt": "2026-08-30 12:00:00"
    }
  ],
  "packagings": [
    {
      "id": 20,
      "name": "桶装",
      "createdAt": "2026-09-08 09:00:00"
    }
  ]
}
```

#### 4.1.2 获取计量单位
- **URL**: `/api/products/units/measurements`
- **Method**: `GET`
- **说明**: 只返回 `unit_type=measurement` 的单位数组，商品与原材料录入弹窗使用此接口

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "公斤",
    "createdAt": "2026-08-30 12:00:00"
  }
]
```

#### 4.1.3 获取包装列表
- **URL**: `/api/products/units/packagings`
- **Method**: `GET`
- **说明**: 只返回 `unit_type=packaging` 的包装数组

**响应示例**:
```json
[
  {
    "id": 20,
    "name": "无",
    "createdAt": "2026-09-08 09:00:00"
  },
  {
    "id": 21,
    "name": "桶装",
    "createdAt": "2026-09-08 09:00:00"
  }
]
```

#### 4.1.4 新增单位或包装
- **URL**: `/api/products/units`
- **Method**: `POST`

**请求参数**:
```json
{
  "name": "吨",
  "type": "measurement"
}
```

`type` 支持 `measurement` 和 `packaging`，未传时默认使用 `measurement`。

**响应示例**:
```json
{
  "success": true,
  "unit": {
    "id": 10,
    "name": "吨",
    "unit_type": "measurement",
    "createdAt": "2026-08-30 12:00:00"
  }
}
```

#### 4.1.5 删除单位或包装
- **URL**: `/api/products/units/<int:unit_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

### 4.2 属性管理

#### 4.2.1 获取所有属性
- **URL**: `/api/products/attributes`
- **Method**: `GET`

**响应示例**:
```json
[
  {
    "id": 1,
    "name": "颜色",
    "options": [
      {
        "id": 101,
        "name": "红色"
      },
      {
        "id": 102,
        "name": "蓝色"
      }
    ],
    "createdAt": "2026-08-30 12:00:00"
  }
]
```

#### 4.2.2 新增属性
- **URL**: `/api/products/attributes`
- **Method**: `POST`

**请求参数**:
```json
{
  "name": "尺寸"
}
```

**响应示例**:
```json
{
  "success": true,
  "attribute": {
    "id": 2,
    "name": "尺寸",
    "options": [],
    "createdAt": "2026-08-30 12:00:00"
  }
}
```

#### 4.2.3 更新属性
- **URL**: `/api/products/attributes/<int:attr_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "name": "颜色更新",
  "options": [
    {
      "id": 101,
      "name": "红色"
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true
}
```

#### 4.2.4 删除属性
- **URL**: `/api/products/attributes/<int:attr_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

#### 4.2.5 新增属性选项
- **URL**: `/api/products/attributes/<int:attr_id>/options`
- **Method**: `POST`

**请求参数**:
```json
{
  "name": "绿色"
}
```

**响应示例**:
```json
{
  "success": true,
  "option": {
    "id": 103,
    "name": "绿色"
  }
}
```

#### 4.2.6 删除属性选项
- **URL**: `/api/products/attributes/<int:attr_id>/options/<int:option_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

### 4.3 商品管理

#### 4.3.1 获取所有商品
- **URL**: `/api/products`
- **Method**: `GET`

**响应示例**:
```json
[
  {
    "id": 1,
    "code": "01",
    "name": "粘钢胶",
    "specification": "40kg/组",
    "category": 202,
    "unitId": 1,
    "enableMultiUnit": false,
    "notes": "",
    "enabled": true,
    "warehouseId": 2,
    "storeIds": [1],
    "warehouseCategories": {},
    "unitConversions": [],
    "enableAttributes": false,
    "attributeCombinations": [],
    "createdAt": "2026-08-30 08:32:03"
  }
]
```

#### 4.3.2 新增商品
- **URL**: `/api/products`
- **Method**: `POST`

**请求参数**:
```json
{
  "storeIds": [1, 2],
  "warehouseId": 1,
  "categoryId": 101,
  "name": "绝缘胶",
  "code": "001",
  "specification": "01",
  "notes": "备注",
  "unitId": 1,
  "enabled": true,
  "unitConversions": [
    {
      "fromUnitId": 2,
      "value": 10,
      "splits": []
    }
  ],
  "enableAttributes": true,
  "attributeCombinations": [
    {
      "id": 0,
      "name": "红色 / L码",
      "purchasePrice": 50,
      "wholesalePrice": 80,
      "retailPrice": 100,
      "barcode": "6901234567890",
      "enabled": true
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "product": {
    "id": 2,
    "code": "001",
    "name": "绝缘胶",
    "specification": "01",
    "category": "",
    "unitId": 1,
    "notes": "备注",
    "enabled": true,
    "warehouseId": 1,
    "storeIds": [1, 2],
    "unitConversions": [],
    "enableAttributes": true,
    "attributeCombinations": [],
    "createdAt": "2026-08-30 12:00:00"
  }
}
```

#### 4.3.3 更新商品
- **URL**: `/api/products/<int:product_id>`
- **Method**: `PUT`

**请求参数**: 同新增商品

**响应示例**:
```json
{
  "success": true
}
```

#### 4.3.4 删除商品
- **URL**: `/api/products/<int:product_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

### 4.4 库存管理

#### 4.4.1 获取库存列表
- **URL**: `/api/products/inventory`
- **Method**: `GET`
- **说明**: 获取带库存信息的商品列表

**响应示例**:
```json
[
  {
    "id": 1,
    "code": "01",
    "name": "粘钢胶",
    "specification": "40kg/组",
    "category": 202,
    "unitId": 1,
    "enableMultiUnit": false,
    "notes": "",
    "enabled": true,
    "warehouseId": 2,
    "storeIds": [1],
    "warehouseCategories": {},
    "unitConversions": [],
    "enableAttributes": false,
    "attributeCombinations": [],
    "createdAt": "2026-08-30 08:32:03",
    "stock": 100,
    "minStock": 50,
    "maxStock": 1000,
    "inventoryUpdatedAt": "2026-08-30 12:00:00"
  }
]
```

#### 4.4.2 更新商品库存
- **URL**: `/api/products/inventory/<int:product_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "stock": 100,
  "minStock": 50,
  "maxStock": 1000
}
```

**响应示例**:
```json
{
  "success": true,
  "inventory": {
    "stock": 100,
    "minStock": 50,
    "maxStock": 1000,
    "updatedAt": "2026-08-30 12:00:00"
  }
}
```

#### 4.4.3 批量更新库存
- **URL**: `/api/products/inventory/batch`
- **Method**: `PUT`

**请求参数**:
```json
{
  "updates": [
    {
      "productId": 1,
      "stock": 100,
      "minStock": 50,
      "maxStock": 1000
    },
    {
      "productId": 2,
      "stock": 200,
      "minStock": 100,
      "maxStock": 2000
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "成功更新 2 条库存记录"
}
```

#### 4.4.4 删除库存信息
- **URL**: `/api/products/inventory/<int:product_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "库存信息已删除"
}
```

### 4.5 原材料商品档案

原材料商品档案与成品商品使用基本相同的字段结构，但存储在独立的
`raw_material_products` 表中。

> `/api/raw-material-products` 管理原材料的名称、编号、规格、单位等档案。
> `/api/materials` 管理原材料使用量和生产量流水，两者不是同一类数据。

#### 4.5.1 获取原材料商品列表
- **URL**: `/api/raw-material-products`
- **Method**: `GET`
- **说明**: 按 ID 倒序返回全部原材料商品档案

**响应示例**:
```json
[
  {
    "id": 1,
    "code": "RM-001",
    "name": "环氧树脂",
    "specification": "E-44 / 20kg",
    "category": 101,
    "unitId": 1,
    "enableMultiUnit": false,
    "notes": "液体原料",
    "enabled": true,
    "warehouseId": 1,
    "storeIds": [1, 2],
    "warehouseCategories": {},
    "unitConversions": [],
    "enableAttributes": false,
    "attributeCombinations": [],
    "createdAt": "2026-09-08 09:00:00",
    "updatedAt": null
  }
]
```

#### 4.5.2 新增原材料商品
- **URL**: `/api/raw-material-products`
- **Method**: `POST`
- **说明**: 新建原材料商品档案，`name` 不能为空

**请求参数**:
```json
{
  "storeIds": [1, 2],
  "warehouseId": 1,
  "categoryId": 101,
  "name": "环氧树脂",
  "code": "RM-001",
  "specification": "E-44 / 20kg",
  "notes": "液体原料",
  "unitId": 1,
  "enableMultiUnit": false,
  "enabled": true,
  "warehouseCategories": {},
  "unitConversions": [
    {
      "fromUnitId": 2,
      "value": 20,
      "splits": []
    }
  ],
  "enableAttributes": false,
  "attributeCombinations": []
}
```

**响应示例（字段已精简）**:
```json
{
  "success": true,
  "product": {
    "id": 1,
    "code": "RM-001",
    "name": "环氧树脂",
    "specification": "E-44 / 20kg",
    "category": 101,
    "unitId": 1,
    "enableMultiUnit": false,
    "notes": "液体原料",
    "enabled": true,
    "warehouseId": 1,
    "storeIds": [1, 2],
    "warehouseCategories": {},
    "unitConversions": [],
    "enableAttributes": false,
    "attributeCombinations": [],
    "createdAt": "2026-09-08 09:00:00",
    "updatedAt": null
  },
  "rawMaterialProduct": {
    "id": 1,
    "name": "环氧树脂"
  }
}
```

`product` 和 `rawMaterialProduct` 指向同一条新建记录，实际两个字段都会返回完整对象；
上例仅为避免重复展示而精简 `rawMaterialProduct`。保留两个字段是为了兼容公共商品弹窗和原材料页面。

#### 4.5.3 更新原材料商品
- **URL**: `/api/raw-material-products/<int:product_id>`
- **Method**: `PUT`
- **说明**: 更新指定原材料商品，提交结构与新增接口相同

**响应示例（字段已精简）**:
```json
{
  "success": true,
  "product": {
    "id": 1,
    "name": "环氧树脂 E-44",
    "updatedAt": "2026-09-08 10:30:00"
  },
  "rawMaterialProduct": {
    "id": 1,
    "name": "环氧树脂 E-44"
  }
}
```

`product` 和 `rawMaterialProduct` 在更新接口中同样是同一条记录的完整对象。

#### 4.5.4 删除原材料商品
- **URL**: `/api/raw-material-products/<int:product_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

#### 4.5.5 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 原材料名称 |
| `code` | string | 否 | 原材料编号 |
| `specification` | string | 否 | 规格型号 |
| `categoryId` / `category` | integer | 否 | 仓库分类 ID |
| `unitId` | integer | 否 | 计量单位 ID，关联 `units` 表 |
| `warehouseId` | integer | 否 | 默认仓库 ID |
| `storeIds` | array | 否 | 所属门店 ID 数组 |
| `enabled` | boolean | 否 | 是否启用，默认 `true` |
| `enableMultiUnit` | boolean | 否 | 是否启用多单位 |
| `unitConversions` | array | 否 | 多单位换算关系 |
| `warehouseCategories` | object | 否 | 仓库与分类的关联配置 |
| `enableAttributes` | boolean | 否 | 是否启用属性 |
| `attributeCombinations` | array | 否 | 属性、价格和条码组合 |
| `notes` | string | 否 | 备注 |

**前端调用关系**:

| 页面或组件 | 路由/模式 | 接口 |
|------------|-----------|------|
| `ProductList.vue` | `/admin/products`、`finished-product` | `/api/products` |
| `MaterialProductList.vue` | `/admin/materials`、`raw-material` | `/api/raw-material-products` |
| `ProductFormModal.vue` | 根据路由或 `mode` 自动切换 | 上述对应接口 |
| `MaterialInventory.vue` | `/admin/inventory/materials` | 读取 `/api/raw-material-products` |

---

## 5. 订单管理

### 5.1 获取所有订单
- **URL**: `/api/orders`
- **Method**: `GET`
- **说明**: 获取所有订单列表，新旧订单格式共存；返回结果包含订单包装和物流服务字段

**响应示例（旧订单）**:
```json
[
  {
    "id": 11,
    "title": "",
    "status": "shipped",
    "type": 0,
    "store_id": 2,
    "date": "2026-07-14 14:41",
    "completed_date": "2026-07-20 17:56",
    "shipped_date": "2026-07-20 17:56",
    "order_client": "张杰订单",
    "receiver_name": "段洪强",
    "receiver_phone": "15527382584",
    "receiver_address": "湖北省武汉市江夏区光谷芯中心二期E区9栋",
    "goods_name": "碳纤维胶5公斤",
    "goods_weight": "5kg",
    "goods_quantity": "1件",
    "goods_packaging": "桶装",
    "logistics_service": ["送货上门+回单拍照回传"],
    "logistics_no": "无单号记录",
    "shipping_method": 0,
    "shipping_custom": "",
    "audit_state": 1,
    "remark": ""
  }
]
```

**响应示例（新订单 - 销售单）**:
```json
[
  {
    "id": 123,
    "type": 1,
    "status": "completed",
    "store_id": 1,
    "customer_id": 5,
    "warehouse_id": 2,
    "order_number": "ZG20260902001",
    "order_date": "2026-09-02",
    "date": "2026-09-02 10:30:00",
    
    "order_client": "武汉海威船舶",
    "contact_person": "段洪强",
    "contact_phone": "15527382584",
    "contact_address": "湖北省武汉市江夏区光谷芯中心二期E区9栋",
    "project_name": "海洋工程项目",
    "sales_person": "李四",
    "creator": "张三",
    
    "order_goods": [
      {
        "product_id": 10,
        "goods_name": "碳纤维胶",
        "spec": "5kg/桶",
        "unit": "桶",
        "warehouse_id": 2,
        "warehouse_name": "小仓库",
        "packages": 2,
        "quantity": 10,
        "price": 100.00,
        "tax_rate": 13,
        "tax_included_price": 113.00,
        "amount": 1000.00,
        "total_amount": 1130.00,
        "remark": "送客户做实验"
      },
      {
        "product_id": 15,
        "goods_name": "环氧树脂",
        "spec": "25kg/桶",
        "unit": "桶",
        "warehouse_id": 2,
        "warehouse_name": "小仓库",
        "packages": 1,
        "quantity": 25,
        "price": 50.00,
        "tax_rate": 13,
        "tax_included_price": 56.50,
        "amount": 1250.00,
        "total_amount": 1412.50,
        "remark": ""
      }
    ],
    
    "subtotal_amount": 2250.00,
    "tax_amount": 292.50,
    "total_amount": 2542.50,
    "discount_amount": 2542.50,
    "other_fees": 0,
    "should_receive": 2542.50,
    "current_payment": 2542.50,
    "current_debt": 0,
    "settlement_account": "武汉门店",
    
    "goods_name": "碳纤维胶 5kg/桶 x10、环氧树脂 25kg/桶 x25",
    "goods_weight": "35kg",
    "goods_quantity": "3件",
    "goods_packaging": "桶装",
    "logistics_service": "送货上门+回单拍照回传",
    "receiver_name": "段洪强",
    "receiver_phone": "15527382584",
    "receiver_address": "湖北省武汉市江夏区光谷芯中心二期E区9栋",
    
    "remark": "订单备注"
}
]
```

**包装和物流服务字段**:

- `goods_packaging`: 订单包装字符串，默认值为 `"无"`，可使用单位接口中的 `unit_type=packaging` 数据
- `logistics_service`: 物流服务字符串，默认值为 `"送货上门+回单拍照回传"`
- 为兼容历史数据，旧订单的 `logistics_service` 可能是数组，新订单保存为字符串

包装默认选项为：`无`、`桶装`、`纸箱`、`托盘`、`袋装`，也可以通过
`POST /api/products/units` 以 `type=packaging` 新增包装。

物流服务选项为：

1. `送货上门+回单拍照回传`
2. `送货上门+回单邮回`
3. `送货上门`
4. `用户自提`
5. `无`

订单表中对应的 SQLite 字段为 `goods_packaging TEXT` 和
`logistics_service TEXT`，两者保存的是字符值。

### 5.2 获取单个订单详情
- **URL**: `/api/orders/<int:order_id>`
- **Method**: `GET`
- **说明**: 获取订单详细信息，用于订单编辑

**响应示例**: 同 5.1，返回单个订单对象

### 5.3 创建订单（新销售单）
- **URL**: `/api/orders`
- **Method**: `POST`
- **说明**: 创建新订单（type=1），包含完整商品明细和财务信息

**请求参数**:
```json
{
  "type": 1,
  "storeId": 1,
  "customerId": 5,
  "warehouseId": 2,
  "orderNumber": "ZG20260902001",
  "orderDate": "2026-09-02",
  "contactPerson": "段洪强",
  "contactPhone": "15527382584",
  "contactAddress": "湖北省武汉市江夏区光谷芯中心二期E区9栋",
  "projectName": "海洋工程项目",
  "goodsPackaging": "桶装",
  "logisticsService": "送货上门+回单拍照回传",
  "salesPerson": "李四",
  "creator": "张三",
  "orderRemark": "订单备注",
  "taxRate": 13,
  "discountAmount": 2542.50,
  "otherFees": 0,
  "settlementAccount": "武汉门店",
  "currentPayment": 2542.50,
  
  "items": [
    {
      "productId": 10,
      "productName": "碳纤维胶",
      "spec": "5kg/桶",
      "unit": "桶",
      "warehouseId": 2,
      "packages": 2,
      "quantity": 10,
      "price": 100.00,
      "taxRate": 13,
      "taxIncludedPrice": 113.00,
      "amount": 1000.00,
      "totalAmount": 1130.00,
      "remark": "送客户做实验"
    },
    {
      "productId": 15,
      "productName": "环氧树脂",
      "spec": "25kg/桶",
      "unit": "桶",
      "warehouseId": 2,
      "packages": 1,
      "quantity": 25,
      "price": 50.00,
      "taxRate": 13,
      "taxIncludedPrice": 56.50,
      "amount": 1250.00,
      "totalAmount": 1412.50,
      "remark": ""
    }
  ]
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "order_number": "ZG20260902001",
    "type": 1,
    "status": "completed",
    "date": "2026-09-02 10:30:00"
  },
  "message": "订单保存成功"
}
```

**注意事项**:
- 保存时会同时填充新旧字段，确保兼容性
- 自动计算 `subtotal_amount`、`tax_amount`、`total_amount`、`should_receive`、`current_debt`
- 自动生成冗余字段 `goods_name`、`goods_weight`、`goods_quantity`
- **库存不足时允许保存，不阻止录入**
- 保存成功后自动扣减库存

### 5.4 更新订单（编辑销售单）
- **URL**: `/api/orders/<int:order_id>`
- **Method**: `PUT`
- **说明**: 更新订单信息，支持编辑商品明细、财务信息等

**请求参数（完整订单更新）**:
```json
{
  "storeId": 1,
  "customerId": 5,
  "warehouseId": 2,
  "orderDate": "2026-09-02",
  "contactPerson": "段洪强（修改）",
  "contactPhone": "15527382584",
  "contactAddress": "新地址",
  "projectName": "海洋工程项目",
  "goodsPackaging": "纸箱",
  "logisticsService": "送货上门",
  "salesPerson": "李四",
  "creator": "张三",
  "orderRemark": "修改后的备注",
  "discountAmount": 2500.00,
  "otherFees": 100,
  "currentPayment": 2600.00,
  
  "items": [
    {
      "productId": 10,
      "quantity": 15,
      "price": 100.00
    }
  ]
}
```

编辑订单时也可以单独更新包装和物流服务：

```json
{
  "goodsPackaging": "纸箱",
  "logisticsService": "送货上门"
}
```

新订单表单使用驼峰字段 `goodsPackaging`、`logisticsService`；后端同时兼容
下划线字段 `goods_packaging`、`logistics_service`。

**或者仅更新订单状态**:
```json
{
  "status": "completed"
}
```

**或者仅更新物流信息**:
```json
{
  "logistics_no": "三志物流-SF123456",
  "audit_state": 1,
  "freight_costs": [
    {
      "type": "freight",
      "note": "运费",
      "amount": 150.00
    },
    {
      "type": "other",
      "note": "货拉拉",
      "amount": 50.00
    }
  ]
}
```

**或者更新为已发货状态**:
```json
{
  "status": "shipped",
  "shipping_method": 0,
  "shipped_date": "2026-09-02 14:00:00"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "订单更新成功"
}
```

### 5.5 删除订单
- **URL**: `/api/orders/<int:order_id>`
- **Method**: `DELETE`
- **说明**: 删除订单，新订单删除时会自动恢复库存

**响应示例**:
```json
{
  "success": true,
  "message": "订单删除成功，库存已恢复"
}
```

**注意事项**:
- 删除新订单（type=1）时，会自动将已扣减的库存恢复
- 删除旧订单不影响库存
- 已发货订单建议先撤销出库再删除

### 5.6 上传回单图片
- **URL**: `/api/orders/<int:order_id>/upload_receipt`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **说明**: 上传订单的发货回单图片

**请求参数**:
```
receipt_image: File (图片文件)
```

**响应示例**:
```json
{
  "success": true,
  "receipt_img_url": "/uploads/receipts/123_1693901234.jpg",
  "message": "回单上传成功"
}
```

### 5.7 删除回单图片
- **URL**: `/api/orders/<int:order_id>/receipt`
- **Method**: `DELETE`
- **说明**: 删除订单的回单图片（从数据库和硬盘中彻底删除）

**响应示例**:
```json
{
  "success": true,
  "message": "回单图片已删除"
}
```

### 5.8 批量删除订单
- **说明**: 前端通过并发调用 DELETE 接口实现批量删除
- **逻辑**: 使用 `Promise.allSettled()` 确保所有请求完成，统计成功和失败数量

### 5.9 更新订单已支付金额
- **URL**: `/api/orders/<int:order_id>/paid-amount`
- **Method**: `PUT`
- **Header**: `Username: admin`
- **说明**: 更新运费的已支付金额（用于物流对账）

**请求参数**:
```json
{
  "freightCostIndex": 0,
  "paidAmount": 50
}
```

**响应示例**:
```json
{
  "success": true,
  "order": {
    "id": 1,
    "freight_costs": [
      {
        "note": "运费",
        "amount": 50,
        "paid_amount": 50,
        "updated_at": "2026-08-30 12:00:00",
        "updated_by": "admin"
      }
    ]
  }
}
```

---

## 6. 运营商标签管理

### 6.1 获取运营商标签
- **URL**: `/api/carrier_tags`
- **Method**: `GET`
- **说明**: 获取历史物流公司快捷标签（最多20个）

**响应示例**:
```json
["三志物流", "顺丰快递", "安能快运", "中通快递"]
```

### 6.2 添加运营商标签
- **URL**: `/api/carrier_tags`
- **Method**: `POST`
- **说明**: 添加新的物流公司标签到历史记录

**请求参数**:
```json
{
  "tag": "韵达快递"
}
```

**响应示例**:
```json
{
  "success": true,
  "tags": ["韵达快递", "三志物流", "顺丰快递", "安能快运"]
}
```

**注意事项**:
- 新标签会插入到列表开头
- 如果标签已存在，不会重复添加
- 最多保留20个标签

---

## 7. 客户管理

### 7.1 获取客户列表
- **URL**: `/api/customers`
- **Method**: `GET`

**查询参数**:
- `customerName`: 客户名称（模糊搜索）
- `phone`: 联系电话（模糊搜索）
- `storeId`: 门店ID
- `status`: 客户状态（active/inactive）

**响应示例**:
```json
[
  {
    "id": 1,
    "customerCode": "001",
    "customerName": "锦州森源",
    "storeId": 1,
    "contactPerson": "张三",
    "phone": "17554354236",
    "address": "北京天安门",
    "balance": 0,
    "receivable": 5000,
    "bankName": "",
    "bankAccount": "",
    "bankCode": "",
    "taxNumber": "",
    "remark": "",
    "status": "active",
    "createdAt": "2026-09-01T12:58:31",
    "updatedAt": "2026-09-01T14:46:38"
  }
]
```

### 7.2 获取单个客户详情
- **URL**: `/api/customers/<int:customer_id>`
- **Method**: `GET`

**响应示例**:
```json
{
  "id": 1,
  "customerCode": "001",
  "customerName": "锦州森源",
  "storeId": 1,
  "contactPerson": "张三",
  "phone": "17554354236",
  "address": "北京天安门",
  "balance": 0,
  "receivable": 5000,
  "bankName": "",
  "bankAccount": "",
  "bankCode": "",
  "taxNumber": "",
  "remark": "",
  "status": "active",
  "createdAt": "2026-09-01T12:58:31",
  "updatedAt": "2026-09-01T14:46:38"
}
```

**字段说明**:
- `customerCode`: 客户编号
- `customerName`: 客户名称
- `storeId`: 所属门店ID
- `contactPerson`: 联系人
- `phone`: 联系电话
- `address`: 客户地址
- `balance`: 余额
- `receivable`: 应收账款
- `bankName`: 开户行
- `bankAccount`: 银行账号
- `bankCode`: 银行代码
- `taxNumber`: 税号
- `remark`: 备注
- `status`: 客户状态（active/inactive）

### 7.3 创建客户
- **URL**: `/api/customers`
- **Method**: `POST`

**请求参数**:
```json
{
  "customerName": "新客户名称",
  "customerCode": "005",
  "storeId": 1,
  "contactPerson": "联系人",
  "phone": "13800138000",
  "address": "客户地址",
  "balance": 0,
  "receivable": 0,
  "bankName": "工商银行",
  "bankAccount": "6222021234567890",
  "bankCode": "102100099996",
  "taxNumber": "91440101MA5CQ1234",
  "remark": "重点客户"
}
```

**响应示例**:
```json
{
  "success": true,
  "customer": {
    "id": 5,
    "customerCode": "005",
    "customerName": "新客户名称",
    "storeId": 1,
    "contactPerson": "联系人",
    "phone": "13800138000",
    "address": "客户地址",
    "balance": 0,
    "receivable": 0,
    "status": "active",
    "createdAt": "2026-09-06T10:30:00"
  }
}
```

### 7.4 更新客户信息
- **URL**: `/api/customers/<int:customer_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "customerName": "更新客户名称",
  "customerCode": "005",
  "storeId": 1,
  "contactPerson": "新联系人",
  "phone": "13900139000",
  "address": "新地址",
  "balance": 1000,
  "receivable": 8000,
  "remark": "更新备注"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "客户更新成功"
}
```

### 7.5 删除客户
- **URL**: `/api/customers/<int:customer_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "客户删除成功"
}
```

---

## 8. 原材料使用与生产流水

> 本章节管理原材料的使用量、生产量和备注标签。
> 原材料商品档案请参阅 [4.5 原材料商品档案](#45-原材料商品档案)。

### 8.1 获取原材料流水与汇总
- **URL**: `/api/materials`
- **Method**: `GET`
- **说明**: 获取原材料使用/生产流水、备注标签和计算后的库存汇总

**响应示例**:
```json
{
  "records": [
    {
      "id": 59,
      "used": 36.0,
      "produced": 88.0,
      "remark": "灌缝胶",
      "date": "2026-08-30 05:10",
      "created_at": "2026-09-06 02:27:56"
    },
    {
      "id": 58,
      "used": 111.0,
      "produced": 888.0,
      "remark": "环氧脂子",
      "date": "2026-08-30 05:09",
      "created_at": "2026-09-06 02:27:56"
    }
  ],
  "remark_tags": [
    "粘钢胶",
    "碳纤维胶",
    "环氧脂子",
    "灌注胶",
    "灌缝胶"
  ],
  "total_stock": 36648.0
}
```

**响应字段说明**:
- `records`: 原材料使用/生产记录数组
- `remark_tags`: 常用备注标签列表（快捷输入）
- `total_stock`: 总库存量（生产总和 - 使用总和）

### 8.2 添加原材料记录
- **URL**: `/api/materials`
- **Method**: `POST`
- **说明**: 添加原材料使用或生产记录

**请求参数**:
```json
{
  "used": 50.0,
  "produced": 100.0,
  "remark": "粘钢胶"
}
```

服务端会使用当前时间生成 `date` 字段，数量单位统一为公斤。

**响应示例**:
```json
{
  "success": true,
  "id": 60
}
```

### 8.3 更新原材料记录
- **URL**: `/api/materials/<int:record_id>`
- **Method**: `PUT`
- **说明**: 修改已有的原材料记录

**请求参数**:
```json
{
  "used": 60.0,
  "produced": 120.0,
  "remark": "粘钢胶（更新）"
}
```

**响应示例**:
```json
{
  "success": true
}
```

### 8.4 删除原材料记录
- **URL**: `/api/materials/<int:record_id>`
- **Method**: `DELETE`
- **说明**: 删除指定的原材料记录

**响应示例**:
```json
{
  "success": true
}
```

**注意事项**:
- 删除记录后，总库存会自动重新计算
- 所有数量单位统一为**公斤**
- `remark` 字段会自动添加到标签列表
- 总库存 = Σ(produced) - Σ(used)

---

## 9. 运费记录管理

### 9.1 获取所有运费记录
- **URL**: `/api/freight-records`
- **Method**: `GET`

**响应示例**:
```json
[
  {
    "id": "uuid-string",
    "type": "insulation",
    "year": 2026,
    "month": 8,
    "period": "上半月",
    "orders": [1, 2, 3],
    "totalAmount": 500,
    "reserveFund": 100,
    "createdAt": "2026-08-30 12:00:00",
    "createdBy": "管理员"
  }
]
```

### 9.2 创建运费记录
- **URL**: `/api/freight-records`
- **Method**: `POST`
- **Header**: `Username: admin`

**请求参数**:
```json
{
  "type": "insulation",
  "year": 2026,
  "month": 8,
  "period": "上半月",
  "orders": [1, 2, 3],
  "totalAmount": 500,
  "reserveFund": 100
}
```

**响应示例**:
```json
{
  "success": true,
  "record": {
    "id": "uuid-string",
    "type": "insulation",
    "year": 2026,
    "month": 8,
    "period": "上半月",
    "orders": [1, 2, 3],
    "totalAmount": 500,
    "reserveFund": 100,
    "createdAt": "2026-08-30 12:00:00",
    "createdBy": "admin"
  }
}
```

### 9.3 获取所有备用金记录
- **URL**: `/api/freight-records/reserve-fund`
- **Method**: `GET`

**响应示例**:
```json
[
  {
    "id": "uuid-string",
    "type": "deposit",
    "amount": 1000,
    "date": "2026-08-30",
    "note": "充值备用金",
    "createdAt": "2026-08-30 12:00:00",
    "createdBy": "管理员"
  }
]
```

### 9.4 创建备用金记录
- **URL**: `/api/freight-records/reserve-fund`
- **Method**: `POST`
- **Header**: `Username: admin`

**请求参数**:
```json
{
  "type": "deposit",
  "amount": 1000,
  "date": "2026-08-30",
  "note": "充值备用金"
}
```

**响应示例**:
```json
{
  "success": true,
  "fund": {
    "id": "uuid-string",
    "type": "deposit",
    "amount": 1000,
    "date": "2026-08-30",
    "note": "充值备用金",
    "createdAt": "2026-08-30 12:00:00",
    "createdBy": "admin"
  }
}
```

### 9.5 获取最新备用金余额
- **URL**: `/api/freight-records/reserve-fund/latest`
- **Method**: `GET`

**响应示例**:
```json
{
  "balance": 1500,
  "latestRecord": {
    "id": "uuid-string",
    "type": "deposit",
    "amount": 1000,
    "date": "2026-08-30",
    "note": "充值备用金",
    "createdAt": "2026-08-30 12:00:00",
    "createdBy": "管理员"
  }
}
```

### 9.6 更新备用金金额
- **URL**: `/api/freight-records/reserve-fund/<fund_id>`
- **Method**: `PUT`
- **Header**: `Username: admin`

**请求参数**:
```json
{
  "amount": 1200
}
```

**响应示例**:
```json
{
  "success": true,
  "fund": {
    "id": "uuid-string",
    "type": "deposit",
    "amount": 1200,
    "date": "2026-08-30",
    "note": "充值备用金",
    "createdAt": "2026-08-30 12:00:00",
    "createdBy": "管理员",
    "updatedAt": "2026-08-30 13:00:00",
    "updatedBy": "admin"
  }
}
```

---

## 10. 人事检测报告文件管理

> 模块前缀：`/api/hr/reports`
>
> 用于管理人事检测报告及其他相关文件，支持多级文件夹、文件上传、同步扫描、下载/预览、分享、移动和删除。

### 10.1 同步文件目录
- **URL**: `/api/hr/reports/sync`
- **Method**: `POST`
- **Content-Type**: 无请求体
- **说明**: 递归扫描服务端人事报告上传目录，将允许类型的文件同步到 `hr_reports` 数据表。

**支持的文件扩展名**:

| 扩展名 | 文件类型 |
|--------|----------|
| `pdf` | PDF 文档 |
| `jpg`、`jpeg`、`png`、`gif` | 图片 |
| `xls`、`xlsx` | Excel 文件 |
| `doc`、`docx` | Word 文件 |

**响应示例**:
```json
{
  "success": true,
  "message": "同步完成: 新增 2 个，更新 1 个，删除 0 个",
  "stats": {
    "new": 2,
    "updated": 1,
    "deleted": 0,
    "total": 8
  }
}
```

**说明**:
- 扫描包含多级子文件夹。
- 只同步上述允许类型的文件。
- 根据文件路径和 MD5 哈希判断新增、修改和删除。
- 如果物理文件已经不存在，对应的数据库记录会被删除。

### 10.2 获取文件列表
- **URL**: `/api/hr/reports/list`
- **Method**: `GET`
- **说明**: 获取所有报告文件，以树形结构返回文件夹和文件。

**响应示例**:
```json
{
  "success": true,
  "data": {
    "folders": [
      {
        "name": "2026",
        "path": "2026",
        "folders": [],
        "files": [
          {
            "id": "2a0e6a7b-3a90-4b5f-9f4a-123456789abc",
            "name": "检测报告.pdf",
            "path": "2026/检测报告.pdf",
            "size": 245760,
            "type": "pdf",
            "createdAt": "2026-09-07 10:00:00",
            "updatedAt": "2026-09-07 10:00:00"
          }
        ]
      }
    ],
    "files": []
  }
}
```

**文件对象字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 文件唯一 ID |
| `name` | string | 文件名 |
| `path` | string | 相对于报告存储目录的文件路径，使用 `/` 分隔 |
| `size` | integer | 文件大小，单位为字节 |
| `type` | string | `pdf`、`image`、`excel`、`word` 或 `other` |
| `createdAt` | string | 创建时间 |
| `updatedAt` | string | 更新时间 |

### 10.3 上传文件
- **URL**: `/api/hr/reports/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Header**: `Username`（可选，未提供时记录为 `unknown`）

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | 待上传文件 |
| `folder_path` | string | 否 | 目标文件夹相对路径，例如 `2026/09`，为空时上传到根目录 |

**请求示例**:
```bash
curl -X POST "http://localhost:5000/api/hr/reports/upload" `
  -H "Username: admin" `
  -F "file=@D:\reports\检测报告.pdf" `
  -F "folder_path=2026/09"
```

**响应示例**:
```json
{
  "success": true,
  "message": "上传成功",
  "file": {
    "id": "2a0e6a7b-3a90-4b5f-9f4a-123456789abc",
    "name": "检测报告.pdf",
    "path": "2026/09/检测报告.pdf",
    "size": 245760,
    "type": "pdf"
  }
}
```

**常见错误**:
- 未提供 `file`：HTTP `400`，返回 `没有文件`。
- 文件名为空：HTTP `400`，返回 `文件名为空`。
- 扩展名不在允许列表中：HTTP `400`，返回 `不支持的文件类型`。

### 10.4 下载或预览文件
- **URL**: `/api/hr/reports/download/<file_id>`
- **Method**: `GET`
- **说明**: 根据文件 ID 返回文件流。

**返回规则**:
- PDF 和图片使用浏览器内联预览（`Content-Disposition: inline`）。
- Excel、Word 等其他允许类型以附件形式下载（`Content-Disposition: attachment`）。
- 成功时返回文件流，不是 JSON。

**错误响应示例**:
```json
{
  "success": false,
  "message": "文件不存在"
}
```

### 10.5 创建文件分享链接
- **URL**: `/api/hr/reports/share/<file_id>`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **说明**: 为指定文件生成一个分享 Token。同一个文件再次生成分享链接时，旧 Token 会被覆盖。

**请求参数**:
```json
{
  "expire_days": 7
}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `expire_days` | number | 否 | `7` | 分享有效天数 |

**响应示例**:
```json
{
  "success": true,
  "share_token": "6d6f4c5e-1be1-4f91-b6e6-123456789abc",
  "expire_at": "2026-09-14 10:30:00"
}
```

### 10.6 通过分享链接下载或预览文件
- **URL**: `/api/hr/reports/share/<share_token>`
- **Method**: `GET`
- **说明**: 通过分享 Token 访问文件。PDF 和图片会尝试在浏览器中预览，其他文件直接下载。

**请求示例**:
```text
GET /api/hr/reports/share/6d6f4c5e-1be1-4f91-b6e6-123456789abc
```

**错误响应**:
```json
{
  "success": false,
  "message": "分享链接已过期"
}
```

**可能的 HTTP 状态码**:
- `403`：分享链接已过期。
- `404`：分享链接无效或文件已丢失。
- `500`：下载处理失败。

### 10.7 删除文件
- **URL**: `/api/hr/reports/delete/<file_id>`
- **Method**: `DELETE`
- **说明**: 同时删除物理文件和数据库记录。

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功"
}
```

### 10.8 重命名文件夹
- **URL**: `/api/hr/reports/folder/rename`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **说明**: 重命名物理文件夹，并同步更新该文件夹下所有文件的数据库路径。

**请求参数**:
```json
{
  "old_path": "2026/09",
  "new_name": "2026年09月"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `old_path` | string | 是 | 原文件夹相对路径 |
| `new_name` | string | 是 | 新文件夹名称，不是完整路径 |

**响应示例**:
```json
{
  "success": true,
  "message": "重命名成功"
}
```

**常见错误**:
- 参数缺失：HTTP `400`，返回 `参数不完整`。
- 原文件夹不存在：HTTP `404`，返回 `文件夹不存在`。
- 目标文件夹已存在：HTTP `400`，返回 `目标文件夹已存在`。

### 10.9 删除文件夹
- **URL**: `/api/hr/reports/folder/delete`
- **Method**: `DELETE`
- **Content-Type**: `application/json`
- **说明**: 递归删除物理文件夹及其内容，并删除数据库中该路径下的所有文件记录。

**请求参数**:
```json
{
  "folder_path": "2026/09"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功，共删除 3 个文件"
}
```

**常见错误**:
- 参数缺失：HTTP `400`，返回 `参数不完整`。
- 文件夹不存在：HTTP `404`，返回 `文件夹不存在`。

### 10.10 移动文件
- **URL**: `/api/hr/reports/move`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **说明**: 将文件移动到指定文件夹，并同步更新数据库中的相对路径。

**请求参数**:
```json
{
  "file_id": "2a0e6a7b-3a90-4b5f-9f4a-123456789abc",
  "target_folder": "2026/10"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 是 | 文件唯一 ID |
| `target_folder` | string | 否 | 目标文件夹相对路径，为空时移动到根目录 |

**响应示例**:
```json
{
  "success": true,
  "message": "移动成功"
}
```

**常见错误**:
- `file_id` 缺失：HTTP `400`，返回 `参数不完整`。
- 文件不存在：HTTP `404`，返回 `文件不存在`。
- 目标位置存在同名文件：HTTP `400`，返回 `目标位置已存在同名文件`。

### 10.11 人事报告文件字段和存储说明

`hr_reports` 表的主要字段如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT | 文件唯一 ID |
| `filename` | TEXT | 原始安全文件名 |
| `file_path` | TEXT | 文件相对路径，唯一 |
| `file_hash` | TEXT | 文件 MD5 哈希 |
| `file_size` | INTEGER | 文件大小，单位为字节 |
| `file_type` | TEXT | 文件类型：`pdf`、`image`、`excel`、`word` |
| `uploader` | TEXT | 上传人，由 `Username` 请求头写入 |
| `share_token` | TEXT | 分享 Token |
| `share_expire` | TEXT | 分享过期时间 |
| `created_at` | TEXT | 创建时间 |
| `updated_at` | TEXT | 更新时间 |

文件物理存储在后端 `uploads/hr_reports` 目录下；Linux 容器环境中如果存在 `/app/uploads`，则使用 `/app/uploads/hr_reports`。

---

## 11. 供应商与入库管理

本模块由 `backend/routes/stock_inbounds.py` 提供，支持原材料采购入库和成品生产完工入库。

入库单有以下两种类型：

- `raw-material`：原材料采购入库，提交过账时必须关联有效供应商
- `finished-product`：成品生产完工入库，生产车间/班组为选填字段

入库单有以下三种状态：

- `draft`：草稿，只保存单据头与明细，不改变库存
- `posted`：已过账，写入库存余额与库存流水
- `cancelled`：已作废，未过账单据执行删除操作后进入此状态

### 11.1 获取供应商列表

- **URL**: `/api/suppliers`
- **Method**: `GET`
- **说明**: 获取供应商基础资料，默认返回所有状态的记录

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `storeId` | integer | 否 | 返回该门店及未指定门店的供应商 |
| `status` | string | 否 | 按状态筛选：`active` 或 `inactive` |

**响应示例**:

```json
[
  {
    "id": 1,
    "supplierCode": "SUP-001",
    "supplierName": "华中原料供应有限公司",
    "storeId": 1,
    "contactPerson": "王经理",
    "phone": "13800000000",
    "address": "湖北省武汉市",
    "taxNumber": "91420100XXXXXXXX",
    "bankName": "中国银行武汉分行",
    "bankAccount": "1234567890",
    "remark": "月结供应商",
    "status": "active",
    "createdAt": "2026-09-08 10:00:00",
    "updatedAt": "2026-09-08 10:00:00"
  }
]
```

### 11.2 新增供应商

- **URL**: `/api/suppliers`
- **Method**: `POST`

**请求参数**:

```json
{
  "supplierCode": "SUP-001",
  "supplierName": "华中原料供应有限公司",
  "storeId": 1,
  "contactPerson": "王经理",
  "phone": "13800000000",
  "address": "湖北省武汉市",
  "taxNumber": "91420100XXXXXXXX",
  "bankName": "中国银行武汉分行",
  "bankAccount": "1234567890",
  "remark": "月结供应商",
  "status": "active"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `supplierName` | string | 是 | 供应商名称；兼容别名 `name` |
| `supplierCode` | string | 否 | 供应商编号；兼容别名 `code`，非空时全局唯一 |
| `storeId` | integer | 否 | 所属门店 ID |
| `contactPerson` | string | 否 | 联系人 |
| `phone` | string | 否 | 联系电话 |
| `address` | string | 否 | 联系地址 |
| `taxNumber` | string | 否 | 税号 |
| `bankName` | string | 否 | 开户银行 |
| `bankAccount` | string | 否 | 银行账号 |
| `remark` | string | 否 | 备注 |
| `status` | string | 否 | 默认 `active` |

**成功响应**: HTTP `201`

```json
{
  "success": true,
  "supplier": {
    "id": 1,
    "supplierCode": "SUP-001",
    "supplierName": "华中原料供应有限公司",
    "status": "active"
  }
}
```

供应商编号重复时返回 HTTP `409`；名称为空或字段格式错误时返回 HTTP `400`。

### 11.3 更新供应商

- **URL**: `/api/suppliers/<int:supplier_id>`
- **Method**: `PUT`
- **说明**: 支持只传需要修改的字段，字段定义与新增供应商相同

**请求示例**:

```json
{
  "contactPerson": "李经理",
  "phone": "13900000000",
  "remark": "联系人已更新"
}
```

**成功响应**:

```json
{
  "success": true,
  "supplier": {
    "id": 1,
    "supplierCode": "SUP-001",
    "supplierName": "华中原料供应有限公司",
    "contactPerson": "李经理",
    "phone": "13900000000",
    "status": "active"
  }
}
```

供应商不存在时返回 HTTP `404`，编号冲突时返回 HTTP `409`。

### 11.4 删除或停用供应商

- **URL**: `/api/suppliers/<int:supplier_id>`
- **Method**: `DELETE`
- **说明**: 未被入库单引用时物理删除；已被引用时保留历史资料并把状态改为 `inactive`

**成功响应示例**:

```json
{
  "success": true,
  "message": "供应商已停用"
}
```

供应商不存在时返回 HTTP `404`。

### 11.5 获取入库单列表

- **URL**: `/api/stock-inbounds`
- **Method**: `GET`
- **说明**: 按 ID 倒序返回入库单；每张单据包含 `items` 明细数组

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 否 | `raw-material` 或 `finished-product` |
| `status` | string | 否 | `draft`、`posted` 或 `cancelled` |

**响应示例**:

```json
[
  {
    "id": 12,
    "documentNo": "RK20260908012",
    "documentDate": "2026-09-08",
    "type": "raw-material",
    "storeId": 1,
    "warehouseId": 2,
    "supplierId": 1,
    "workshop": "",
    "status": "posted",
    "totalQuantity": 98.5,
    "totalTax": 158.09,
    "totalAmount": 1374.13,
    "postedAt": "2026-09-08 14:30:00",
    "createdAt": "2026-09-08 14:25:00",
    "updatedAt": "2026-09-08 14:30:00",
    "items": [
      {
        "id": 28,
        "inbound_id": 12,
        "line_no": 1,
        "product_type": "raw-material",
        "productId": 3,
        "productCode": "RM-003",
        "productName": "轻质碳酸钙",
        "receivedQty": 98.5,
        "batchNo": "20260908-A",
        "unitPrice": 12.3456,
        "taxRate": 13,
        "taxAmount": 158.09,
        "totalAmount": 1374.13
      }
    ]
  }
]
```

### 11.6 获取入库单详情

- **URL**: `/api/stock-inbounds/<int:inbound_id>`
- **Method**: `GET`
- **说明**: 返回指定入库单的表头、汇总和全部明细

入库单不存在时返回 HTTP `404`：

```json
{
  "success": false,
  "message": "入库单不存在"
}
```

### 11.7 新建入库单

- **URL**: `/api/stock-inbounds`
- **Method**: `POST`
- **说明**: 使用 `status: "draft"` 保存草稿，或使用 `status: "posted"` 直接提交过账

**请求参数**:

```json
{
  "documentNo": "RK20260908012",
  "documentDate": "2026-09-08",
  "type": "raw-material",
  "storeId": 1,
  "warehouseId": 2,
  "supplierId": 1,
  "workshop": null,
  "inspector": "张质检",
  "qualityNo": "QJ-20260908-001",
  "remark": "采购到货",
  "attachments": [
    {
      "name": "送货单.pdf",
      "size": 128000,
      "type": "application/pdf"
    }
  ],
  "status": "posted",
  "items": [
    {
      "productId": 3,
      "productCode": "RM-003",
      "productName": "轻质碳酸钙",
      "specification": "1250目 / 40kg",
      "unit": "公斤",
      "expectedQty": 100,
      "receivedQty": 98.5,
      "binCode": "A-01-03",
      "batchNo": "20260908-A",
      "unitPrice": 12.3456,
      "taxRate": 13,
      "remark": "抽检合格"
    }
  ]
}
```

**表头字段**:

| 参数 | 类型 | 草稿 | 过账 | 说明 |
|------|------|------|------|------|
| `documentNo` | string | 否 | 否 | 为空时由后端生成 `RK + YYYYMMDD + 至少三位ID` |
| `documentDate` | string | 是 | 是 | 单据日期，建议使用 `YYYY-MM-DD` |
| `type` | string | 是 | 是 | `raw-material` 或 `finished-product` |
| `storeId` | integer | 否 | 否 | 门店 ID |
| `warehouseId` | integer | 是 | 是 | 目标仓库 ID，必须存在 |
| `supplierId` | integer | 否 | 原材料必填 | 供应商 ID，原材料过账时必须有效且为 `active` |
| `workshop` | string | 否 | 否 | 成品生产车间/班组，当前为选填 |
| `inspector` | string | 否 | 否 | 检验员 |
| `qualityNo` | string | 否 | 否 | 质检单号 |
| `remark` | string | 否 | 否 | 备注，最多保存 200 字符 |
| `attachments` | array | 否 | 否 | 附件元数据数组，见下方说明 |
| `status` | string | 否 | 是 | 默认 `draft`；提交过账传 `posted` |
| `items` | array | 否 | 是 | 草稿允许空数组；过账至少一条有效明细 |

**明细字段**:

| 参数 | 类型 | 过账必填 | 说明 |
|------|------|----------|------|
| `productId` | integer | 业务必填 | 物料 ID；按入库类型关联 `products` 或 `raw_material_products` |
| `productCode` | string | 否 | 物料编码；请求也兼容 `code` |
| `productName` | string | 否 | 物料名称快照；请求也兼容 `name`，前端选择物料后自动填充 |
| `specification` | string | 否 | 规格型号 |
| `unit` | string | 否 | 基本计量单位文本 |
| `expectedQty` | number | 否 | 应收数量 |
| `receivedQty` | number | 是 | 实收数量，必须大于 `0` |
| `binCode` | string | 否 | 货位编码 |
| `batchNo` | string | 是 | 批次号 |
| `unitPrice` | number | 否 | 单价；前端限制 4 位小数 |
| `taxRate` | number | 否 | 百分数，例如 `13` 代表 13%，不是 `0.13` |
| `remark` | string | 否 | 行备注 |

> 调用方过账时必须提供 `productId`。当前接口兼容只带 `productName` 的历史明细，但没有 `productId` 的明细不会更新库存余额，也不会生成库存流水。

金额字段由服务端重新计算，不信任客户端传入值：

```text
taxAmount = receivedQty × unitPrice × taxRate ÷ 100
totalAmount = receivedQty × unitPrice + taxAmount
```

行税额、行价税合计和单据汇总均使用十进制定点计算，金额保留 2 位小数。

**成功响应**: HTTP `201`

```json
{
  "success": true,
  "message": "入库单保存成功",
  "id": 12,
  "stockIn": {
    "id": 12,
    "documentNo": "RK20260908012",
    "documentDate": "2026-09-08",
    "type": "raw-material",
    "status": "posted",
    "totalQuantity": 98.5,
    "totalTax": 158.09,
    "totalAmount": 1374.13,
    "postedAt": "2026-09-08 14:30:00",
    "items": [
      {
        "id": 28,
        "inbound_id": 12,
        "line_no": 1,
        "product_type": "raw-material",
        "productId": 3,
        "productCode": "RM-003",
        "productName": "轻质碳酸钙",
        "receivedQty": 98.5,
        "batchNo": "20260908-A",
        "unitPrice": 12.3456,
        "taxRate": 13,
        "taxAmount": 158.09,
        "totalAmount": 1374.13
      }
    ]
  }
}
```

> `attachments` 当前只把文件名、大小、MIME 类型等 JSON 元数据写入入库单，尚未提供附件二进制上传接口。

### 11.8 修改草稿或提交过账

- **URL**: `/api/stock-inbounds/<int:inbound_id>`
- **Method**: `PUT`
- **说明**: 修改现有未过账单据；传入 `status: "posted"` 时提交过账

请求字段与“新建入库单”相同。保存时会替换该单据的全部明细，不是局部合并明细。

**成功响应**:

```json
{
  "success": true,
  "message": "入库单更新成功",
  "stockIn": {
    "id": 12,
    "documentNo": "RK20260908012",
    "status": "posted"
  }
}
```

已过账单据不可再次修改或重复过账，返回 HTTP `409`：

```json
{
  "success": false,
  "message": "已过账单据不可修改"
}
```

### 11.9 作废入库单

- **URL**: `/api/stock-inbounds/<int:inbound_id>`
- **Method**: `DELETE`
- **说明**: 逻辑作废未过账单据，把状态更新为 `cancelled`，不物理删除记录

**成功响应**:

```json
{
  "success": true,
  "message": "入库单已作废"
}
```

已过账单据不能直接作废，返回 HTTP `409`；入库单不存在时返回 HTTP `404`。

### 11.10 获取库存余额

- **URL**: `/api/stock-balances`
- **Method**: `GET`
- **说明**: 汇总已过账入库数量，结果按物料类型、物料、仓库和门店分组

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 否 | `raw-material` 或 `finished-product` |

**响应示例**:

```json
[
  {
    "productType": "raw-material",
    "productId": 3,
    "warehouseId": 2,
    "storeId": 1,
    "quantity": 98.5,
    "updatedAt": "2026-09-08 14:30:00"
  }
]
```

### 11.11 过账规则与数据写入

提交 `status: "posted"` 后，后端在同一个 SQLite 事务中执行：

1. 写入或更新 `stock_inbounds` 单据头。
2. 写入 `stock_inbound_items` 入库明细。
3. 按物料、仓库、门店、货位和批次增量更新 `stock_balances`。
4. 为每条有效明细写入一条 `stock_movements` 库存流水。
5. 成品入库额外增量同步旧版 `inventory` 表，保证现有成品库存页面兼容。

原材料库存使用独立 `stock_balances` 余额，不写入旧的成品 `inventory` 表。草稿不会执行第 3 至第 5 步。

---

## 错误响应格式

多数 JSON 接口在发生错误时返回以下格式。文件下载和预览接口在失败时也返回 JSON，成功时返回文件流。

```json
{
  "success": false,
  "message": "错误描述"
}
```

**HTTP 状态码**:
- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 权限不足
- `404` - 资源不存在
- `409` - 资源状态冲突或唯一编号重复
- `500` - 服务器内部错误

---

## 数据库技术细节

### 表结构

**核心表**:
- `orders` - 订单表（209条记录）
- `products` - 商品表（15条记录）
- `raw_material_products` - 原材料商品档案表
- `inventory` - 库存表（6条记录）
- `customers` - 客户表（4条记录）
- `material_records` - 原材料使用/生产流水表（55条记录）
- `stores` - 门店表（3条记录）
- `warehouses` - 仓库表（4条记录）
- `users` - 用户表（9条记录）
- `suppliers` - 供应商基础资料表
- `stock_inbounds` - 入库单头与状态、汇总信息表
- `stock_inbound_items` - 入库单明细表
- `stock_balances` - 按物料、仓库、门店、货位和批次保存的库存余额表
- `stock_movements` - 入库过账库存流水表

**辅助表**:
- `units` - 计量单位和包装表，通过 `unit_type` 分组
- `attributes` - 商品属性表
- `attribute_options` - 属性选项表
- `warehouse_categories` - 仓库分类表
- `carrier_tags` - 物流公司标签表
- `remark_tags` - 原材料备注标签表
- `hr_reports` - 人事检测报告文件表

### 数据库索引优化

```sql
-- 订单查询优化
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(date);
CREATE INDEX idx_orders_store ON orders(store_id);

-- 商品查询优化
CREATE INDEX idx_products_code ON products(code);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_warehouse ON products(warehouse_id);

-- 原材料商品档案查询优化
CREATE INDEX idx_raw_material_products_code
ON raw_material_products(code);
CREATE INDEX idx_raw_material_products_name
ON raw_material_products(name);

-- 供应商与入库单查询优化
CREATE UNIQUE INDEX idx_suppliers_code
ON suppliers(supplier_code)
WHERE supplier_code IS NOT NULL AND trim(supplier_code) <> '';
CREATE INDEX idx_suppliers_store_status
ON suppliers(store_id, status);
CREATE INDEX idx_stock_inbounds_filter
ON stock_inbounds(receipt_type, status, document_date DESC);
CREATE INDEX idx_stock_inbound_items_inbound
ON stock_inbound_items(inbound_id, line_no);
CREATE INDEX idx_stock_balances_lookup
ON stock_balances(product_type, product_id, warehouse_id);
CREATE INDEX idx_stock_movements_product
ON stock_movements(product_type, product_id, warehouse_id, created_at DESC);
```

### 性能优化建议

1. **查询优化**: 使用索引字段作为查询条件
2. **批量操作**: 使用事务批量插入/更新数据
3. **连接管理**: 后端按请求创建 SQLite 连接，统一在请求结束后关闭
4. **备份策略**: 定期备份 `order_system.db` 文件

### 数据迁移

从 JSON 迁移到 SQLite 的数据映射：

| JSON 文件 | SQLite 表 | 记录数 |
|-----------|----------|--------|
| orders_db.json | orders | 209 |
| products_db.json | products, inventory | 15 + 6 |
| customers_db.json | customers | 4 |
| materials_db.json | material_records | 55 |
| stores_db.json | stores | 3 |
| warehouses_db.json | warehouses, warehouse_categories | 4 + N |
| users_db.json | users | 9 |

原材料商品档案 `raw_material_products` 是新增的独立表，没有对应的历史 JSON 迁移来源；新建或编辑后直接通过
`/api/raw-material-products` 持久化到 SQLite。

供应商、入库单、明细、库存余额和库存流水表由 `backend/utils/db.py` 在首次数据库连接时自动创建，
没有对应的历史 JSON 迁移来源。

---

## 权限说明

### 角色类型
- `super_admin` - 超级管理员（拥有所有权限）
- `admin` - 管理员（受限的管理权限）
- `employee` - 员工（基础权限）

### 权限列表
- `pending.view` - 查看待处理订单
- `pending.edit` - 编辑待处理订单
- `pending.delete` - 删除待处理订单
- `completed.view` - 查看已完成订单
- `completed.delete` - 删除已完成订单
- `material.edit` - 编辑材料
- `material.edit_stock` - 编辑库存
- `material.delete` - 删除材料

---

## 附录

### 订单状态说明
- `pending` - 待处理
- `completed` - 已完成
- `shipped` - 已出库/已发货

### 门店状态说明
- `active` - 启用
- `inactive` - 停用

### 入库类型说明
- `raw-material` - 原材料采购入库
- `finished-product` - 成品生产完工入库

### 入库单状态说明
- `draft` - 草稿，未改变库存
- `posted` - 已过账，已经写入库存余额和流水
- `cancelled` - 已作废

### 供应商状态说明
- `active` - 启用，可用于原材料入库过账
- `inactive` - 停用，仅保留历史关联

### 备用金类型
- `deposit` - 充值
- `withdraw` - 提现

### 发货方式
- `0` - 物流
- `1` - 零担快运
- `2` - 快递
- `3` - 专车
- `4` - 其它

---

## 常见问题 (FAQ)

### 1. 数据库文件在哪里？
数据库文件位于项目根目录下的 `data/order_system.db`。Docker 部署时默认使用容器内的 `/app/data/order_system.db`。

### 2. 如何备份数据？
```bash
# 方法1: 直接复制数据库文件
copy data\order_system.db data\order_system_backup.db

# 方法2: 导出为 JSON（使用备份脚本）
cd backend
py tools\backup_json.py
```

### 3. 如何使用历史 JSON 备份？
当前运行版本以 SQLite 为准，不再提供切换回 JSON 读写模式的操作。历史 JSON 文件仅用于迁移或人工核对，
可以使用 `backend/tools/backup_json.py` 从当前 SQLite 导出一份新的 JSON 备份。

### 4. 并发支持如何？
SQLite 支持**多读一写**模式：
- ✅ 多个用户可以同时读取数据
- ✅ 一个用户写入时，其他用户可以继续读取
- ⚠️ 同时只能有一个用户执行写入操作

对于中小型团队（< 20人）完全够用。

### 5. 如何查看数据库内容？
推荐工具：
- **DB Browser for SQLite** (免费，图形界面)
- **SQLiteStudio** (免费，跨平台)
- **命令行**: `sqlite3 data/order_system.db`

### 6. API 响应速度变慢怎么办？
1. 检查数据库文件大小（正常 < 50MB）
2. 运行 `VACUUM` 清理碎片：
   ```bash
   sqlite3 data/order_system.db "VACUUM;"
   ```
3. 重建索引：
   ```bash
   sqlite3 data/order_system.db "REINDEX;"
   ```

### 7. 成品和原材料为什么使用不同接口？
两类商品使用相同的录入字段结构，但数据存储目标不同：

- 成品商品使用 `/api/products`，保存到 `products`
- 原材料商品使用 `/api/raw-material-products`，保存到 `raw_material_products`
- 公共组件 `ProductFormModal.vue` 会根据路由或 `mode` 自动选择对应接口

这样可以避免原材料档案和成品档案混在同一张表中，同时保留相同的前端录入体验。

---

## 更新日志

### v2.3.0 (2026-09-08)
- ✅ 新增供应商 CRUD 与 `suppliers` 数据表
- ✅ 新增原材料采购入库和成品生产完工入库接口
- ✅ 新增入库单头、入库明细、库存余额和库存流水数据表
- ✅ 支持草稿保存、事务过账、防止重复过账和未过账单据作废
- ✅ 成品过账同步旧版 `inventory` 表，原材料使用独立库存余额
- ✅ 两个库存页面接入公共 `StockInOrderModal.vue` 入库单弹窗

### v2.2.0 (2026-09-08)
- ✅ 新增原材料商品档案 CRUD 接口和 `raw_material_products` 独立数据表
- ✅ `ProductFormModal.vue` 支持成品和原材料两种录入模式
- ✅ `units` 增加 `unit_type` 分组，计量单位与包装数据分离
- ✅ 新增计量单位、包装分组查询接口
- ✅ 订单接口补充 `goods_packaging` 和 `logistics_service` 字段说明

### v2.1.0 (2026-09-07)
- ✅ 补充人事检测报告文件管理接口
- ✅ 补充文件上传、预览、分享、移动和文件夹管理说明
- ✅ 同步 `hr_reports` 数据表字段文档

### v2.0.0 (2026-09-06)
- ✅ 迁移至 SQLite 数据库
- ✅ 查询性能提升 10-100 倍
- ✅ 支持并发读写
- ✅ 添加数据库索引优化
- ✅ 保持 API 完全兼容

### v1.0.0 (2026-08-30)
- 初始版本
- 使用 JSON 文件存储

---

## 技术支持

如有问题，请联系开发团队或查看：
- 项目文档: [README_SQLITE.md](../README_SQLITE.md)
- 迁移文档: [MIGRATION_SQLITE.md](../MIGRATION_SQLITE.md)
- 测试脚本: [backend/test_sqlite.py](../backend/test_sqlite.py)
