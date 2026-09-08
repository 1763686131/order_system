# 订单管理系统

基于 Vue 3 + Vite + Flask + SQLite 的物流订单管理系统，支持订单全生命周期管理、商品与原材料档案、库存管理、回单管理、运费对账和智能订单解析。

## ✨ 主要特性

- 🎯 **完整订单流转** - 未完成 → 已完成 → 已出库全流程管理
- 📸 **回单智能管理** - 图片上传、在线预览、旋转编辑、大图查看
- 💰 **运费对账系统** - 物流/快递运费对账、备用金管理、Excel导出
- 📦 **商品档案管理** - 成品商品与原材料商品分开管理，共用商品录入弹窗
- 📊 **原材料业务数据** - 使用/生产时间线、日期筛选、快捷词库、行内编辑
- 📋 **库存管理** - 成品库存与原材料库存独立展示，支持筛选、分页和调整
- 🔍 **全局搜索** - 支持运单号、收货人、电话、地址多维度搜索
- 🤖 **智能解析** - 粘贴文本自动识别填充订单信息
- 🧮 **智能计算器** - 内置重量计算器，支持复杂算术表达式
- 🎨 **NomiAI 助手** - 浮动智能助手，快捷操作导航
- 🔐 **权限管理** - 细粒度权限控制，支持多角色管理

## 🚀 快速开始

### 环境要求

- Node.js >= 20.19.0
- Python >= 3.8 (后端)
- Docker (可选，用于容器化部署)

### 安装依赖

```bash
# 前端依赖
npm install

# 后端依赖
pip install -r backend/requirements.txt
```

### 启动项目

**方式1：本地开发**

```bash
# 启动后端服务（端口 7899）
python backend/app.py

# 启动前端开发服务器（端口 3000）
npm run dev
```

**方式2：Docker 部署**

```bash
# Windows 环境
cd backend
.\start.bat

# 访问服务
http://localhost:7899
```

访问 http://localhost:3000 (开发环境) 或 http://localhost:7899 (Docker)

### 生产构建

```bash
# 构建前端静态文件
npm run build

# 预览构建结果
npm run preview
```

## 📁 项目结构

```
order_system/
├── backend/                          # 后端服务
│   ├── app.py                        # Flask 主应用和蓝图注册
│   ├── routes/                       # API 路由
│   │   ├── products.py               # 成品、单位、属性和成品库存接口
│   │   ├── raw_material_products.py  # 原材料商品档案接口
│   │   ├── materials.py              # 原材料使用/生产流水接口
│   │   └── orders.py                 # 订单接口
│   ├── utils/                        # SQLite 连接和数据读写
│   ├── start.bat                     # Docker 启动脚本（自动检测路径）
│   ├── Dockerfile                    # Docker 镜像配置
│   └── requirements.txt              # Python 依赖
│
├── src/                              # 前端源码
│   ├── main.js                       # 应用入口
│   ├── App.vue                       # 根组件
│   │
│   ├── router/                       # 路由配置
│   │   └── index.js                  # Vue Router 配置
│   │
│   ├── stores/                       # 状态管理 (Pinia)
│   │   ├── user.js                   # 用户状态（登录、权限、用户管理）
│   │   ├── order.js                  # 订单状态（CRUD、流转）
│   │   ├── material.js               # 原材料状态
│   │   └── nomi.js                   # NomiAI 助手状态
│   │
│   ├── views/                        # 页面组件
│   │   ├── LoginView.vue             # 登录页
│   │   ├── MainView.vue              # 主界面（Tab导航容器）
│   │   │
│   │   ├── Admin.vue                 # 管理后台容器、侧边菜单和顶部导航
│   │   ├── front/                    # 前台业务页面
│   │   │   ├── OrderList.vue         # 订单列表（未完成+已完成）
│   │   │   ├── ShippedOrderList.vue  # 已出库订单
│   │   │   └── MaterialDisplay.vue   # 原材料使用/生产数据展示
│   │   │
│   │   └── admin/                    # 后台管理页面
│   │       ├── Dashboard.vue         # 管理后台首页
│   │       ├── products/             # 商品与库存管理
│   │       │   ├── ProductList.vue          # 成品商品列表
│   │       │   ├── MaterialProductList.vue  # 原材料商品档案列表
│   │       │   ├── InventoryList.vue        # 成品库存
│   │       │   └── MaterialInventory.vue    # 原材料库存
│   │       ├── orders/               # 订单管理模块
│   │       │   ├── OrderForm.vue            # 新增/修改订单
│   │       │   └── UnifiedOrderList.vue     # 统一订单列表
│   │       ├── system/               # 用户、角色、门店管理
│   │       ├── finance/              # 财务与运费对账
│   │       └── hr/                   # 人事报告
│   │
│   ├── components/                   # 组件库
│   │   ├── common/                   # 公共组件
│   │   │   ├── ConfirmModal.vue              # 确认对话框
│   │   │   ├── SearchOrderModal.vue          # 全局搜索
│   │   │   ├── ShippedOrderActionModal.vue   # 已出库订单操作
│   │   │   ├── SmartCalculator.vue           # 智能计算器
│   │   │   └── NomiFloatingAI.vue            # NomiAI 浮动助手
│   │   │
│   │   ├── admin/                    # 后台公共组件
│   │   │   ├── ProductFormModal.vue  # 成品/原材料共用商品录入弹窗
│   │   │   └── StoreFormModal.vue    # 门店录入弹窗
│   │   │
│   │   └── front/                    # 前台专用组件
│   │       ├── OrderFormModal.vue    # 订单表单（新增/编辑）
│   │       ├── ShipOrderModal.vue    # 发货出库弹窗
│   │       └── UploadMaterialModal.vue  # 原材料录入
│   │
│   ├── api/                          # API 封装
│   │   └── request.js                # Axios 统一请求（拦截器、认证）
│   │
│   ├── utils/                        # 工具函数
│   │   ├── tools.js                  # 通用工具集
│   │   ├── constants.js              # 常量定义
│   │   └── helpers.js                # 辅助函数
│   │
│   └── assets/                       # 静态资源
│       └── styles/
│           └── main.css              # 全局样式
│
├── data/                             # SQLite 数据库与历史备份
│   ├── order_system.db               # 当前业务数据库
│   └── backup_before_cleanup/        # 历史 JSON 备份
│
├── uploads/                          # 上传文件
│   └── receipts/                     # 回单图片存储
│
├── frontend old/                     # 旧版前端代码（已废弃，保留参考）
│
├── vite.config.js                    # Vite 构建配置
├── package.json                      # 项目依赖配置
└── README.md                         # 项目文档
```

