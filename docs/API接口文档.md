# API 接口文档

## 基础信息

- **Base URL**: `/api`
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 目录

1. [用户管理](#1-用户管理)
2. [门店管理](#2-门店管理)
3. [仓库管理](#3-仓库管理)
4. [商品管理](#4-商品管理)
5. [订单管理](#5-订单管理)
6. [材料库存管理](#6-材料库存管理)
7. [运费记录管理](#7-运费记录管理)

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

#### 4.1.1 获取所有单位
- **URL**: `/api/products/units`
- **Method**: `GET`

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

#### 4.1.2 新增单位
- **URL**: `/api/products/units`
- **Method**: `POST`

**请求参数**:
```json
{
  "name": "箱"
}
```

**响应示例**:
```json
{
  "success": true,
  "unit": {
    "id": 10,
    "name": "箱",
    "createdAt": "2026-08-30 12:00:00"
  }
}
```

#### 4.1.3 删除单位
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

---

## 5. 订单管理

### 5.1 获取所有订单
- **URL**: `/api/orders`
- **Method**: `GET`

**响应示例**:
```json
[
  {
    "id": 1,
    "title": "",
    "status": "pending",
    "type": 1,
    "store_id": 1,
    "date": "2026-08-30 12:00",
    "completed_date": "",
    "shipped_date": "",
    "shipping_method": "",
    "shipping_custom": "",
    "logistics_no": "",
    "order_client": "客户名称",
    "receiver_name": "收货人",
    "receiver_phone": "13800138000",
    "receiver_address": "收货地址",
    "goods_name": "货物名称",
    "goods_weight": "100kg",
    "goods_quantity": "10",
    "goods_packaging": "箱",
    "logistics_service": "顺丰",
    "remark": "备注"
  }
]
```

### 5.2 创建订单
- **URL**: `/api/orders`
- **Method**: `POST`

**请求参数**:
```json
{
  "type": 1,
  "order_client": "客户名称",
  "receiver_name": "收货人",
  "receiver_phone": "13800138000",
  "receiver_address": "收货地址",
  "goods_name": "货物名称",
  "goods_weight": "100kg",
  "goods_quantity": "10",
  "goods_packaging": "箱",
  "logistics_service": "顺丰",
  "remark": "备注"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 2,
    "title": "",
    "status": "pending",
    "type": 1,
    "store_id": 1,
    "date": "2026-08-30 12:00",
    "order_client": "客户名称",
    "receiver_name": "收货人",
    "receiver_phone": "13800138000",
    "receiver_address": "收货地址",
    "goods_name": "货物名称",
    "goods_weight": "100kg",
    "remark": "备注"
  }
}
```

### 5.3 更新订单状态
- **URL**: `/api/orders/<int:order_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "status": "completed"
}
```

**或者更新物流信息**:
```json
{
  "logistics_no": "SF1234567890",
  "freight_costs": [
    {
      "note": "运费",
      "amount": 50
    }
  ]
}
```

**或者更新为已发货状态**:
```json
{
  "status": "shipped",
  "shipping_method": 0,
  "logistics_no": "SF1234567890",
  "shipped_date": "2026-08-30 12:00",
  "freight_costs": [
    {
      "note": "运费",
      "amount": 50
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

### 5.4 删除订单
- **URL**: `/api/orders/<int:order_id>`
- **Method**: `DELETE`
- **权限**: 需要对应的删除权限
- **Header**: `Role: super_admin`, `Username: admin`

**响应示例**:
```json
{
  "success": true
}
```

### 5.5 编辑订单内容
- **URL**: `/api/orders/<int:order_id>/edit`
- **Method**: `PUT`
- **权限**: 需要 `pending.edit` 权限
- **Header**: `Role: super_admin`, `Username: admin`

**请求参数**:
```json
{
  "title": "",
  "type": 1,
  "date": "2026-08-30 12:00",
  "order_client": "新客户名称",
  "receiver_name": "新收货人",
  "receiver_phone": "13900139000",
  "receiver_address": "新收货地址",
  "goods_name": "新货物名称",
  "goods_weight": "200kg",
  "goods_quantity": "20",
  "goods_packaging": "袋",
  "logistics_service": "中通",
  "remark": "新备注"
}
```

**响应示例**:
```json
{
  "success": true
}
```

### 5.6 上传订单回单
- **URL**: `/api/orders/<int:order_id>/upload_receipt`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

**请求参数**:
- `receipt_image`: 图片文件

**响应示例**:
```json
{
  "success": true,
  "message": "新图片上传并保存成功，旧图片已清理",
  "image_url": "/uploads/2026-08/客户订单_收货人_2026-08-30_A1B2.jpg"
}
```

### 5.7 删除订单回单
- **URL**: `/api/orders/<int:order_id>/receipt`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "回单图片已彻底删除"
}
```

### 5.8 更新订单已支付金额
- **URL**: `/api/orders/<int:order_id>/paid-amount`
- **Method**: `PUT`
- **Header**: `Username: admin`

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

### 5.9 获取运营商标签
- **URL**: `/api/orders/carrier_tags`
- **Method**: `GET`

**响应示例**:
```json
["顺丰", "中通", "申通", "圆通"]
```

### 5.10 添加运营商标签
- **URL**: `/api/orders/carrier_tags`
- **Method**: `POST`

**请求参数**:
```json
{
  "tag": "韵达"
}
```

**响应示例**:
```json
{
  "success": true,
  "tags": ["韵达", "顺丰", "中通", "申通", "圆通"]
}
```

---

## 6. 材料库存管理

### 6.1 获取材料库存信息
- **URL**: `/api/materials`
- **Method**: `GET`

**响应示例**:
```json
{
  "stock": 1000,
  "records": [
    {
      "id": 1,
      "used": 50,
      "produced": 100,
      "date": "2026-08-30 12:00",
      "remark": "生产备注"
    }
  ],
  "remark_tags": ["生产", "领料", "退料"]
}
```

### 6.2 添加材料记录
- **URL**: `/api/materials`
- **Method**: `POST`

**请求参数**:
```json
{
  "used": 50,
  "produced": 100,
  "remark": "生产备注"
}
```

**响应示例**:
```json
{
  "success": true,
  "id": 2
}
```

### 6.3 更新库存
- **URL**: `/api/materials/stock`
- **Method**: `PUT`

**请求参数**:
```json
{
  "stock": 1200
}
```

**响应示例**:
```json
{
  "success": true
}
```

### 6.4 更新材料记录
- **URL**: `/api/materials/<int:record_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "used": 60,
  "produced": 120,
  "remark": "更新备注"
}
```

**响应示例**:
```json
{
  "success": true
}
```

### 6.5 删除材料记录
- **URL**: `/api/materials/<int:record_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true
}
```

---

## 7. 运费记录管理

### 7.1 获取所有运费记录
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

### 7.2 创建运费记录
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

### 7.3 获取所有备用金记录
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

### 7.4 创建备用金记录
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

### 7.5 获取最新备用金余额
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

### 7.6 更新备用金金额
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

## 错误响应格式

所有接口在发生错误时返回以下格式：

```json
{
  "error": "错误描述",
  "message": "详细错误信息"
}
```

**HTTP 状态码**:
- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 权限不足
- `404` - 资源不存在
- `500` - 服务器内部错误

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

### 备用金类型
- `deposit` - 充值
- `withdraw` - 提现

### 发货方式
- `0` - 物流
- `1` - 零担快运
- `2` - 快递
- `3` - 专车
- `4` - 其它
