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
6. [运营商标签管理](#6-运营商标签管理)
7. [客户管理](#7-客户管理)
8. [材料库存管理](#8-材料库存管理)
9. [运费记录管理](#9-运费记录管理)

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
- **说明**: 获取所有订单列表，新旧订单格式共存

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
    "receiver_name": "段洪强",
    "receiver_phone": "15527382584",
    "receiver_address": "湖北省武汉市江夏区光谷芯中心二期E区9栋",
    
    "remark": "订单备注"
  }
]
```

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
    "customerCode": "C20260001",
    "customerName": "张三超市",
    "storeId": 1,
    "contactPerson": "张三",
    "phone": "13800138000",
    "address": "广东省广州市天河区XX路XX号",
    "balance": 5000,
    "receivable": 5000,
    "bankName": "工商银行",
    "bankAccount": "6222021234567890",
    "bankCode": "102100099996",
    "taxNumber": "91440101MA5CQ1234",
    "remark": "重点客户",
    "status": "active",
    "createdAt": "2026-01-15T10:30:00",
    "updatedAt": "2026-01-15T10:30:00"
  }
]
```

### 6.2 获取单个客户详情
- **URL**: `/api/customers/<int:customer_id>`
- **Method**: `GET`

**响应示例**:
```json
{
  "id": 1,
  "customerCode": "C20260001",
  "customerName": "张三超市",
  "storeId": 1,
  "contactPerson": "张三",
  "phone": "13800138000",
  "address": "广东省广州市天河区XX路XX号",
  "balance": 5000,
  "receivable": 5000,
  "bankName": "工商银行",
  "bankAccount": "6222021234567890",
  "bankCode": "102100099996",
  "taxNumber": "91440101MA5CQ1234",
  "remark": "重点客户",
  "status": "active",
  "createdAt": "2026-01-15T10:30:00",
  "updatedAt": "2026-01-15T10:30:00"
}
```

### 6.3 创建客户
- **URL**: `/api/customers`
- **Method**: `POST`

**请求参数**:
```json
{
  "customerName": "张三超市",
  "customerCode": "C20260001",
  "storeId": 1,
  "contactPerson": "张三",
  "phone": "13800138000",
  "address": "广东省广州市天河区XX路XX号",
  "balance": 5000,
  "initialDebt": 0,
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
  "id": 1,
  "customerCode": "C20260001",
  "customerName": "张三超市",
  "storeId": 1,
  "contactPerson": "张三",
  "phone": "13800138000",
  "address": "广东省广州市天河区XX路XX号",
  "balance": 5000,
  "receivable": 0,
  "bankName": "工商银行",
  "bankAccount": "6222021234567890",
  "bankCode": "102100099996",
  "taxNumber": "91440101MA5CQ1234",
  "remark": "重点客户",
  "status": "active",
  "createdAt": "2026-09-01T10:30:00",
  "updatedAt": "2026-09-01T10:30:00"
}
```

### 6.4 更新客户信息
- **URL**: `/api/customers/<int:customer_id>`
- **Method**: `PUT`

**请求参数**:
```json
{
  "customerName": "张三超市",
  "customerCode": "C20260001",
  "storeId": 1,
  "contactPerson": "张三",
  "phone": "13800138000",
  "address": "广东省广州市天河区XX路XX号",
  "balance": 5000,
  "initialDebt": 5000,
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
  "id": 1,
  "customerCode": "C20260001",
  "customerName": "张三超市",
  "storeId": 1,
  "contactPerson": "张三",
  "phone": "13800138000",
  "address": "广东省广州市天河区XX路XX号",
  "balance": 5000,
  "receivable": 5000,
  "bankName": "工商银行",
  "bankAccount": "6222021234567890",
  "bankCode": "102100099996",
  "taxNumber": "91440101MA5CQ1234",
  "remark": "重点客户",
  "status": "active",
  "createdAt": "2026-09-01T10:30:00",
  "updatedAt": "2026-09-01T11:30:00"
}
```

### 6.5 删除客户
- **URL**: `/api/customers/<int:customer_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true,
  "message": "删除成功",
  "customer": {
    "id": 1,
    "customerCode": "C20260001",
    "customerName": "张三超市"
  }
}
```

---

## 8. 材料库存管理

### 8.1 获取材料库存信息
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

### 8.2 添加材料记录
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

### 8.3 更新库存
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

### 8.4 更新材料记录
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

### 8.5 删除材料记录
- **URL**: `/api/materials/<int:record_id>`
- **Method**: `DELETE`

**响应示例**:
```json
{
  "success": true
}
```

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
