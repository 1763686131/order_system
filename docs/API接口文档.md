# API 接口文档

## 基础信息

- **Base URL**: `/api`
- **数据格式**: JSON
- **字符编码**: UTF-8
- **数据库**: SQLite 3
- **后端框架**: Flask + Python 3

### 通用请求约定

| Header | 必填 | 说明 |
|---|---|---|
| `Content-Type: application/json` | 是（JSON 请求） | 请求体编码 |
| `Cookie` | 浏览器自动携带 | 登录成功后由服务端 session 设置，前端不得自行构造身份 |

`Username`、`Role` 请求头已停用，不能再作为身份或权限依据。业务单据中的
审核人、操作人和上传人统一从服务端 session 解析。前端请求需开启
`withCredentials`，同源部署无需额外配置；开发跨域来源通过 `CORS_ORIGINS`
环境变量声明。

除文件上传接口外，请求和响应均使用 JSON。常见错误响应包含 `message` 或
`error` 字段，前端应优先显示服务端返回的信息。

## 版本历史

- **v4.0** (2026-09-18) - 重构 session 登录、首次超级管理员初始化、账号、员工档案、权限组和触屏端后端鉴权
- **v3.4** (2026-09-17) - 新增打印模板数据库、模板 CRUD、默认模板和旧 localStorage 模板迁移接口
- **v3.3** (2026-09-16) - 下线旧 `/api/materials` 使用/生产流水接口并删除 `material_records`、旧 `remark_tags` 表
- **v3.2** (2026-09-16) - 新增库存流水查询接口，支持按物料、门店和仓库查询已审核入库与出库明细
- **v3.1** (2026-09-16) - 补充销售订单审核/反审核接口、审核人姓名解析及审核字段说明
- **v3.0** (2026-09-14) - 客户期初欠款与储值字段优化，新增 `initial_receivable_at` 和 `balance_at` 时间戳字段
- **v2.8** (2026-09-14) - 新增客户应收对账单详情接口，复用审核流水并支持商品级欠款分摊
- **v2.7** (2026-09-14) - 新增银行账户、银行卡图片上传及结算账户动态关联接口
- **v2.6** (2026-09-14) - 新增退货单草稿、修改、审核、反审核及客户应收和库存联动接口
- **v2.5** (2026-09-11) - 新增服务器路径配置、目录浏览和 NAS 检测报告动态扫描接口
- **v2.4** (2026-09-10) - 新增收款单、审核入账、反审核和客户应收联动接口
- **v2.3** (2026-09-08) - 新增供应商、入库单、库存余额与事务过账接口
- **v2.2** (2026-09-08) - 新增原材料商品档案接口，补充单位分组接口
- **v2.1** (2026-09-07) - 补充人事检测报告文件管理接口文档
- **v2.0** (2026-09-06) - 迁移至 SQLite 数据库，优化性能和并发支持
- **v1.0** (2026-08-30) - 初始版本，使用 JSON 文件存储

---

## 目录

