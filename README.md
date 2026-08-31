# 订单管理系统

基于 Vue 3 + Vite 的现代化物流订单管理系统，支持订单全生命周期管理、回单管理、运费对账和智能订单解析。

## ✨ 主要特性

- 🎯 **完整订单流转** - 未完成 → 已完成 → 已出库全流程管理
- 📸 **回单智能管理** - 图片上传、在线预览、旋转编辑、大图查看
- 💰 **运费对账系统** - 物流/快递运费对账、备用金管理、Excel导出
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
│   ├── app.py                        # Flask 主应用
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
│   │   ├── front/                    # 前台业务页面
│   │   │   ├── OrderList.vue         # 订单列表（未完成+已完成）
│   │   │   ├── ShippedOrderList.vue  # 已出库订单
│   │   │   └── MaterialDisplay.vue   # 原材料数据展示
│   │   │
│   │   └── admin/                    # 后台管理页面
│   │       ├── Admin.vue             # 管理后台容器
│   │       ├── UserManage.vue        # 用户权限管理
│   │       ├── LogisticsTruckReconciliation.vue  # 物流对账
│   │       ├── ExpressCourierReconciliation.vue  # 快递对账
│   │       └── orders/               # 订单管理模块
│   │           └── UnifiedOrderList.vue  # 统一订单列表
│   │
│   ├── components/                   # 组件库
│   │   ├── common/                   # 公共组件
│   │   │   ├── ConfirmModal.vue              # 确认对话框
│   │   │   ├── SearchOrderModal.vue          # 全局搜索
│   │   │   ├── ShippedOrderActionModal.vue   # 已出库订单操作
│   │   │   ├── SmartCalculator.vue           # 智能计算器
│   │   │   └── NomiFloatingAI.vue            # NomiAI 浮动助手
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
├── data/                             # 数据存储（JSON 数据库）
│   ├── orders_db.json                # 订单数据
│   ├── users_db.json                 # 用户数据
│   ├── material_db.json              # 原材料数据
│   └── carrier_tags.json             # 物流快捷词库
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
- **JSON** - 文件数据库（生产环境建议迁移至 MySQL/PostgreSQL）

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
- `data/` - 数据存储（JSON 文件数据库）
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

- **当前版本**: v2.8.0
- **最后更新**: 2026-08-30
- **Vue 版本**: 3.4+
- **Vite 版本**: 5.0+
- **Node 版本**: 16.0+

### 数据存储

系统使用 JSON 文件作为数据库：

- `data/orders_db.json` - 订单数据
- `data/users_db.json` - 用户数据
- `data/material_db.json` - 原材料数据
- `data/carrier_tags.json` - 物流公司快捷词库
- `uploads/` - 回单图片存储目录

⚠️ **生产环境建议**: 迁移到 MySQL/PostgreSQL 等关系型数据库以提升性能和数据安全性。

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