## 🔧 技术栈

### 前端

- **Vue 3** - 渐进式 JavaScript 框架（Composition API + `<script setup>`）
- **Vue Router** - 官方路由管理器
- **Pinia** - 新一代状态管理库
- **Vite** - 下一代前端构建工具
- **Axios** - HTTP 客户端
- **XLSX** - Excel 文件导入导出

### 后端

- **Flask** - Python 轻量级 Web 框架
- **Python 3.8+** - 后端语言
- **SQLite** - 当前业务数据库，按表存储订单、商品、原材料档案和库存

### 部署

- **Docker** - 容器化部署
- **Nginx** - 反向代理（可选）

## 📝 功能模块

### 订单管理
- ✅ **订单创建** - 支持中固/绝缘两种订单类型
- ✅ **智能填充** - 粘贴文本自动解析（支持两种格式）
  - 模式1: 系统标准化复制格式（【中固订单】/【绝缘订单】开头）
  - 模式2: 模糊提取引擎（智能识别姓名、电话、地址）
- ✅ **订单编辑** - 修改订单信息（使用专用 `/edit` 端点，不影响状态）
- ✅ **包装与物流服务** - 订单录入和编辑支持包装、物流服务下拉选择，并写入订单数据
- ✅ **订单草稿保留** - 离开新增/修改页面后通过顶部悬浮入口返回，表单数据不会丢失
- ✅ **订单搜索** - 全局搜索（运单号、收货人、电话、地址）
- ✅ **订单复制** - 一键复制订单信息，支持"制单归属"字段
- ✅ **订单删除** - 权限控制下的物理删除

### 订单状态流转
- ✅ **未完成 → 已完成** - 订单完成确认（货物内容预览弹窗）
- ✅ **已完成 → 已出库** - 发货出库（选择物流方式、录入运单号）
- ✅ **已出库 → 审核** - 物流审核（支持修改运单号）
- ✅ **状态撤销** - 已完成订单可撤销至未完成

### 回单管理
- ✅ **回单上传** - 支持图片格式，自动压缩（max 800x800）
- ✅ **图片旋转** - 在线旋转调整方向（90°增量）
- ✅ **大图预览** - 点击图片全屏预览（z-index 100001）
- ✅ **视图切换** - 预览模式 ↔ 上传模式无缝切换
- ✅ **搜索集成** - 搜索结果中直接上传/查看回单（粉色主题按钮）
- ✅ **回单删除** - 彻底删除回单图片