1. [认证、账号、权限组与员工管理](#1-认证账号权限组与员工管理)
2. [门店管理](#2-门店管理)
3. [仓库管理](#3-仓库管理)
4. [商品管理](#4-商品管理)
5. [订单管理](#5-订单管理)
6. [运营商标签管理](#6-运营商标签管理)
7. [客户管理](#7-客户管理)
8. [原材料触屏出库](#8-原材料触屏出库)
9. [运费记录管理](#9-运费记录管理)
10. [人事检测报告文件管理](#10-人事检测报告文件管理)
11. [供应商与入库管理](#11-供应商与入库管理)
12. [收款单与应收核销](#12-收款单与应收核销)
13. [退货单与客户应收、库存联动](#13-退货单与客户应收库存联动)
14. [银行账户与结算账户](#14-银行账户与结算账户)
15. [系统设置与服务器路径](#15-系统设置与服务器路径)
16. [打印模板管理](#16-打印模板管理)

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
- `bank_accounts.store_id/account_number` - 按门店查询并保证门店内账号唯一
- `print_templates.business_type/is_default` - 按业务类型加载默认打印模板

---

## 1. 认证、账号、权限组与员工管理

### 1.1 初始化状态
- **URL**: `/api/auth/bootstrap-status`
- **Method**: `GET`
- **权限**: 公开

系统判断是否存在“启用账号 + 启用权限组 + `full_access = 1`”的有效超级管理员。
只要不存在有效超级管理员，`setupRequired` 就返回 `true`，即使数据库中仍有普通
用户也允许重新创建超级管理员。

```json
{
  "success": true,
  "setupRequired": true,
  "reason": "missing_super_admin"
}
```

### 1.2 创建超级管理员
- **URL**: `/api/auth/bootstrap`
- **Method**: `POST`
- **权限**: 仅在没有有效超级管理员时开放

```json
{
  "displayName": "系统管理员",
  "username": "admin",
  "password": "至少8位密码",
  "confirmPassword": "至少8位密码"
}
```

接口在事务内再次检查有效超级管理员，防止并发创建多个初始超管。创建成功后
会同步创建一条同名空白员工档案并绑定账号，然后关闭初始化入口；如果最后一个
超级管理员被直接从数据库删除，入口会重新开放。

### 1.3 登录、退出和当前账号

| Method | URL | 说明 |
|---|---|---|
| `POST` | `/api/auth/login` | 使用账号密码登录并建立 session |
| `POST` | `/api/auth/logout` | 销毁当前 session |
| `GET` | `/api/auth/me` | 获取当前账号、权限组和权限快照 |
| `PUT` | `/api/auth/profile` | 修改当前账号姓名和头像地址 |
| `PUT` | `/api/auth/password` | 校验当前密码后修改密码 |

密码只保存 Werkzeug 哈希，任何列表和详情接口均不返回明文密码或密码哈希。

### 1.4 后台账号管理

| Method | URL | 说明 |
|---|---|---|
| `GET` | `/api/admin/users` | 查询账号列表 |
| `POST` | `/api/admin/users` | 创建账号并绑定权限组 |
| `PUT` | `/api/admin/users/<user_id>` | 修改资料、状态和权限组 |
| `PUT` | `/api/admin/users/<user_id>/password` | 重置账号密码 |

以上接口仅允许超级管理员。系统禁止通过后台停用或移除最后一个有效超级管理员。
账号不再直接保存权限数组，实际权限通过账号绑定的员工档案，从
`employee_roles -> role_permissions` 汇总。

### 1.5 权限目录与权限组

| Method | URL | 说明 |
|---|---|---|
| `GET` | `/api/admin/permissions` | 获取触屏端权限目录 |
| `GET` | `/api/admin/roles` | 获取权限组、成员数和权限编码 |
| `POST` | `/api/admin/roles` | 创建权限组 |
| `PUT` | `/api/admin/roles/<role_id>` | 修改权限组、数据范围和权限 |
| `PUT` | `/api/admin/roles/<role_id>/members` | 使用员工 ID 更新角色组成员 |

内置 `super_admin` 权限组拥有 `full_access = 1`，不允许通过普通编辑接口修改。
角色组成员来自员工档案。未开通账号的员工也可以先加入角色组；后续在员工档案中
开通账号后，会直接继承该员工已有的角色组和权限。
门店和仓库范围分别保存在 `role_stores`、`role_warehouses`。

### 1.6 员工档案和可选登录账号

| Method | URL | 说明 |
|---|---|---|
| `GET` | `/api/admin/employees` | 查询员工档案和绑定账号 |
| `POST` | `/api/admin/employees` | 创建员工档案，可同时开通账号 |
| `PUT` | `/api/admin/employees/<employee_id>` | 修改档案、密码和账号状态 |

员工抽屉不配置权限组，角色组关系统一在“角色组管理”页面维护。没有填写
登录账号时只创建员工档案，账号状态为 `pending`。账号是员工档案的可选能力，
系统会保证每个账号都绑定一条员工档案，但允许员工档案没有账号。

### 1.7 已下线旧接口

旧 `/api/login`、`/api/users`、`/api/users/<username>/permissions` 等接口不再
注册。旧 `users.password`、`users.role`、`users.permissions` 表结构在 v4.0
迁移时直接删除，不保留旧用户数据。

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
> 原材料数量由入库、出库审核和库存流水统一管理，不允许直接修改历史汇总值。

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
    "status": "shipped",
    "audit_state": 1,
    "audit_by": "系统超管",
    "audit_date": "2026-09-16T10:30:00",
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
  "totalPackages": 3,
  
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
- **总件数字段 `totalPackages`**：前端录入时默认自动累加各商品的 `packages`，用户可手动修改此值，以用户最终修改的值为准保存到数据库的 `total_packages` 字段

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
  "totalPackages": 5,
  
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

### 5.5 审核与反审核销售订单

- **URL**: `/api/orders/<int:order_id>`
- **Method**: `PUT`
- **身份**: 服务端 Session 中的当前登录账号
- **适用范围**: 有订单编号和商品明细、且 `status` 为 `shipped` 的销售订单

**审核请求**:

```json
{
  "audit_state": 1
}
```

**反审核请求**:

```json
{
  "audit_state": 0
}
```

审核在同一个 SQLite 事务中完成：

1. 从服务端 Session 读取当前用户姓名，写入 `orders.audit_by`。
2. 写入 `audit_date`，并将 `audit_state` 更新为 `1`。
3. 根据应收金额、本次收款和客户储值更新客户欠款与储值。
4. 写入一条有效的 `order_audit` 客户账户流水。
5. 本次有收款且结算账户有效时，同步增加银行账户余额。

反审核会撤销原审核流水，恢复客户储值与应收数据，并清空订单的
`audit_by`、`audit_date`。如果本单欠款已被后续收款核销，则返回 `409`，
避免账务数据被破坏。

**审核成功响应示例**:

```json
{
  "success": true,
  "message": "审核成功，客户应收已更新",
  "data": {
    "id": 244,
    "status": "shipped",
    "audit_state": 1,
    "audit_by": "系统超管",
    "audit_date": "2026-09-16T10:30:00"
  },
  "account": {
    "customerId": 4,
    "storedBalanceApplied": 0,
    "receivableChange": 0,
    "balanceAfter": 22750,
    "receivableAfter": 0
  }
}
```

**审核字段**:

| 字段 | 类型 | 说明 |
|---|---|---|
| `audit_state` | integer | `0` 未审核，`1` 已审核/已过账 |
| `audit_by` | string | 审核人姓名；由请求头中的登录账号解析 |
| `audit_date` | string | 审核时间，ISO 8601 格式 |
| `balance_applied` | number | 本单使用的客户储值 |
| `current_debt` | number | 审核后本单实际增加的应收欠款 |

**常见状态码**:

| 状态码 | 场景 |
|---|---|
| `404` | 订单不存在 |
| `409` | 订单状态不允许审核、客户不存在、重复审核或无法反审核 |
| `500` | 数据库或服务端异常；不会提交部分账务变更 |

### 5.6 删除订单
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

### 5.7 上传回单图片
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

### 5.8 删除回单图片
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

### 5.9 批量删除订单
- **说明**: 前端通过并发调用 DELETE 接口实现批量删除
- **逻辑**: 使用 `Promise.allSettled()` 确保所有请求完成，统计成功和失败数量

### 5.10 更新订单已支付金额
- **URL**: `/api/orders/<int:order_id>/paid-amount`
- **Method**: `PUT`
- **权限**: 仅超级管理员
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
    "balanceAt": null,
    "initialReceivable": 5000,
    "initialReceivableAt": "2026-09-01T12:58:31",
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
  "balanceAt": null,
  "initialReceivable": 5000,
  "initialReceivableAt": "2026-09-01T12:58:31",
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
- `balance`: 当前储值余额（客户预付款，可用于抵扣订单）
- `balanceAt`: 储值余额最近一次录入/修改时间；储值为 0 时为 `null`
- `initialReceivable`: 期初欠款金额（客户的历史欠款，作为应收起点）
- `initialReceivableAt`: 期初欠款最近一次录入/修改时间；期初欠款为 0 时为 `null`
- `receivable`: 当前应收欠款（期初欠款 + 审核订单新增欠款 - 已收回欠款 - 优惠）
- `bankName`: 开户行
- `bankAccount`: 银行账号
- `bankCode`: 银行代码
- `taxNumber`: 税号
- `remark`: 备注
- `status`: 客户状态（active/inactive）

**储值与期初欠款业务规则**:
1. **录入新客户时**：
   - 填入 `balance` 大于 0：自动生成 `balanceAt` 为当前时间
   - 填入 `initialDebt` 大于 0：自动生成 `initialReceivableAt` 为当前时间，同时设置 `receivable = initialDebt`
   - 留空或为 0：对应的金额和时间字段均为 `null`

2. **修改客户时**：
   - 修改 `balance` 为新值：更新 `balanceAt` 为当前时间
   - 修改 `initialDebt` 为新值：更新 `initialReceivableAt` 为当前时间，并重新计算 `receivable = 旧receivable - 旧initialDebt + 新initialDebt`
   - 输入 0 或留空：清空对应的金额字段和时间戳字段
   - 如果修改期初欠款导致 `receivable < 0`，接口返回 400 错误

3. **对账单显示**：
   - 期初欠款和储值会在对账单接口中作为独立记录返回
   - 期初欠款的 `businessType` 为 `INITIAL`，储值的 `businessType` 为 `BALANCE`
   - 按时间排序时使用对应的时间戳字段

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
    "balanceAt": null,
    "initialReceivable": 0,
    "initialReceivableAt": null,
    "receivable": 0,
    "status": "active",
    "createdAt": "2026-09-06T10:30:00"
  }
}
```

`balance` 表示储值余额，`initialDebt` 表示期初欠款。服务端会在金额大于 0 时自动记录对应的 `balanceAt` 或 `initialReceivableAt` 时间戳。

**数据类型转换说明**：
- 前端传递的 `balance` 和 `initialDebt` 会被后端转换为 float 类型
- 所有财务计算使用 Decimal 类型确保精度，但在执行 SQL 前会显式转换为 float
- 这样可以避免 SQLite 参数绑定的类型错误

**示例场景**：
1. 新增客户，期初欠款 5000 元，储值 0 元：
   - `initialDebt: 5000` → `initialReceivable: 5000`, `initialReceivableAt: "2026-09-14T10:30:00"`, `receivable: 5000`
   - `balance: 0` → `balance: 0`, `balanceAt: null`

2. 客户充值 1000 元储值：
   - `balance: 1000` → `balance: 1000`, `balanceAt: "2026-09-14T11:00:00"`

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
  "initialDebt": 8000,
  "remark": "更新备注"
}
```

更新客户时，`balance` 和 `initialDebt` 都是覆盖写入：
- 传入新的正数：覆盖原金额并更新时间戳为当前时间
- 传入 `0`、空字符串或 `null`：清除对应金额字段和时间戳字段
- 修改期初欠款：自动调整当前应收欠款 = `旧receivable - 旧initialDebt + 新initialDebt`
- 若调整后当前应收小于 0：接口返回 `400` 错误并拒绝保存

**数据库字段映射**：
| 前端字段 | 后端字段 | 数据库字段 | 类型 | 说明 |
|---------|---------|-----------|------|------|
| balance | balance | balance | REAL | 储值余额 |
| - | balanceAt | balance_at | TEXT | 储值调整时间 |
| initialDebt | initial_receivable | initial_receivable | REAL | 期初欠款 |
| - | initialReceivableAt | initial_receivable_at | TEXT | 期初欠款时间 |

**修改示例**：
1. 修改期初欠款从 5000 元到 8000 元：
   - 旧数据：`receivable: 12000`, `initialReceivable: 5000`
   - 新数据：`initialDebt: 8000`
   - 结果：`receivable: 15000`, `initialReceivable: 8000`, `initialReceivableAt: "2026-09-14T14:30:00"`

2. 清空期初欠款（输入 0）：
   - 旧数据：`receivable: 12000`, `initialReceivable: 5000`
   - 新数据：`initialDebt: 0`
   - 结果：`receivable: 7000`, `initialReceivable: 0`, `initialReceivableAt: null`

3. 修改储值从 0 到 2000 元：
   - 旧数据：`balance: 0`, `balanceAt: null`
   - 新数据：`balance: 2000`
   - 结果：`balance: 2000`, `balanceAt: "2026-09-14T15:00:00"`

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

### 7.6 获取应收欠款汇总

- **URL**: `/api/customers/receivables`
- **Method**: `GET`
- **说明**: 获取客户期初欠款、订单/退货产生的净应收变动、收回欠款、优惠和当前净应收欠款。储值/预收仍单独保存，但列表中的 `receivable` 按“实际应收 - 储值余额”计算；收款超过应收时保留负数，表示客户储值信用。反审核按原流水撤销。

**响应示例**:

```json
{
  "items": [
    {
      "customerId": 1,
      "customerCode": "001",
      "customerName": "李超",
      "contactPerson": "李超",
      "phone": "13800138000",
      "storedBalance": 0,
      "initialDebt": 0,
      "receivableIncrease": 5000,
      "debtRecovered": 3000,
      "discountAmount": 0,
      "receivable": 2000
    }
  ],
  "total": 1,
  "summary": {
    "initialDebt": 0,
    "receivableIncrease": 5000,
    "debtRecovered": 3000,
    "discountAmount": 0,
    "receivable": 2000
  }
}
```

### 7.7 获取客户应收欠款详情（对账单）

- **URL**: `/api/customers/<int:customer_id>/debt-details`
- **Method**: `GET`
- **说明**: 获取指定客户的应收对账单，统一展示已审核且仍有效的销售订单、退货单和收款单流水，并将当前期初欠款、储值作为虚拟记录加入同一账单。接口直接读取 `customer_account_transactions`，并关联原业务单据及商品明细，不新增重复账务表，也不会单独生成“优惠调整”记录。

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `startDate` | string | 否 | 开始日期，格式 `YYYY-MM-DD`，只过滤列表 |
| `endDate` | string | 否 | 结束日期，格式 `YYYY-MM-DD`，只过滤列表 |
| `businessType` | string | 否 | `ORDER` 销售订单、`RETURN` 退货单、`PAYMENT` 收款单、`INITIAL` 期初欠款、`BALANCE` 储值调整；为空表示全部 |
| `expandProducts` | boolean | 否 | 是否返回商品级明细及分摊欠款，默认 `false`；详情页应传 `true` |

**响应示例**:

```json
{
  "customerId": 5,
  "customerCode": "001",
  "customerName": "武汉海威船舶",
  "storeId": 1,
  "storeName": "总部店",
  "initialDebt": 5000.00,
  "initialDebtAt": "2026-09-01T12:58:31",
  "storedBalance": 800.00,
  "balanceAt": "2026-09-12T09:30:00",
  "totalReceivable": 7742.50,
  "summary": {
    "initialDebt": 5000.00,
    "storedBalance": 800.00,
    "receivableIncrease": 5542.50,
    "debtRecovered": 2800.00,
    "discountAmount": 0.00,
    "receivable": 7742.50
  },
  "records": [
    {
      "id": "tx-123",
      "transactionId": 123,
      "businessDate": "2026-09-10",
      "docNumber": "SO20260910001",
      "businessType": "ORDER",
      "orderAmount": 2542.50,
      "paidAmount": 1000.00,
      "storedBalanceApplied": 0.00,
      "debtAmount": 1542.50,
      "currentDebt": 6542.50,
      "hasMultipleProducts": true,
      "productCount": 2,
      "products": [
        {
          "productId": 10,
          "name": "碳纤维胶",
          "quantity": 10,
          "unit": "桶",
          "price": 100.00,
          "subtotal": 1000.00,
          "allocatedDebt": 685.56,
          "cumulativeDebt": 5685.56
        },
        {
          "productId": 15,
          "name": "环氧树脂",
          "quantity": 25,
          "unit": "桶",
          "price": 50.00,
          "subtotal": 1250.00,
          "allocatedDebt": 856.94,
          "cumulativeDebt": 6542.50
        }
      ]
    }
  ],
  "total": 1
}
```

**计算与状态规则**:

1. 只纳入 `customer_account_transactions.status = 'active'` 的 `order_audit`、`customer_return`、`customer_payment` 流水；已反审核流水及反向流水不展示。当前期初欠款会生成一条 `INITIAL` 记录，当前储值会生成一条 `BALANCE` 记录。

2. **期初欠款记录格式**（businessType: INITIAL）：
   ```json
   {
     "id": "initial-5",
     "businessDate": "2026-09-01T12:58:31",
     "docNumber": "期初欠款",
     "businessType": "INITIAL",
     "orderAmount": 5000.00,
     "paidAmount": 0.00,
     "debtAmount": 5000.00,
     "currentDebt": 5000.00,
     "products": [],
     "hasMultipleProducts": false,
     "productCount": 0,
     "remark": "客户期初欠款"
   }
   ```

3. **储值记录格式**（businessType: BALANCE）：
   ```json
   {
     "id": "balance-5",
     "businessDate": "2026-09-12T09:30:00",
     "docNumber": "储值调整",
     "businessType": "BALANCE",
     "balanceAmount": 800.00,
     "debtAmount": 0.00,
     "currentDebt": 5000.00,
     "products": [],
     "hasMultipleProducts": false,
     "productCount": 0,
     "remark": "客户储值余额"
   }
   ```

4. `debtAmount` 使用净应收变动：销售订单会加上本单使用的储值抵扣，退货按实际核销金额减少应收，收款会把本次预收一并计入负数，因此收款超过应收时可显示为负数。期初欠款的 `debtAmount` 为正数，已由付款流水覆盖的储值记录不重复计入。

5. `currentDebt` 按业务日期、流水 ID 顺序累计净应收变动，`INITIAL` 记录作为累计起点，`BALANCE` 只补记未被付款流水覆盖的手工储值。接口内部按时间正序计算后返回，前端默认按最新时间倒序展示（时间近的在上面），因此修改期初欠款或储值后会显示在最新发生时间的位置。日期或业务类型筛选只影响列表，不改变累计欠款结果。

6. `expandProducts=true` 时，商品按小计占比拆分 `debtAmount`；商品金额合计为 0 时平均分摊，最后一项用差额修正，确保分摊合计与本单欠款精确到分。

7. 收款单不包含商品明细；优惠金额保留在原订单/收款流水字段中，接口不生成独立优惠调整行。

8. **前端视觉标识**：期初欠款记录使用黄色标签（#d97706 背景），储值记录使用蓝色标签（#0891b2 背景），与普通订单和收款记录明确区分。

---

## 8. 原材料触屏出库

> 原材料商品档案请参阅 [4.5 原材料商品档案](#45-原材料商品档案)。
> 原材料库存以 `stock_balances` 为余额来源，只有审核后的入库单和出库单能够改变库存。

### 8.1 获取原材料出库触屏设置
- **URL**: `/api/material-outbound-settings`
- **Method**: `GET`
- **说明**: 获取默认门店、默认仓库、可操作原材料、默认原材料、库存提示和备注标签

主要响应字段：

- `configured`: 是否已经完成触屏端配置
- `defaultStoreId`: 默认门店 ID
- `defaultWarehouseId`: 默认仓库 ID
- `allowedProductIds`: 触屏端可操作原材料 ID
- `defaultProductId`: 当前默认原材料 ID
- `showCurrentStock`: 是否在触屏端显示当前库存
- `allowInsufficientDraft`: 库存不足时是否仍允许提交草稿
- `deductionStrategy`: 库存扣减策略，当前固定为 `fifo`
- `remarkTags`: 常用备注标签

### 8.2 保存原材料出库触屏设置
- **URL**: `/api/material-outbound-settings`
- **Method**: `PUT`

```json
{
  "defaultStoreId": 2,
  "defaultWarehouseId": 1,
  "allowedProductIds": [3],
  "defaultProductId": 3,
  "showCurrentStock": true,
  "allowInsufficientDraft": true,
  "deductionStrategy": "fifo"
}
```

默认原材料必须包含在 `allowedProductIds` 中，仓库必须属于所选门店。

### 8.3 查询原材料出库单
- **URL**: `/api/material-outbounds`
- **Method**: `GET`
- **查询参数**:
  - `status`: `draft`、`reviewed` 或 `cancelled`
  - `startDate`: 开始日期
  - `endDate`: 结束日期
  - `limit`: 返回数量，最大 1000

每张单据包含门店、仓库、原材料快照、出库数量、成品数量、备注、录入人、审核人与审核时间。

### 8.4 员工提交原材料出库草稿
- **URL**: `/api/material-outbounds`
- **Method**: `POST`
- **说明**: 创建 `draft` 状态的出库单，不立即扣减库存

```json
{
  "productId": 3,
  "quantity": 50,
  "producedQuantity": 120,
  "remark": "粘钢胶"
}
```

门店和仓库以提交时的触屏设置为准，并保存名称快照。新备注会自动进入出库备注标签表。

### 8.5 审核原材料出库单
- **URL**: `/api/material-outbounds/<int:outbound_id>/audit`
- **Method**: `POST`
- **说明**: 在同一事务内校验实时库存、按 FIFO 扣减 `stock_balances`、写入 `stock_movements`，并将状态更新为 `reviewed`

库存不足时返回 `409`，单据继续保持草稿状态。

### 8.6 反审核原材料出库单
- **URL**: `/api/material-outbounds/<int:outbound_id>/audit`
- **Method**: `DELETE`
- **说明**: 按原出库流水回补对应批次和库位，并将状态恢复为 `draft`

### 8.7 作废、删除与重新启用

- `DELETE /api/material-outbounds/<int:outbound_id>`：首次调用将草稿置为 `cancelled`；对已作废单据再次调用会物理删除
- `POST /api/material-outbounds/<int:outbound_id>/restart`：将已作废单据恢复为 `draft`
- 已审核单据必须先反审核，不能直接作废或删除

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
- **操作人**: 从服务端 Session 获取；未登录时使用系统默认名称

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
- **操作人**: 从服务端 Session 获取；未登录时使用系统默认名称

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
- **操作人**: 从服务端 Session 获取；未登录时使用系统默认名称

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
- **说明**: 递归扫描当前系统配置的检测报告目录，将允许类型的文件同步到 `hr_reports` 数据表。扫描路径由 `reports.path` 系统设置决定；未设置时使用部署环境的默认目录。

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
- 每次调用同步接口时都会重新读取服务器中的路径配置，无需重启服务。
- 配置目录不存在、不是文件夹或当前后端进程没有读取权限时，同步失败并返回路径不可用信息。
- 修改检测报告根目录后，建议立即执行一次同步。旧目录对应的数据库记录会根据新目录的扫描结果清理。

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
- **上传人**: 从服务端 Session 获取；未登录时记录为 `unknown`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | 待上传文件 |
| `folder_path` | string | 否 | 目标文件夹相对路径，例如 `2026/09`，为空时上传到根目录 |

**请求示例**:
```bash
curl -X POST "http://localhost:5000/api/hr/reports/upload" `
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
| `uploader` | TEXT | 上传人，由服务端 Session 中的当前用户写入 |
| `share_token` | TEXT | 分享 Token |
| `share_expire` | TEXT | 分享过期时间 |
| `created_at` | TEXT | 创建时间 |
| `updated_at` | TEXT | 更新时间 |

文件根目录由系统设置键 `reports.path` 决定。未配置时：

- Docker/Linux 生产环境默认使用 `/app/uploads/hr_reports`。
- 本地开发环境默认使用项目根目录下的 `uploads/hr_reports`。

数据库中的 `file_path` 始终保存相对于当前报告根目录的路径，不保存 NAS 主机路径。上传、下载、预览、移动、重命名和删除操作都会在每次请求时读取当前配置，并限制文件操作不能越过报告根目录。

如需使用 NAS 目录，必须先将 NAS 主机目录挂载到 Docker 容器，再通过第 13 章的路径配置接口保存“容器内路径”。例如：

```yaml
volumes:
  - /vol2/1000/检测报告:/mnt/nas/reports
```

系统中应保存 `/mnt/nas/reports`，而不是主机侧的 `/vol2/1000/检测报告`。

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
- **说明**: 汇总已审核入库后的当前数量与库存金额，结果按物料类型、物料、仓库和门店分组

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
    "averageUnitCost": 12.3456,
    "inventoryAmount": 1215.04,
    "updatedAt": "2026-09-08 14:30:00"
  }
]
```

`averageUnitCost` 按同一物料、仓库、门店、货位和批次的有效入库流水进行加权计算，
`inventoryAmount` 为当前库存余额乘以对应加权入库单价后的汇总金额（不含税）。没有单价的历史余额按 `0` 计价。

### 11.11 获取库存流水

- **URL**: `/api/stock-movements`
- **Method**: `GET`
- **说明**: 查询已经实际影响库存的入库与出库流水。结果按来源单据、物料、门店和仓库聚合，并按流水时间倒序返回。草稿和已反审核单据不会出现在结果中。

**Query 参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `productId` | integer | 是 | 商品或原材料 ID |
| `type` | string | 否 | `raw-material` 或 `finished-product`，默认 `raw-material` |
| `storeId` | integer | 否 | 按门店 ID 筛选 |
| `warehouseId` | integer | 否 | 按仓库 ID 筛选 |
| `limit` | integer | 否 | 最大返回数量，默认 `200`，范围 `1-500` |

**请求示例**:

```http
GET /api/stock-movements?type=raw-material&productId=3&storeId=2&warehouseId=1&limit=200
```

**响应示例**:

```json
[
  {
    "movementType": "out",
    "receiptType": "raw-material",
    "sourceDocumentId": 5,
    "documentNo": "YLCK202609160005",
    "productType": "raw-material",
    "productId": 3,
    "warehouseId": 1,
    "storeId": 2,
    "quantity": 800.0,
    "unitPrice": null,
    "totalAmount": null,
    "createdAt": "2026-09-16 08:21:30",
    "documentDate": "2026-09-16",
    "storeName": "中固",
    "warehouseName": "中固车间",
    "remark": "灌缝胶",
    "producedQuantity": 800.0,
    "batchNos": "2026-09-09"
  },
  {
    "movementType": "in",
    "receiptType": "raw-material",
    "sourceDocumentId": 11,
    "documentNo": "RK20260909349",
    "productType": "raw-material",
    "productId": 3,
    "warehouseId": 1,
    "storeId": 2,
    "quantity": 200.0,
    "unitPrice": 15.0,
    "totalAmount": 3390.0,
    "createdAt": "2026-09-16 08:06:58",
    "documentDate": "2026-09-09",
    "storeName": "中固",
    "warehouseName": "中固车间",
    "remark": "",
    "producedQuantity": null,
    "batchNos": "2026-09-09"
  }
]
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `movementType` | string | `in` 入库，`out` 出库 |
| `documentNo` | string | 来源入库单或原材料出库单编号 |
| `quantity` | number | 本单实际入库或出库数量，始终返回正数，由 `movementType` 表示方向 |
| `remark` | string | 来源单据备注；出库取 `material_outbounds.remark`，入库取 `stock_inbounds.remark` |
| `producedQuantity` | number/null | 原材料出库单的成品数量；入库流水返回 `null` |
| `unitPrice` | number/null | 入库加权单价；出库流水返回 `null` |
| `totalAmount` | number/null | 入库金额合计；出库流水返回 `null` |
| `batchNos` | string | 本单涉及的库存批次，多个批次使用逗号连接 |

原材料库存明细页面将出库备注显示为 `remark · producedQuantity公斤`。由于 FIFO 出库可能从多个批次扣减，本接口会把同一出库单产生的多条批次流水聚合为一条，避免页面重复显示同一单据。

`productId` 缺失时返回 HTTP `400`；`type` 无效时同样返回 HTTP `400`。

### 11.12 审核规则与数据写入

调用 `POST /api/stock-inbounds/{id}/audit` 审核入库单后，后端在同一个 SQLite 事务中执行：

1. 写入或更新 `stock_inbounds` 单据头。
2. 写入 `stock_inbound_items` 入库明细。
3. 按物料、仓库、门店、货位和批次增量更新 `stock_balances`。
4. 为每条有效明细写入一条 `stock_movements` 库存流水。
5. 成品入库额外增量同步旧版 `inventory` 表，保证现有成品库存页面兼容。

原材料库存使用独立 `stock_balances` 余额，不写入旧的成品 `inventory` 表。待审核单据不会执行第 3 至第 5 步。

---

## 12. 收款单与应收核销

收款单采用“先保存、后审核”的单据模式。保存草稿只写入 `payment_receipts`，不会修改客户欠款和储值；审核时才在同一个 SQLite 事务中更新客户账户并写入可追溯流水。

### 12.1 获取收款单列表

- **URL**: `/api/payment-receipts`
- **Method**: `GET`
- **Query 参数**:
  - `storeId` - 可选，按门店 ID 筛选
  - `status` - 可选，`draft` 或 `audited`
  - `keyword` - 可选，匹配单据编号、客户、制单人或备注

**响应示例**:

```json
{
  "items": [
    {
      "id": 1,
      "documentNo": "SK20260910001",
      "documentDate": "2026-09-10",
      "storeId": 1,
      "storeName": "绝缘",
      "customerId": 2,
      "customerCode": "002",
      "customerName": "雷安电器",
      "settlementAccount": "绝缘结算账户",
      "paymentMethod": "银行转账",
      "paymentAmount": 2200.0,
      "discountAmount": 100.0,
      "totalAmount": 2300.0,
      "writeoffAmount": 2000.0,
      "advanceAmount": 300.0,
      "creator": "王醒",
      "remark": "",
      "attachmentUrl": "",
      "status": "audited",
      "auditedBy": "admin",
      "auditedAt": "2026-09-10T10:00:00"
    }
  ],
  "total": 1
}
```

### 12.2 获取下一收款单号

- **URL**: `/api/payment-receipts/next-number`
- **Method**: `GET`
- **Query 参数**:
  - `date` - 单据日期，格式 `YYYY-MM-DD`

单据编号格式为 `SK + YYYYMMDD + 三位流水号`。预览编号仅供录入界面展示，最终编号在保存事务内重新生成，防止并发重复。

### 12.3 上传收款附件

- **URL**: `/api/payment-receipts/attachments`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **文件字段**: `attachment`
- **限制**: 支持 JPG、JPEG、PNG、WebP、GIF，最大 10MB

接口把图片保存到 `uploads/payment-receipts/YYYY-MM/`，数据库仅保存返回的 `attachmentUrl`。

### 12.4 新增收款单草稿

- **URL**: `/api/payment-receipts`
- **Method**: `POST`

**请求示例**:

```json
{
  "documentDate": "2026-09-10",
  "customerId": 2,
  "paymentMethod": "银行转账",
  "paymentAmount": 2200,
  "discountAmount": 100,
  "creator": "王醒",
  "remark": "9月货款",
  "attachmentUrl": "/uploads/payment-receipts/2026-09/payment_xxx.jpg"
}
```

后端根据客户所属门店生成结算账户，并保存预计核销金额与预计预收金额。此时状态为 `draft`，客户的 `receivable` 和 `balance` 保持不变。

### 12.5 修改或删除草稿

- **修改 URL**: `/api/payment-receipts/<id>`
- **修改 Method**: `PUT`
- **删除 URL**: `/api/payment-receipts/<id>`
- **删除 Method**: `DELETE`

只有 `draft` 状态可以修改或删除。已审核单据必须先反审核；删除草稿时会同时清理该单据关联的附件图片。

### 12.6 审核收款单

- **URL**: `/api/payment-receipts/<id>/audit`
- **Method**: `POST`
- **操作人**: 从服务端 Session 获取当前用户姓名，作为审核人和账户流水操作人

审核时按客户实时账户计算：

1. 优惠金额先抵减客户应收欠款。
2. 实际收款再抵减剩余欠款。
3. 实际收款超过剩余欠款的部分计入 `advanceAmount`，增加客户 `balance` 储值。
4. 核销总额写入 `writeoffAmount`，客户 `receivable` 按该金额减少。
5. 写入一条 `customer_payment` 客户账户流水，并把流水 ID 回写收款单。

例如客户欠款 2000 元，收款 2200 元，优惠 100 元：核销欠款 2000 元，本次预收 300 元。

### 12.7 反审核收款单

- **URL**: `/api/payment-receipts/<id>/audit`
- **Method**: `DELETE`
- **操作人**: 从服务端 Session 获取当前用户姓名，作为反审核操作人

反审核会恢复本单核销的客户欠款，撤回本单产生的预收储值，将原入账流水标记为 `reversed`，并写入 `customer_payment_reverse` 反向流水。

如果本单产生的预收储值已经被后续订单使用，当前储值不足以撤回，接口返回 `409`，必须先处理后续关联业务，避免客户账户出现错误负数。

---

## 13. 退货单与客户应收、库存联动

退货单使用“保存草稿、审核入账”的状态模型。保存和修改只写入退货单及商品明细，不改变客户应收、客户储值或库存；审核时才在同一个 SQLite 事务中核销客户应收并返还库存。接口前缀为 `/api/returns`，成品和原材料通过 `productType` 区分。

### 13.1 状态与可执行操作

| 数据库状态 | 页面显示 | 客户流水/库存 | 可执行操作 |
| --- | --- | --- | --- |
| `draft` | 待审核 | 不影响 | 修改、审核、删除、查看 |
| `audited` | 已审核 | 已核销并返还库存 | 反审核、查看 |
| `completed` | 已审核（历史兼容） | 视历史数据而定 | 反审核、查看 |

已审核单据不能直接修改或删除，必须先反审核。反审核成功后单据恢复为 `draft`，客户应收和库存回到审核前状态。

### 13.2 获取退货单列表

- **URL**: `/api/returns`
- **Method**: `GET`
- **Query 参数**:
  - `storeId`：可选，按门店 ID 筛选
  - `customerId`：可选，按客户 ID 筛选
  - `status`：可选，按 `draft`、`audited` 或历史状态筛选

列表返回数组。每条记录包含 `returnNumber`、`originalOrderNumber`、`returnDate`、门店/客户信息、`totalQuantity`、`totalAmount`（实退货金额）、`refundAmount`、`writeoffAmount`、`status`、`remark` 等字段，并额外提供 `goodsName` 和 `units` 用于列表摘要。

### 13.3 获取退货单详情

- **URL**: `/api/returns/<id>`
- **Method**: `GET`

除列表字段外，详情响应包含 `items` 明细数组。明细字段包括 `productId`、`goodsName`、`specification`、`unit`、`warehouseId`、`packages`、`quantity`、`price`、`amount`、`taxRate`、`taxIncludedPrice`、`taxAmount`、`taxIncludedAmount` 和 `remark`。

### 13.4 新增退货单草稿

- **URL**: `/api/returns`
- **Method**: `POST`
- **响应状态**: `201`

**请求示例**:

```json
{
  "productType": "finished-product",
  "storeId": 1,
  "customerId": 2,
  "returnDate": "2026-09-14",
  "originalOrderNumber": "ZG20260912001",
  "taxEnabled": false,
  "returnAmount": 500,
  "refundAmount": 0,
  "settlementAccount": "绝缘结算账户",
  "salesPerson": "王醒",
  "creator": "制单员",
  "packaging": "无",
  "remark": "包装破损",
  "items": [
    {
      "productId": 1,
      "productCode": "DA-Z",
      "goodsName": "粘钢胶",
      "specification": "40kg/组",
      "unit": "组",
      "warehouseId": 2,
      "packages": 1,
      "quantity": 1,
      "price": 500,
      "amount": 500,
      "taxRate": 0,
      "taxIncludedPrice": 0,
      "remark": ""
    }
  ]
}
```

`productType` 只能是 `finished-product` 或 `raw-material`。`returnAmount` 为实退货金额，未传或小于等于零时按明细金额合计；`refundAmount` 为本次实际退款，必须满足 `0 <= refundAmount <= returnAmount`。保存成功后返回 `returnId`、`returnNumber` 和 `returnOrder`，状态为 `draft`。此时不会写入客户账户流水，也不会增加库存。

**成功响应示例**:

```json
{
  "success": true,
  "message": "退货单草稿保存成功，请审核后计入客户流水和库存",
  "returnId": 12,
  "returnNumber": "TH202609140001",
  "returnOrder": {
    "id": 12,
    "returnNumber": "TH202609140001",
    "storeId": 1,
    "customerId": 2,
    "productType": "finished-product",
    "totalQuantity": 1,
    "totalAmount": 500.0,
    "refundAmount": 0.0,
    "writeoffAmount": 500.0,
    "status": "draft",
    "accountTransactionId": null
  }
}
```

### 13.5 修改退货单草稿

- **URL**: `/api/returns/<id>`
- **Method**: `PUT`

请求结构与新增接口相同。只有 `draft`（以及未入账的历史待处理状态）可以修改；后端会替换单据头和全部明细，保留原退货单号。已审核单据返回 `409`，需先调用反审核接口。

### 13.6 审核退货单

- **URL**: `/api/returns/<id>/audit`
- **Method**: `POST`
- **操作人**: 从服务端 Session 获取当前用户姓名，作为客户流水操作人

审核在一个数据库事务中完成：

1. 校验门店、客户归属和实退金额；实退金额不能超过客户当前应收欠款。
2. 按每条明细的门店、仓库、商品和数量增加 `stock_balances`，并写入 `stock_movements` 入库流水；成品同时兼容更新旧版 `inventory` 表。
3. 客户 `receivable` 减少 `returnAmount`；`refundAmount` 作为实际退款，差额写入 `writeoffAmount`。
4. 写入一条 `customer_return` 客户账户流水，并把流水 ID 写回退货单。
5. 单据状态更新为 `audited`，记录 `debtBefore` 和 `debtAfter`。

例如客户当前应收 5000 元，实退金额 500 元、本次退款 0 元：审核后客户应收为 4500 元，500 元全部作为核销金额；不会产生现金退款。

### 13.7 反审核退货单

- **URL**: `/api/returns/<id>/reverse-audit`
- **Method**: `POST`

仅 `audited` 或历史 `completed` 且存在有效客户流水的单据可以反审核。接口会删除本单库存流水、扣回本单返还的库存、恢复客户 `receivable`，并将原客户流水标记为 `reversed`；单据恢复为 `draft`。如果库存不足或审核流水不存在，返回 `409`，不会提交部分变更。

### 13.8 删除退货单草稿

- **URL**: `/api/returns/<id>`
- **Method**: `DELETE`

只有未审核草稿可以删除。删除会同时删除退货商品明细，不会操作客户应收或库存。已审核单据返回 `409`，必须先反审核。

### 13.9 退货单错误响应

```json
{
  "success": false,
  "message": "已审核单据不能修改，请先反审核"
}
```

常见状态码：`400` 参数或业务校验失败，`404` 单据不存在，`409` 状态冲突、客户欠款不足、库存不足或无法反审核，`500` 服务端异常。

---

## 14. 银行账户与结算账户

银行账户数据保存在 `bank_accounts` 表中，按门店维护。订单、收款单和退货单保存时会优先使用所选门店下的真实账户名称；没有配置账户时继续兼容历史的“门店结算账户”文字。

### 14.1 获取银行账户列表

- **URL**: `/api/bank-accounts`
- **Method**: `GET`
- **Query 参数**: `storeId`（可选，按门店筛选）

响应同时提供 `data`、`items` 字段，便于列表页和下拉框使用：

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "storeId": 1,
      "storeName": "总店",
      "accountName": "深圳某某科技有限公司",
      "accountNumber": "6222021234567890123",
      "bankName": "中国工商银行深圳分行",
      "bankCode": "102584000012",
      "balance": 125680.5,
      "isDefault": true,
      "cardColor": "#1a1a1a",
      "cardBgImage": "/uploads/bank-cards/backgrounds/bank_card_bg_20260914120000_x.jpg",
      "bankIcon": "/uploads/bank-cards/icons/bank_icon_20260914120000_x.png",
      "createdAt": "2026-09-14T12:00:00",
      "updatedAt": "2026-09-14T12:00:00"
    }
  ],
  "total": 1
}
```

### 14.2 获取结算账户下拉选项

- **URL**: `/api/bank-accounts/options`
- **Method**: `GET`
- **Query 参数**: `storeId`（可选）

返回精简字段 `id`、`storeId`、`accountName`、`accountNumber`、`bankName`、`label` 和 `value`。订单、收款单和退货单页面按门店过滤此列表，`value` 默认是账户名称。

### 14.3 新增银行账户

- **URL**: `/api/bank-accounts`
- **Method**: `POST`
- **响应状态**: `201`

必填字段为 `storeId`、`accountName`、`accountNumber` 和 `bankName`。可选字段包括 `bankCode`、`balance`、`cardColor`、`cardBgImage` 和 `bankIcon`。同一门店下银行账号不能重复。

```json
{
  "storeId": 1,
  "accountName": "深圳某某科技有限公司",
  "accountNumber": "6222021234567890123",
  "bankName": "中国工商银行深圳分行",
  "bankCode": "102584000012",
  "balance": 0,
  "cardColor": "#1a1a1a",
  "cardBgImage": "",
  "bankIcon": "",
  "isDefault": true
}
```

### 14.4 修改和删除银行账户

- **修改**：`PUT /api/bank-accounts/<id>`，请求字段与新增相同，未传字段沿用原值。
- **删除**：`DELETE /api/bank-accounts/<id>`。

已被订单、收款单或退货单的 `settlement_account` 使用的账户不能删除，接口返回 `409`。修改或删除账户时，系统会清理不再使用的本系统银行卡图片文件；外部 URL 和历史自由文本不会被删除。

### 14.5 上传银行卡背景图

- **URL**: `/api/upload/bank-card-background`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **字段**: `file`（兼容 `image` 字段）
- **限制**: 仅支持 JPG、PNG、WEBP、GIF，建议不超过 5 MB

文件保存到系统设置 `bank_cards.bg_path` 指定的目录，返回的路径保存到 `bank_accounts.card_bg_image`：

```json
{
  "success": true,
  "message": "图片上传成功",
  "data": {
    "path": "/uploads/bank-cards/backgrounds/bank_card_bg_20260914120000_x.jpg",
    "url": "/uploads/bank-cards/backgrounds/bank_card_bg_20260914120000_x.jpg"
  }
}
```

### 14.6 上传银行图标

- **URL**: `/api/upload/bank-icon`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **字段**: `file`（兼容 `image` 字段）
- **限制**: 仅支持 JPG、PNG、WEBP、GIF，建议不超过 2 MB

文件保存到 `bank_cards.icon_path` 指定的目录，返回格式与背景图上传一致，访问前缀为 `/uploads/bank-cards/icons/`。

### 14.7 账户余额与业务单据

`balance` 使用两位小数保存账户余额。审核业务单据时才产生余额变化，草稿保存和修改不改变账户余额：

| 业务动作 | 账户余额变化 |
| --- | --- |
| 销售订单审核，存在本次收款 | 增加 `currentPayment` |
| 收款单审核 | 增加 `paymentAmount` |
| 收款单反审核 | 减少原 `paymentAmount` |
| 退货单审核 | 减少 `refundAmount`，实退金额核销不产生现金变化 |
| 退货单反审核 | 加回原 `refundAmount` |

例如客户应收 5000 元，退货实退金额 500 元、本次退款 0 元：客户应收核销为 4500 元，银行账户余额不变化。

---

## 15. 系统设置与服务器路径

模块前缀：`/api/settings`

系统路径配置保存在 SQLite 的 `system_settings` 表中。检测报告模块使用键 `reports.path` 保存报告根目录；银行卡背景图和银行图标分别使用 `bank_cards.bg_path`、`bank_cards.icon_path`。相关上传和静态访问接口都会在请求时读取这些配置。

### 15.1 获取路径配置

- **URL**: `/api/settings/paths`
- **Method**: `GET`
- **说明**: 获取当前检测报告、公司资料、回单上传路径以及银行卡背景图和银行图标上传路径。

**响应示例**:

```json
{
  "success": true,
  "data": {
    "reportPath": "/mnt/nas/reports",
    "documentPath": "/var/data/documents",
    "receiptPath": "/var/data/receipts",
    "bankCardBgPath": "/app/uploads/bank-cards/backgrounds",
    "bankIconPath": "/app/uploads/bank-cards/icons",
    "reportPathConfigured": true,
    "reportPathDefault": "/app/uploads/hr_reports",
    "reportStatus": {
      "path": "/mnt/nas/reports",
      "exists": true,
      "is_directory": true,
      "readable": true,
      "writable": true,
      "message": "路径可用"
    }
  }
}
```

`reportPathConfigured` 为 `false` 时，表示尚未保存自定义路径，当前使用 `reportPathDefault`。

### 15.2 保存路径配置

- **URL**: `/api/settings/paths`
- **Method**: `PUT`
- **Content-Type**: `application/json`
- **说明**: 保存系统路径配置。`reportPath` 必须是后端服务器可访问的已存在文件夹，并且至少具有读取权限。

**请求示例**:

```json
{
  "reportPath": "/mnt/nas/reports",
  "documentPath": "/var/data/documents",
  "receiptPath": "/var/data/receipts",
  "bankCardBgPath": "/app/uploads/bank-cards/backgrounds",
  "bankIconPath": "/app/uploads/bank-cards/icons"
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "路径配置已保存",
  "data": {
    "reportPath": "/mnt/nas/reports",
    "documentPath": "/var/data/documents",
    "receiptPath": "/var/data/receipts",
    "bankCardBgPath": "/app/uploads/bank-cards/backgrounds",
    "bankIconPath": "/app/uploads/bank-cards/icons",
    "bankCardBgStatus": {
      "path": "/app/uploads/bank-cards/backgrounds",
      "exists": true,
      "is_directory": true,
      "readable": true,
      "writable": true,
      "message": "路径可用"
    },
    "bankIconStatus": {
      "path": "/app/uploads/bank-cards/icons",
      "exists": true,
      "is_directory": true,
      "readable": true,
      "writable": true,
      "message": "路径可用"
    },
    "reportStatus": {
      "path": "/mnt/nas/reports",
      "exists": true,
      "is_directory": true,
      "readable": true,
      "writable": true,
      "message": "路径可用"
    }
  }
}
```

`bankCardBgPath` 和 `bankIconPath` 保存时会自动创建目录并检查读写权限；路径不可用返回 HTTP `400`。将 `reportPath` 传为空字符串会清除自定义配置，恢复使用部署环境默认路径。

### 15.3 测试服务器路径

- **URL**: `/api/settings/paths/test`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **说明**: 只检查路径，不修改系统配置。

**请求示例**:

```json
{
  "path": "/mnt/nas/reports"
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "路径可用",
  "data": {
    "path": "/mnt/nas/reports",
    "exists": true,
    "is_directory": true,
    "readable": true,
    "writable": true,
    "message": "路径可用"
  }
}
```

### 15.4 浏览服务器目录

- **URL**: `/api/settings/directories`
- **Method**: `GET`
- **说明**: 返回后端进程可以读取的服务器目录，用于系统设置页的“获取文件夹”功能。此接口浏览的是 Docker 容器内路径，不是访问者电脑的本地路径。

首次打开时不带查询参数，返回由 `REPORTS_BROWSE_ROOTS` 环境变量配置的可浏览根目录：

```text
GET /api/settings/directories
```

浏览某个目录时传入 `path`：

```text
GET /api/settings/directories?path=/mnt/nas
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "path": "/mnt/nas",
    "parent_path": "/mnt",
    "directories": [
      {
        "name": "reports",
        "path": "/mnt/nas/reports"
      }
    ],
    "message": "读取成功"
  }
}
```

如果 NAS 挂载点不在目录浏览器的初始根目录中，仍可在弹窗中直接输入容器内绝对路径，然后点击“打开”或使用“测试路径”按钮确认。

### 15.5 NAS/Docker 路径配置规则

NAS 主机目录必须先挂载到后端容器，应用只能使用容器内可见的路径。例如：

```yaml
services:
  order-board:
    volumes:
      - /vol2/1000/检测报告:/mnt/nas/reports
```

挂载完成并重启容器后，在系统设置中保存：

```text
/mnt/nas/reports
```

不能直接保存 NAS 主机侧的 `/vol2/1000/检测报告`，除非该路径本身也是后端运行环境可见的路径。挂载目录需要根据实际功能授予权限：

- 只扫描和预览：后端进程需要读取权限；
- 上传、移动、重命名和删除：后端进程还需要写入权限；
- 修改路径后建议立即调用 `POST /api/hr/reports/sync`，让 `hr_reports` 表与新目录内容同步。

---

## 16. 打印模板管理

模块前缀：`/api/print-templates`

打印模板的名称、业务类型、纸张尺寸、默认状态、启用状态和设计器 JSON 保存在 SQLite 的 `print_templates` 表中。浏览器打印或 C-Lodop 的协议、主机、端口和本地打印机名称不通过本模块上传，它们只保存在每台客户端浏览器的 `localStorage`。

前端调用文件：

```text
src/api/printTemplate.js
```

后端路由文件：

```text
backend/routes/print_templates.py
```

完整的设计器、变量渲染和打印流程见：

```text
docs/打印机项目实现.md
```

### 16.1 模板字段

数据库和 GET 接口响应使用下划线字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 模板主键 |
| `name` | string | 模板名称 |
| `business_type` | string | 业务类型，例如 `sale`、`purchase` |
| `paper_type` | string/null | 纸张名称，例如三联单、A4、自定义 |
| `page_width` | number | 纸张宽度，单位 mm |
| `page_height` | number | 纸张高度，单位 mm |
| `is_default` | integer | `1` 为默认模板，`0` 为非默认模板 |
| `enabled` | integer | `1` 为启用，`0` 为停用 |
| `content` | object/null | `vue-print-designer` 设计 JSON |
| `created_at` | string | 创建时间 |
| `updated_at` | string/null | 最后更新时间 |

创建和更新请求使用驼峰字段：

| 请求字段 | 响应/数据库字段 |
| --- | --- |
| `businessType` | `business_type` |
| `paperType` | `paper_type` |
| `pageWidth` | `page_width` |
| `pageHeight` | `page_height` |
| `isDefault` | `is_default` |
| `createdAt` | `created_at` |
| `updatedAt` | `updated_at` |

前端 `normalizePrintTemplate()` 会把 GET 响应转换为驼峰字段，并把 `is_default`、`enabled` 转换为 boolean。直接调用 HTTP 接口的客户端必须自行处理这种字段差异。

当前设计器支持以下业务类型：

| 值 | 名称 |
| --- | --- |
| `sale` | 销售 |
| `purchase` | 采购 |
| `return` | 退货 |
| `transfer` | 调拨 |
| `inventory` | 盘点 |
| `receipt` | 收款 |
| `payment` | 付款 |

后端当前没有对 `businessType` 做固定枚举校验，只要求创建时该字段非空。

`content` 典型结构：

```json
{
  "canvasSize": {
    "width": 794,
    "height": 529
  },
  "pages": [
    {
      "id": "sale-page",
      "elements": []
    }
  ],
  "unit": "mm",
  "testData": {},
  "ext": {
    "availableVariables": []
  }
}
```

`content` 在 SQLite 中以 JSON 字符串保存，读取接口会在返回前解析成对象。解析失败时接口将该字段返回为 `null`。

### 16.2 获取模板列表

- **URL**: `/api/print-templates`
- **Method**: `GET`
- **说明**: 获取全部模板，可按业务类型和启用状态筛选

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `businessType` | string | 否 | 空 | 按业务类型过滤 |
| `enabledOnly` | string/boolean | 否 | `false` | 值转成小写后等于 `true` 时只返回启用模板 |

**请求示例**:

```text
GET /api/print-templates?businessType=sale&enabledOnly=true
```

**响应示例**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "销售出库单",
      "business_type": "sale",
      "paper_type": "三联单",
      "page_width": 210,
      "page_height": 140,
      "is_default": 1,
      "enabled": 1,
      "content": {
        "canvasSize": {
          "width": 794,
          "height": 529
        },
        "pages": [],
        "unit": "mm"
      },
      "created_at": "2026-09-17 09:00:00",
      "updated_at": "2026-09-17 10:00:00"
    }
  ]
}
```

排序规则：

1. `is_default DESC`，默认模板在前。
2. `created_at DESC`，同级模板按创建时间倒序。

接口当前不分页。

### 16.3 获取单个模板

- **URL**: `/api/print-templates/{id}`
- **Method**: `GET`
- **说明**: 按模板 ID 获取完整记录和设计 JSON

**响应示例**:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "销售出库单",
    "business_type": "sale",
    "paper_type": "三联单",
    "page_width": 210,
    "page_height": 140,
    "is_default": 1,
    "enabled": 1,
    "content": {
      "canvasSize": {
        "width": 794,
        "height": 529
      },
      "pages": [],
      "unit": "mm"
    },
    "created_at": "2026-09-17 09:00:00",
    "updated_at": "2026-09-17 10:00:00"
  }
}
```

模板不存在时返回 HTTP `404`：

```json
{
  "success": false,
  "message": "模板不存在"
}
```

### 16.4 创建模板

- **URL**: `/api/print-templates`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **说明**: 创建模板记录并保存设计器 JSON

**请求参数**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `name` | string | 是 | - | 模板名称 |
| `businessType` | string | 是 | - | 业务类型 |
| `paperType` | string | 否 | 空字符串 | 纸张名称 |
| `pageWidth` | number | 是 | - | 纸张宽度，单位 mm |
| `pageHeight` | number | 是 | - | 纸张高度，单位 mm |
| `isDefault` | boolean | 否 | `false` | 是否设为当前业务类型默认模板 |
| `enabled` | boolean | 否 | `true` | 是否启用 |
| `content` | object/null | 否 | `null` | 设计器 JSON |

**请求示例**:

```json
{
  "name": "销售出库单",
  "businessType": "sale",
  "paperType": "三联单",
  "pageWidth": 210,
  "pageHeight": 140,
  "isDefault": true,
  "enabled": true,
  "content": {
    "canvasSize": {
      "width": 794,
      "height": 529
    },
    "pages": [],
    "unit": "mm",
    "testData": {},
    "ext": {
      "availableVariables": []
    }
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 1
  }
}
```

当 `isDefault=true` 时，后端会先把同一 `business_type` 下的其他模板更新为非默认，再插入新模板。

缺少必填字段时返回 HTTP `400`：

```json
{
  "success": false,
  "message": "缺少必填字段: pageWidth"
}
```

### 16.5 更新模板

- **URL**: `/api/print-templates/{id}`
- **Method**: `PUT`
- **Content-Type**: `application/json`
- **说明**: 部分更新模板元数据或设计内容

支持更新：

```text
name
businessType
paperType
pageWidth
pageHeight
isDefault
enabled
content
```

**请求示例**:

```json
{
  "name": "销售出库单 A4",
  "businessType": "sale",
  "paperType": "A4",
  "pageWidth": 210,
  "pageHeight": 297,
  "enabled": true,
  "content": {
    "canvasSize": {
      "width": 794,
      "height": 1123
    },
    "pages": [],
    "unit": "mm"
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "更新成功"
}
```

更新时后端会自动写入 `updated_at`。

提交 `isDefault=true` 时：

1. 优先使用请求中的 `businessType`。
2. 请求未传 `businessType` 时读取模板当前业务类型。
3. 取消同业务类型其他模板的默认状态。
4. 将当前模板设置为默认。

提交 `"content": null` 会清空当前设计内容。

### 16.6 删除模板

- **URL**: `/api/print-templates/{id}`
- **Method**: `DELETE`
- **说明**: 删除非默认模板

**成功响应**:

```json
{
  "success": true,
  "message": "删除成功"
}
```

默认模板不允许直接删除，返回 HTTP `400`：

```json
{
  "success": false,
  "message": "不能删除默认模板，请先设置其他模板为默认"
}
```

模板不存在时返回 HTTP `404`。

### 16.7 设置默认模板

- **URL**: `/api/print-templates/{id}/set-default`
- **Method**: `POST`
- **说明**: 将模板设为所属业务类型的默认模板

无需请求体。

后端在同一数据库连接中执行：

1. 查询当前模板的 `business_type`。
2. 取消该业务类型下所有模板的默认状态。
3. 将当前模板的 `is_default` 更新为 `1`。

**响应示例**:

```json
{
  "success": true,
  "message": "设置成功"
}
```

同一业务类型“只保留一个默认模板”由接口事务逻辑保证，数据库当前没有建立部分唯一索引。

### 16.8 迁移旧 localStorage 模板

- **URL**: `/api/print-templates/migrate`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **说明**: 将旧版浏览器 localStorage 模板批量迁移到 SQLite

**请求示例**:

```json
{
  "templates": [
    {
      "name": "旧销售模板",
      "businessType": "sale",
      "paperType": "三联单",
      "pageWidth": 210,
      "pageHeight": 140,
      "isDefault": false,
      "enabled": true,
      "content": {
        "pages": []
      }
    }
  ]
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "成功迁移 1 个模板",
  "data": {
    "migratedCount": 1
  }
}
```

迁移规则：

- `templates` 必须是非空数组。
- 以 `name + businessType` 判断是否已经存在。
- 已存在的模板直接跳过。
- 单条模板迁移失败时记录后继续处理后续模板。
- `isDefault=true` 时会取消同业务类型原默认模板。

模板管理页仅在服务器模板列表为空时尝试调用迁移接口。该接口用于历史数据迁移，不用于保存 C-Lodop 打印机配置。

### 16.9 数据库表结构

```sql
CREATE TABLE print_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    business_type TEXT NOT NULL,
    paper_type TEXT,
    page_width INTEGER NOT NULL,
    page_height INTEGER NOT NULL,
    is_default INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1,
    content TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);
```

索引：

```sql
CREATE INDEX idx_print_templates_business_type
ON print_templates(business_type);

CREATE INDEX idx_print_templates_is_default
ON print_templates(is_default);
```

`backend/utils/db.py` 在首次数据库连接时检查并创建该表。仅在表不存在时插入三条基础记录：

```text
销售出库单-标准模板 / sale
采购入库单-标准模板 / purchase
退货单-标准模板 / return
```

当前初始化数据的 `paper_type` 为“二等分”，宽高为 `210 × 140mm`；设计器中的二等分预设为 `241 × 140mm`。历史项目以模板最终保存的宽高为准，新项目应统一初始化名称和尺寸。

### 16.10 本地打印配置不属于后端接口

以下设置不会写入 `print_templates`：

```text
打印方式 browser/clodop
C-Lodop 协议
C-Lodop 主机
C-Lodop 端口
本地打印机名称
```

前端存储键：

```text
order-system-print-client-config
```

默认配置：

```json
{
  "version": 1,
  "mode": "clodop",
  "protocol": "http",
  "host": "localhost",
  "port": 8000,
  "printerName": ""
}
```

HTTPS 页面默认使用端口 `8443`。环境变量 `VITE_CLODOP_URL` 可以覆盖默认协议、主机和端口。

这种拆分保证模板可以在系统用户之间共享，同时每台电脑可以选择自己的 C-Lodop 服务和物理打印机。

### 16.11 接口约束与状态码

| 场景 | HTTP 状态码 |
| --- | --- |
| 查询、创建、更新、删除或设置成功 | `200` |
| 缺少创建必填字段 | `400` |
| 迁移数据不是非空数组 | `400` |
| 删除默认模板 | `400` |
| 模板不存在 | `404` |
| 数据库或 JSON 处理异常 | `500` |

当前打印模板路由尚未接入服务端管理员权限守卫，主要依赖后台入口限制。对外部署或多人环境中，应继续补充后端权限校验；客户端身份请求头不能作为替代方案。

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
- `stores` - 门店表（3条记录）
- `warehouses` - 仓库表（4条记录）
- `users` - 用户表（9条记录）
- `suppliers` - 供应商基础资料表
- `stock_inbounds` - 入库单头与状态、汇总信息表
- `stock_inbound_items` - 入库单明细表
- `material_outbound_settings` - 员工触屏端默认门店、仓库和原材料配置
- `material_outbounds` - 原材料出库单头、状态、录入和审核快照
- `material_outbound_items` - 原材料出库明细
- `material_remark_tags` - 新原材料出库流程的常用备注标签
- `stock_balances` - 按物料、仓库、门店、货位和批次保存的库存余额表
- `stock_movements` - 入库与出库过账库存流水表
- `payment_receipts` - 收款单草稿、审核状态、核销和预收快照表
- `customer_account_transactions` - 订单审核、收款、反审核的客户账户流水表
- `system_settings` - 系统键值配置表，包括检测报告根目录 `reports.path`
- `print_templates` - 打印模板元数据、纸张尺寸和设计器 JSON

**辅助表**:
- `units` - 计量单位和包装表，通过 `unit_type` 分组
- `attributes` - 商品属性表
- `attribute_options` - 属性选项表
- `warehouse_categories` - 仓库分类表
- `carrier_tags` - 物流公司标签表
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

-- 打印模板按业务类型和默认状态查询
CREATE INDEX idx_print_templates_business_type
ON print_templates(business_type);
CREATE INDEX idx_print_templates_is_default
ON print_templates(is_default);
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
| stores_db.json | stores | 3 |
| warehouses_db.json | warehouses, warehouse_categories | 4 + N |
| users_db.json | 不再迁移 | v4.0 已清空旧用户数据，首次启动后由管理员初始化 |

原材料商品档案 `raw_material_products` 是新增的独立表，没有对应的历史 JSON 迁移来源；新建或编辑后直接通过
`/api/raw-material-products` 持久化到 SQLite。

旧版 `materials_db.json`、`material_records`、`remark_tags` 和 `/api/materials` 已于 2026-09-16 下线；
当前原材料业务只使用商品档案、入库单、原材料出库单、库存余额、库存流水和 `material_remark_tags`。

供应商、入库单、明细、库存余额和库存流水表由 `backend/utils/db.py` 在首次数据库连接时自动创建，
没有对应的历史 JSON 迁移来源。

打印模板原本保存在浏览器 localStorage。当前模板以 `print_templates` 表为准，旧模板可以通过
`POST /api/print-templates/migrate` 一次性迁移；C-Lodop 地址和打印机名称仍只保存在客户端。

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

订单业务状态 `status` 与审核状态 `audit_state` 相互独立。销售订单完成后可进入
物流流程，发货后状态为 `shipped`；财务审核成功后 `audit_state=1`，页面显示
“已过账”，但 `status` 仍保持 `shipped`。

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

### v4.0.0 (2026-09-18)
- 新增首次超级管理员初始化，依据有效全权限账号是否存在决定入口是否开放
- 登录改为服务端 Session Cookie，停用客户端 `Username`、`Role` 身份请求头
- 密码改为安全哈希，旧用户表和明文用户备份不再保留
- 新增员工档案、账号、权限组、权限目录及其关联接口
- 触屏端订单、回单和原材料出库接口增加服务端权限校验

### v3.4.0 (2026-09-17)
- 新增 `print_templates` SQLite 数据表及业务类型、默认状态索引
- 新增打印模板列表、详情、创建、更新、删除和设为默认接口
- 新增旧 localStorage 模板批量迁移接口
- 补充模板字段、设计器 JSON 和客户端 C-Lodop 配置边界

### v3.1.0 (2026-09-16)
- 补充销售订单审核与反审核请求、响应、账务联动和错误状态码
- 审核人姓名解析逻辑已在 v4.0 改为读取服务端 Session
- 新增 `audit_state`、`audit_by`、`audit_date` 等字段说明
- 旧数据库启动时自动补齐审核字段，并兼容转换历史账号值

### v2.4.0 (2026-09-10)
- ✅ 新增收款历史列表、门店滑块、Excel 导出和收款单打印
- ✅ 新增收款单草稿、附件、修改、删除、审核与反审核接口
- ✅ 审核时自动核销客户应收，多收金额转为储值预收
- ✅ 反审核按原流水恢复客户应收和储值，并防止撤回已被使用的预收
- ✅ 应收欠款汇总联动收回欠款与优惠金额

### v2.5.0 (2026-09-11)
- ✅ 新增系统路径配置、服务器目录浏览和路径测试接口
- ✅ 人事检测报告扫描、上传、下载、移动和删除支持自定义服务器/NAS 路径
- ✅ 补充 Docker NAS 挂载与容器内路径使用说明

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
默认账户规则：`isDefault` 表示门店默认结算账户。每个门店最多一个默认账户，新增或修改时提交 `isDefault: true` 会在同一事务内取消旧默认标记；接口按默认账户优先返回。订单录入、收款历史和退货单录入选择门店后会自动带出默认账户，没有默认账户时回退到该门店第一条账户。
