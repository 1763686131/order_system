# order-system

订单管理系统 - Vue 3 重构版本

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

### 预览生产构建

```bash
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
│   │   └── ShippedOrderList.vue     # 已出库订单列表
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

### 前台功能
- ✅ 订单管理（创建、编辑、搜索、删除）
- ✅ 订单状态流转（未完成 → 已完成 → 已出库）
- ✅ 发货出库管理
- ✅ 回单上传与管理
- ✅ 原材料数据录入与查看
- ✅ 智能订单解析（粘贴文本自动填充）
- ✅ 智能计算器

### 后台管理
- ✅ 用户账户管理（增删改查）
- ✅ 细粒度权限控制
- ✅ 用户登录认证

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

系统支持细粒度权限控制：

- `pending.add` - 创建订单权限
- `pending.edit` - 编辑订单权限
- `pending.delete` - 删除订单权限
- `completed.ship` - 发货出库权限
- `shipped.audit` - 审核已出库订单权限
- `material.add` - 录入原材料权限
- `material.view` - 查看原材料权限
- `system.user_manage` - 用户管理权限

超级管理员 (`super_admin`) 拥有所有权限。

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

本项目已完成从传统架构到现代 Vue 3 架构的重构：

### 重构内容
1. ✅ 组件结构重组（按功能和业务分类）
2. ✅ API 请求迁移到 Pinia stores
3. ✅ 工具函数提取和复用
4. ✅ 删除重复和碎片化组件
5. ✅ 统一代码风格（Composition API）

### 迁移完成后
旧版本文件保留在 `frontend/` 目录下，新版本使用 `src/` 目录。可根据需要删除旧版本文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