### 运费对账系统
- ✅ **物流对账** - 物流运费记录与对账
- ✅ **快递对账** - 快递运费记录与对账
- ✅ **备用金管理** - 运费备用金录入与余额跟踪
- ✅ **日期筛选** - 按年月期数筛选对账数据
- ✅ **Excel 导出** - 导出对账表格（带样式、边框、字体）
- ✅ **绝缘订单标记** - 绝缘订单以红色字体显示
- ✅ **多笔运费** - 支持单个订单多笔运费记录

### 商品与库存管理
- ✅ **成品商品列表** - 商品档案新增、修改、复制、删除和门店筛选
- ✅ **原材料商品列表** - 独立维护原材料名称、编号、规格、单位、分类、仓库和门店
- ✅ **公共商品弹窗** - `ProductFormModal.vue` 根据路由或 `mode` 属性切换成品/原材料模式
- ✅ **独立数据表** - 成品保存到 `products`，原材料保存到 `raw_material_products`
- ✅ **成品库存** - 读取 `products` 与 `inventory` 数据
- ✅ **原材料库存** - 展示原材料库存状态，并兼容原材料商品档案
- ✅ **单位分组** - `units` 表通过 `unit_type` 区分计量单位和包装

订单中的包装和物流服务使用字符串保存：

- 包装字段：`goods_packaging`，默认值为“无”
- 物流服务字段：`logistics_service`，默认值为“送货上门+回单拍照回传”
- 历史订单可能把 `logistics_service` 返回为数组，新订单返回字符串，前端会兼容两种格式

### 原材料业务数据
- ✅ **数据录入** - 使用量/生产量/备注快速录入
- ✅ **时间线展示** - 按日期分组的朋友圈式时间线
- ✅ **日期筛选** - 默认30天，支持自定义日期范围
- ✅ **快捷词库** - 备注历史标签，点击快速填充
- ✅ **行内编辑** - 双击单元格直接修改数据
- ✅ **数据删除** - 行级删除操作

### 用户权限
- ✅ **用户管理** - 增删改查用户账户
- ✅ **角色管理** - 超级管理员、管理员、操作员、普通员工
- ✅ **权限控制** - 细粒度权限（12+权限点）
- ✅ **登录认证** - 本地存储 + Header 认证

### 辅助工具
- ✅ **智能计算器** - 支持加减乘除和括号运算
- ✅ **NomiAI 助手** - 浮动智能助手，快捷操作导航
- ✅ **日期筛选** - 已出库订单/原材料数据日期范围筛选
- ✅ **复制功能** - 支持 HTTP 环境的降级复制方案

## 🏗️ 架构设计

### 状态管理
所有 API 请求逻辑统一封装在 Pinia stores 中：
- `useUserStore()` - 用户登录、用户管理、权限控制
- `useOrderStore()` - 订单 CRUD、状态流转
- `useMaterialStore()` - 原材料数据管理
- `useNomiStore()` - NomiAI 助手状态

### 工具函数
通用工具函数提取到 `utils/` 目录：
- **tools.js** - 日期格式化、文本处理、图片处理、智能解析、剪贴板操作
- **constants.js** - 常量定义（订单状态、角色权限等）
- **helpers.js** - 辅助函数（数据转换、验证等）

### API 封装
- **统一请求拦截** - 自动注入认证 Header（Username、Role）
- **响应处理** - 统一错误处理和数据提取
- **环境适配** - 开发/生产环境自动切换 baseURL

### 组件组织
- `views/` - 页面级组件，按前台/后台分类
- `components/common/` - 公共弹窗和工具组件
- `components/admin/` - 后台管理公共弹窗，包含成品/原材料共用的 `ProductFormModal.vue`
- `components/front/` - 前台专用弹窗组件

### 前端组件说明表

| 页面/组件 | 类型 | 主要职责 | 主要数据来源 |
|-----------|------|----------|--------------|
| `src/views/admin/orders/OrderForm.vue` | 页面 | 新增、修改订单；包装、物流服务选择；保存订单草稿状态 | `/api/orders`、单位接口 |
| `src/views/admin/orders/UnifiedOrderList.vue` | 页面 | 统一展示订单和物流状态；复制物流订单文本 | `/api/orders`、门店接口 |
| `src/views/admin/products/ProductList.vue` | 页面 | 成品商品档案新增、编辑、复制、删除 | `/api/products` |
| `src/views/admin/products/MaterialProductList.vue` | 页面 | 原材料商品档案新增、编辑、复制、删除 | `/api/raw-material-products` |
| `src/views/admin/products/InventoryList.vue` | 页面 | 成品库存查询和调整 | `/api/products/inventory` |
| `src/views/admin/products/MaterialInventory.vue` | 页面 | 原材料库存展示和筛选；当前库存调整为前端演示 | `/api/raw-material-products` |
| `src/components/admin/ProductFormModal.vue` | 公共弹窗 | 根据 `mode` 或路由元信息切换成品/原材料录入模式 | `/api/products` 或 `/api/raw-material-products` |
| `src/views/front/MaterialDisplay.vue` | 页面 | 原材料使用/生产流水时间线和快捷备注 | `/api/materials` |

