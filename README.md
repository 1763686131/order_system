# 订单管理系统

基于 Vue 3 + Vite 的现代化物流订单管理系统，支持订单全生命周期管理、回单管理、原材料数据管理和智能订单解析。

## ✨ 主要特性

- 🎯 **完整订单流转** - 未完成 → 已完成 → 已出库全流程管理
- 📸 **回单智能管理** - 图片上传、在线预览、旋转编辑、大图查看
- 📊 **原材料数据** - 时间线展示、日期筛选、快捷词库、行内编辑
- 🔍 **全局搜索** - 支持运单号、收货人、电话、地址多维度搜索
- 🤖 **智能解析** - 粘贴文本自动识别填充订单信息
- 🧮 **智能计算器** - 内置重量计算器，支持复杂算术表达式
- 🎨 **NomiAI 助手** - 浮动智能助手，快捷操作导航
- 🔐 **权限管理** - 细粒度权限控制，支持多角色管理

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0
- Python >= 3.8 (后端)

### 安装依赖

```bash
# 前端依赖
npm install

# 后端依赖
pip install -r backend/requirements.txt
```

### 启动项目

```bash
# 启动后端服务（端口 7899）
python backend/app.py

# 启动前端开发服务器（端口 3000）
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
npm run preview
```

## 📁 项目结构

```
src/
├── App.vue                          # 根组件（路由容器）
├── main.js                          # 入口文件
├── router/
│   └── index.js                     # 路由配置
├── stores/                          # 状态管理 (Pinia)
│   ├── user.js                      # 用户状态 + API
│   ├── order.js                     # 订单状态 + API
│   ├── material.js                  # 原材料状态 + API
│   └── nomi.js                      # 小圆智能助手状态
├── views/                           # 页面级组件
│   ├── LoginView.vue                # 登录页面
│   ├── MainView.vue                 # 主界面（业务逻辑容器）
│   ├── front/                       # 前台页面
│   │   ├── OrderList.vue            # 订单列表（未完成+已完成）
│   │   ├── ShippedOrderList.vue     # 已出库订单列表
│   │   └── MaterialDisplay.vue      # 原材料数据展示（时间线视图）
│   └── admin/                       # 后台管理页面
│       └── UserManage.vue           # 用户权限管理
├── components/                      # 组件
│   ├── common/                      # 公共组件
│   │   ├── ConfirmModal.vue         # 确认弹窗
│   │   ├── SearchOrderModal.vue     # 搜索订单
│   │   ├── ShippedOrderActionModal.vue  # 已出库订单操作
│   │   ├── SmartCalculator.vue      # 智能计算器
│   │   └── NomiFloatingAI.vue       # 小圆智能助手
│   └── front/                       # 前台专用弹窗
│       ├── OrderFormModal.vue       # 订单表单（新增/编辑）
│       ├── ShipOrderModal.vue       # 发货出库
│       └── UploadMaterialModal.vue  # 录入原材料
├── api/
│   └── request.js                   # 统一请求封装 (axios)
├── utils/
│   └── tools.js                     # 工具函数集合
└── assets/
    └── styles/
        └── main.css                 # 全局样式
```

## 🔧 技术栈

- **Vue 3** - 渐进式 JavaScript 框架（Composition API）
- **Vue Router** - 官方路由管理器
- **Pinia** - 新一代状态管理库
- **Vite** - 下一代前端构建工具
- **Axios** - HTTP 客户端

## 📝 功能模块

### 订单管理
- ✅ **订单创建** - 支持中固/绝缘两种订单类型
- ✅ **智能填充** - 粘贴文本自动解析（支持两种格式）
  - 模式1: 系统标准化复制格式（【中固订单】/【绝缘订单】开头）
  - 模式2: 模糊提取引擎（智能识别姓名、电话、地址）
- ✅ **订单编辑** - 修改订单信息（使用专用 `/edit` 端点，不影响状态）
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
- ✅ **悬停优化** - 旋转按钮悬停效果不漂移

### 原材料管理
- ✅ **数据录入** - 使用量/生产量/备注快速录入
- ✅ **时间线展示** - 按日期分组的朋友圈式时间线
- ✅ **日期筛选** - 默认30天，支持自定义日期范围
- ✅ **快捷词库** - 备注历史标签，点击快速填充
- ✅ **行内编辑** - 双击单元格直接修改数据
- ✅ **数据删除** - 行级删除操作

### 用户权限
- ✅ **用户管理** - 增删改查用户账户
- ✅ **角色管理** - 超级管理员、管理员、操作员、普通员工
- ✅ **权限控制** - 细粒度权限（10+权限点）
- ✅ **登录认证** - 本地存储 + Header 认证

