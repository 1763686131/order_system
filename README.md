# order-system

订单管理系统 - Vue 3 版本

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
├── App.vue                          # 根组件
├── main.js                          # 入口文件
├── router/
│   └── index.js                     # 路由配置
├── stores/
│   ├── user.js                      # 用户状态管理
│   └── order.js                     # 订单状态管理
├── views/
│   ├── LoginView.vue                # 登录页面
│   └── MainView.vue                 # 主界面
├── components/
│   ├── layout/
│   │   ├── NavBar.vue               # 导航栏
│   │   └── FloatingMenu.vue         # 悬浮菜单
│   ├── orders/
│   │   ├── OrderList.vue            # 订单列表
│   │   ├── OrderCard.vue            # 订单卡片
│   │   ├── CreateOrderModal.vue     # 创建订单
│   │   └── SearchOrderModal.vue     # 搜索订单
│   ├── material/
│   │   ├── MaterialTimeline.vue     # 原材料时间轴
│   │   └── UploadMaterialModal.vue  # 录入原材料
│   └── user/
│       └── UserManageModal.vue      # 用户管理
├── api/
│   ├── request.js                   # axios 封装
│   ├── auth.js                      # 认证 API
│   ├── orders.js                    # 订单 API
│   ├── materials.js                 # 原材料 API
│   └── users.js                     # 用户 API
└── assets/
    └── styles/
        └── main.css                 # 全局样式
```

## 🔧 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vue Router** - 官方路由管理器
- **Pinia** - 新一代状态管理库
- **Vite** - 下一代前端构建工具
- **Axios** - HTTP 客户端

## 📝 功能模块

- ✅ 用户登录认证
- ✅ 权限管理系统
- ✅ 订单管理（创建、编辑、搜索）
- ✅ 原材料数据管理
- ✅ 用户账户管理
- ✅ 订单状态流转
- ✅ 出库管理

## 🔐 权限说明

系统支持细粒度权限控制：

- `pending.add` - 创建订单权限
- `material.add` - 录入原材料权限
- `system.user_manage` - 用户管理权限

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

## 📦 从旧版本迁移

旧版本文件保留在 `frontend/` 目录下，新版本使用 `src/` 目录。

迁移完成后，可以删除旧版本文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