### 商品弹窗模式

`src/components/admin/ProductFormModal.vue` 是成品和原材料共用的录入组件：

- 在 `ProductList.vue` 中使用 `mode="finished-product"`，调用 `/api/products`
- 在 `MaterialProductList.vue` 中使用 `mode="raw-material"`，调用 `/api/raw-material-products`
- 组件也会读取当前路由的 `meta.productType`，兼容直接从路由进入的场景
- 两种模式共用门店、仓库、分类、单位、单位换算、属性和状态字段
- 只有数据存储目标不同，原材料不会写入成品 `products` 表

### 后台路由

| 路由 | 页面 | 数据用途 |
|------|------|----------|
| `/admin/products` | 成品商品列表 | 成品档案，使用 `products` 表 |
| `/admin/materials` | 原材料列表 | 原材料商品档案，使用 `raw_material_products` 表 |
| `/admin/inventory` | 成品库存 | 成品库存数据 |
| `/admin/inventory/materials` | 原材料库存 | 原材料库存展示和前端调整演示 |

## 🔐 权限说明

系统支持基于角色和权限点的细粒度访问控制：

### 权限点列表

| 权限点 | 说明 |
|--------|------|
| `pending.add` | 创建订单 |
| `pending.edit` | 编辑订单 |
| `pending.delete` | 删除未完成订单 |
| `completed.delete` | 删除已完成订单 |
| `completed.ship` | 发货出库 |
| `shipped.audit` | 审核已出库订单 |
| `shipped.upload_receipt` | 上传回单 |
| `shipped.view_receipt` | 查看回单 |
| `shipped.delete_receipt` | 删除回单 |
| `material.add` | 录入原材料 |
| `material.view` | 查看原材料 |
| `material.edit` | 编辑原材料 |
| `material.delete` | 删除原材料 |
| `system.user_manage` | 用户管理 |
| `reconciliation.view` | 查看运费对账 |
| `reconciliation.edit` | 编辑运费对账 |

### 角色说明

- **超级管理员** (`super_admin`) - 拥有所有权限，无需配置
- **管理员** (`admin`) - 自定义权限组合
- **操作员** (`operator`) - 一般操作权限
- **普通员工** (`employee`) - 受限查看权限（隐藏电话/服务等敏感信息）

## 🌐 API 配置

### 开发环境