### 辅助工具
- ✅ **智能计算器** - 支持加减乘除和括号运算
- ✅ **NomiAI 助手** - 浮动智能助手，快捷操作导航
- ✅ **日期筛选** - 已出库订单/原材料数据日期范围筛选

## 🏗️ 架构设计

### 状态管理
所有 API 请求逻辑统一封装在 Pinia stores 中：
- `useUserStore()` - 用户登录、用户管理
- `useOrderStore()` - 订单 CRUD、状态流转
- `useMaterialStore()` - 原材料数据管理

### 工具函数
通用工具函数提取到 `utils/tools.js`：
- 日期时间格式化
- 文本处理与验证
- 图片处理（旋转、Base64转换）
- 智能订单解析
- 剪贴板操作
- 本地存储封装

### 组件组织
- `views/` - 页面级组件，按前台/后台分类
- `components/common/` - 公共弹窗组件
- `components/front/` - 前台专用弹窗组件

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
| `shipped.receipt` | 管理回单 |
| `material.add` | 录入原材料 |
| `material.view` | 查看原材料 |
| `material.edit` | 编辑原材料 |
| `material.delete` | 删除原材料 |
| `system.user_manage` | 用户管理 |

### 角色说明

- **超级管理员** (`super_admin`) - 拥有所有权限，无需配置
- **管理员** (`admin`) - 自定义权限组合
- **操作员** (`operator`) - 一般操作权限
- **普通员工** (`employee`) - 受限查看权限（隐藏电话/服务等敏感信息）

## 🌐 API 配置

后端 API 地址在 `vite.config.js` 中配置：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true
    }
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

#### 4. 工具函数提取
- ✅ 日期时间处理
- ✅ 图片处理（旋转、Base64、压缩）
- ✅ 智能订单解析引擎
- ✅ 剪贴板操作封装

#### 5. 代码质量提升
- ✅ 统一代码风格（Composition API + `<script setup>`）
- ✅ 移除全局变量污染
- ✅ TypeScript 类型提示（JSDoc）
- ✅ 性能优化（计算属性、事件委托）

### 新增功能

在重构过程中新增/优化的功能：

1. **回单功能增强**
   - 图片旋转和大图预览
   - 搜索结果中直接上传/查看回单
   - 条件渲染按钮（有回单显示预览，无回单显示上传）

2. **智能填充优化**
   - "制单归属"字段检测和自动填充
   - 复制模板优化（字段放在最下面）

3. **UI 细节优化**
   - 回单按钮粉色主题（`#FDECEE` 背景 + `#F26E83` 文字）
   - 旋转按钮悬停效果修复（不再漂移）
   - z-index 层级管理（预览模态框 100001）

4. **Bug 修复**
   - 修改订单类型时卡片隐藏问题（使用 `/edit` 端点）
   - 回单上传认证头缺失问题
   - 控制台报错清理

### 迁移对比

| 项目 | 原版本 (frontend/) | 新版本 (src/) |
|------|-------------------|---------------|
| 代码行数 | ~3000 行 | ~2500 行 |
| 组件数量 | 30+ 个文件 | 15 个核心组件 |
| 全局函数 | 50+ 个 | 0 个 |
| API 调用 | 分散在各处 | 统一在 stores |
| 状态管理 | localStorage + 全局变量 | Pinia + localStorage |
| 构建工具 | 无 | Vite |

### 目录说明

- `frontend/` - 旧版本代码（保留作为参考）
- `src/` - 新版本代码（当前使用）
- `backend/` - 后端代码（Flask API）
- `data/` - 数据存储（JSON 文件数据库）

可根据需要删除 `frontend/` 目录。

## 🤝 贡献与支持

### 开发规范

- 使用 Vue 3 Composition API + `<script setup>` 语法
- 组件命名使用 PascalCase（如 `OrderFormModal.vue`）
- API 请求统一放在 Pinia stores 中
- 工具函数放在 `utils/tools.js` 中
- 样式优先使用 scoped，公共样式放在 `assets/styles/`

### 版本信息

- **当前版本**: v2.2.22
- **最后更新**: 2026-08-25
- **Vue 版本**: 3.4+
- **Vite 版本**: 5.0+

### 数据存储

系统使用 JSON 文件作为数据库：

- `data/orders_db.json` - 订单数据
- `data/users_db.json` - 用户数据
- `data/material_db.json` - 原材料数据
- `data/carrier_tags.json` - 物流公司快捷词库
- `uploads/` - 回单图片存储目录

⚠️ **生产环境建议**: 迁移到 MySQL/PostgreSQL 等关系型数据库。

### 技术支持

如有问题或建议，欢迎提交 Issue！

### License

MIT License