后端 API 地址在 `vite.config.js` 中配置代理：

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:7899',
      changeOrigin: true
    }
  }
}
```

### 生产环境

生产环境使用相对路径 `/api`，前后端需部署在同一域名下，或配置 Nginx 反向代理。

**Nginx 配置示例：**

```nginx
server {
  listen 80;
  server_name your-domain.com;

  # 前端静态文件
  location / {
    root /path/to/dist;
    try_files $uri $uri/ /index.html;
  }

  # 后端 API 代理
  location /api {
    proxy_pass http://localhost:7899;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # 上传文件
  location /uploads {
    alias /path/to/uploads;
  }
}
```

## 📦 重构说明

本项目已完成从传统原生 JS 架构到现代 Vue 3 架构的全面重构。

### 重构内容

#### 1. 技术栈升级
- ❌ 原生 JavaScript + jQuery → ✅ Vue 3 Composition API
- ❌ 手动 DOM 操作 → ✅ 响应式数据绑定
- ❌ 全局函数 → ✅ Pinia 状态管理
- ❌ 碎片化 CSS → ✅ 组件化样式

#### 2. 组件架构重组
- ✅ 按功能和业务分类（common/front/admin）
- ✅ 弹窗组件统一管理（Teleport to body）
- ✅ 跨组件通信优化（Event Bus → Pinia + CustomEvent）
- ✅ 删除 15+ 重复/冗余组件

#### 3. API 请求统一化
- ✅ 所有 API 逻辑迁移到 Pinia stores
- ✅ Axios 统一请求封装（拦截器、错误处理）
- ✅ 认证 Header 自动注入（Username、Role）
- ✅ 环境适配（开发/生产自动切换）

#### 4. 工具函数提取
- ✅ 日期时间处理
- ✅ 图片处理（旋转、Base64、压缩）
- ✅ 智能订单解析引擎
- ✅ 剪贴板操作封装（支持降级）

#### 5. 代码质量提升
- ✅ 统一代码风格（Composition API + `<script setup>`）
- ✅ 移除全局变量污染
- ✅ TypeScript 类型提示（JSDoc）
- ✅ 性能优化（计算属性、事件委托）

### 新增功能

1. **运费对账系统**
   - 物流/快递运费对账
   - 备用金管理
   - Excel 导出（带样式）
   - 绝缘订单红色标记

2. **回单功能增强**
   - 图片旋转和大图预览
   - 搜索结果中直接上传/查看回单
   - 条件渲染按钮（有回单显示预览，无回单显示上传）

3. **智能填充优化**
   - "制单归属"字段检测和自动填充
   - 复制模板优化（字段放在最下面）

4. **UI 细节优化**
   - 回单按钮粉色主题（`#FDECEE` 背景 + `#F26E83` 文字）
   - 旋转按钮悬停效果修复（不再漂移）
   - z-index 层级管理（预览模态框 100001）

5. **兼容性改进**
   - 复制功能降级方案（支持 HTTP 环境）
   - Docker 启动脚本路径自动检测
   - 生产环境 API 请求修复

### 迁移对比

| 项目 | 原版本 (frontend/) | 新版本 (src/) |
|------|-------------------|---------------|
| 代码行数 | ~3000 行 | ~2800 行 |
| 组件数量 | 30+ 个文件 | 18 个核心组件 |
| 全局函数 | 50+ 个 | 0 个 |
| API 调用 | 分散在各处 | 统一在 stores |
| 状态管理 | localStorage + 全局变量 | Pinia + localStorage |
| 构建工具 | 无 | Vite |
| Excel 导出 | 无 | XLSX 库 |

### 目录说明

- `src/` - 新版本代码（当前使用）
- `backend/` - 后端代码（Flask API）
- `data/` - SQLite 数据库和历史备份
- `uploads/` - 上传文件存储
- `frontend old/` - 旧版本代码（已废弃，可删除）

## 🤝 贡献与支持

### 开发规范

- 使用 Vue 3 Composition API + `<script setup>` 语法
- 组件命名使用 PascalCase（如 `OrderFormModal.vue`）
- API 请求统一放在 Pinia stores 中
- 工具函数放在 `utils/` 目录中
- 样式优先使用 scoped，公共样式放在 `assets/styles/`
- 提交前运行 `npm run build` 确保构建成功

### 版本信息

- **当前版本**: v3.0.0
- **最后更新**: 2026-09-08
- **Vue 版本**: 3.4+
- **Vite 版本**: 8.2.2
- **Node 版本**: 20.19.0+（或 22.12.0+）

### 数据存储

系统当前使用 SQLite 数据库 `data/order_system.db`：

- `orders` - 订单数据
- `products` - 成品商品档案
- `raw_material_products` - 原材料商品档案
- `inventory` - 成品库存数据
- `material_records` - 原材料使用/生产流水
- `units` - 计量单位和包装，使用 `unit_type` 分组
- `attributes` - 商品属性及选项
- `stores`、`warehouses`、`customers` - 基础业务数据
- `uploads/` - 回单图片和人事报告文件

原材料商品档案与原材料使用/生产流水是两类数据：

- 原材料商品档案：用于后台原材料列表，并作为原材料库存等后续业务的数据来源，存储在 `raw_material_products`
- 原材料使用/生产流水：用于前台原材料数据时间线，存储在 `material_records`

历史 JSON 文件仅作为迁移或备份参考，当前业务接口以 SQLite 为准。

### 常见问题

**Q: 生产环境 API 请求失败？**
A: 确保前后端部署在同一域名下，或配置 Nginx 反向代理。检查 `src/api/request.js` 中的 baseURL 配置。

**Q: Docker 启动失败？**
A: 确保 Docker Desktop 正在运行，检查 `backend/start.bat` 中的路径配置。

**Q: 复制功能在生产环境不工作？**
A: 已修复降级方案，支持 HTTP 环境。确保使用最新版本代码。

**Q: Excel 导出样式不对？**
A: 确保安装了 `xlsx` 依赖：`npm install xlsx`

### 技术支持

如有问题或建议，欢迎提交 Issue 或 Pull Request！

### License

MIT License

---

**Made with ❤️ by Your Team**
