# 订单与进销存管理系统

基于 Vue 3、Vite、Pinia、Flask 和 SQLite 的内网业务管理系统，覆盖销售订单、物流出库、商品与原材料档案、供应商、仓库库存、入库审核、回单和运费对账等流程。

系统采用前后端分离开发、同源部署的方式运行。所有前端资源均由本地项目构建，不依赖在线 CDN、Google Fonts 或在线图标库，适合纯内网和本地环境。

## 当前版本

| 项目 | 内容 |
| --- | --- |
| 应用版本 | `3.0.0` |
| 文档更新 | `2026-09-09` |
| 前端 | Vue 3、Vite 8、Pinia、Vue Router、Axios、XLSX |
| 后端 | Python、Flask、SQLite |
| 开发端口 | 前端 `3000`，后端 `7899` |
| API 前缀 | `/api` |
| 主数据库 | `data/order_system.db` |

## 主要功能

- 销售订单创建、编辑、复制、查询及状态流转
- 成品和原材料档案独立维护
- 门店、仓库、客户、供应商和单位等基础资料管理
- 成品库存与原材料库存查询
- 原材料采购入库和成品生产完工入库
- 入库单待审核、审核、反审核、红冲、重新启用和删除
- 入库记录与出库记录统一流水组件
- 回单上传、查看、旋转和删除
- 物流、快递运费对账及 Excel 导出
- 用户、角色和细粒度权限管理
- 原材料使用/生产流水记录

## 2026-09-09 更新

本轮库存模块已完成以下调整：

- 新增供应商管理页面，支持新增、编辑、查看、筛选和停用/删除。
- 入库弹窗按门店联动仓库、供应商和物料，切换门店后自动清理无效选项。
- 入库明细批次号默认使用当天日期，格式为 `YYYY-MM-DD`，允许手工修改。
- “保存草稿”仅写入 Pinia 内存，同一前端会话内再次打开弹窗可恢复，不请求服务器。
- “提交过账”调整为“提交审核”，提交后单据状态为待审核，库存保持不变。
- 入库记录抽屉支持审核、反审核、红冲、重新启用和删除等状态操作。
- 审核请求成功后才写入库存余额和库存流水；反审核会同步回退库存。
- 出库记录复用流水组件，但仅用于查看销售订单的成品流向，不在该页面审核或删除。
- 入库/出库记录支持原材料与成品切换、组合筛选、文字搜索下拉和明细抽屉。
- 原材料商品列表的当前库存已映射到库存余额接口。
- 原材料库存页面的库存数量、库存金额和平均单位成本已映射到库存 API。

## 快速开始

### 环境要求

- Node.js `20.19.0+` 或 `22.12.0+`
- Python `3.8+`，推荐 Python `3.10`
- npm
- Docker Desktop，可选

纯内网环境需要提前准备 npm、pip 依赖缓存或内部镜像源。应用运行时不需要访问互联网。

### 安装依赖

在项目根目录执行：

```powershell
npm install

py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

如果本机没有 `py` 命令，可以使用对应版本的 `python`。

### 本地开发

打开第一个终端启动 Flask：

```powershell
.\.venv\Scripts\python.exe backend\app.py
```

打开第二个终端启动 Vite：

```powershell
npm run dev
```

访问地址：

- 前端：`http://localhost:3000`
- 后端健康检查：`http://localhost:7899/api/health`

开发环境中，Vite 会把 `/api` 请求代理到 `http://localhost:7899`。

### 构建前端

```powershell
npm run build
```

构建结果输出到 `dist/`。当前 Flask/Docker 部署读取 `frontend/` 目录，因此发布时需要将确认过的构建文件部署到 `frontend/`。

### Docker 启动后端

Windows 本地环境可运行：

```powershell
.\backend\start.bat
```

脚本会构建 `order-backend` 镜像并启动名为 `my_order_app` 的容器，将本地 `backend/`、`data/`、`frontend/` 和 `uploads/` 挂载到容器中。

`docker-compose.yml` 当前包含 NAS 环境的固定挂载路径。换机器部署前，必须先修改其中的宿主机路径。

## 项目结构

```text
order_system/
├─ backend/
│  ├─ app.py                         # Flask 入口、蓝图注册和静态文件服务
│  ├─ routes/
│  │  ├─ orders.py                   # 销售订单和物流状态接口
│  │  ├─ products.py                 # 成品、单位、属性和成品库存接口
│  │  ├─ raw_material_products.py    # 原材料商品档案接口
│  │  ├─ stock_inbounds.py           # 供应商、入库单、审核、库存余额和流水
│  │  ├─ materials.py                # 原材料使用/生产流水
│  │  ├─ stores.py                   # 门店接口
│  │  ├─ warehouses.py               # 仓库接口
│  │  ├─ customers.py                # 客户接口
│  │  ├─ freight.py                  # 运费与对账接口
│  │  ├─ users.py                    # 用户、角色与权限接口
│  │  └─ hr_reports.py               # 人事报告接口
│  ├─ utils/
│  │  ├─ db.py                       # SQLite 连接、建表和结构升级
│  │  └─ db_helper.py                # 历史数据兼容读写
│  ├─ tools/                         # 数据备份等维护脚本
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ start.bat
├─ src/
│  ├─ api/
│  │  └─ request.js                  # Axios 实例、认证头和统一响应处理
│  ├─ stores/
│  │  ├─ user.js                     # 登录、用户和权限状态
│  │  ├─ order.js                    # 销售订单状态
│  │  ├─ orderDraft.js               # 销售订单草稿
│  │  ├─ stockDraft.js               # 入库单会话内存草稿
│  │  ├─ material.js                 # 原材料业务流水
│  │  └─ nomi.js                     # 辅助工具状态
│  ├─ components/
│  │  ├─ common/
│  │  │  ├─ StockInOrderModal.vue    # 原材料/成品共用入库弹窗
│  │  │  ├─ ConfirmModal.vue         # 通用确认弹窗
│  │  │  ├─ SearchOrderModal.vue     # 全局订单搜索
│  │  │  └─ SmartCalculator.vue      # 计算器
│  │  ├─ admin/
│  │  │  ├─ ProductFormModal.vue     # 成品/原材料共用档案弹窗
│  │  │  └─ StoreFormModal.vue       # 门店维护弹窗
│  │  └─ front/                      # 前台订单、发货和原材料弹窗
│  ├─ views/
│  │  ├─ Admin.vue                   # 后台布局、菜单和入库弹窗注册
│  │  ├─ MainView.vue                # 前台业务容器
│  │  ├─ front/                      # 订单、已出库和原材料流水页面
│  │  └─ admin/
│  │     ├─ products/
│  │     │  ├─ ProductList.vue       # 成品档案
│  │     │  ├─ MaterialProductList.vue
│  │     │  ├─ InventoryList.vue     # 成品库存
│  │     │  ├─ MaterialInventory.vue # 原材料库存及库存金额
│  │     │  ├─ SupplierList.vue      # 供应商管理
│  │     │  └─ StockRecordList.vue   # 入库/出库记录通用组件
│  │     ├─ orders/                  # 后台销售订单
│  │     ├─ inventory/               # 仓库管理
│  │     ├─ customers/               # 客户管理
│  │     ├─ finance/                 # 财务与运费对账
│  │     ├─ system/                  # 用户、角色和门店
│  │     └─ hr/                      # 人事报告
│  ├─ router/index.js                # 前端路由和登录守卫
│  ├─ utils/                         # Excel、日期、单位和通用工具
│  └─ assets/styles/                 # 本地全局样式
├─ data/
│  ├─ order_system.db                # 当前 SQLite 业务数据库
│  └─ backup_before_cleanup/         # 历史 JSON 备份
├─ docs/
│  ├─ API接口文档.md                 # 完整 API 参数、响应和业务规则
│  ├─ 数据库表单说明.md              # 数据表说明
│  └─ BUG及优化文档.md               # 问题与优化记录
├─ uploads/                          # 回单和报告等上传文件
├─ frontend/                         # Flask/Docker 当前使用的生产静态文件
├─ dist/                             # Vite 默认构建输出
├─ frontend old/                     # 旧版前端，仅保留参考
├─ vite.config.js
├─ package.json
└─ README.md
```

## 库存业务规则

### 入库单状态

| 数据库状态 | 页面含义 | 是否影响库存 | 可执行操作 |
| --- | --- | --- | --- |
| `draft` | 待审核 | 否 | 审核、红冲 |
| `reviewed` | 已审核 | 是 | 反审核 |
| `posted` | 已过账，兼容历史数据 | 是 | 反审核 |
| `cancelled` | 已红冲 | 否 | 重新启用、删除 |

前端把已提交到服务器的 `draft` 显示为“待审核”。`posted` 是旧数据兼容状态，新审核流程使用 `reviewed`。

### 入库流程

```text
填写入库单
  ├─ 保存草稿 -> Pinia 内存 -> 不访问服务器、不改变库存
  └─ 提交审核 -> 保存为 draft -> 入库记录显示待审核
                              -> 审核成功后写入库存余额与库存流水
                              -> 反审核时回退对应库存与流水
```

核心约束：

- 门店确定后，只能选择归属该门店的仓库、供应商和物料。
- 原材料采购入库提交审核时必须选择供应商。
- 有效明细必须包含物料、正数实收数量和批次号。
- 审核和库存写入在同一数据库事务中完成。
- 未审核单据只进入入库记录，不计入库存数量和库存金额。
- 已审核单据不能直接删除，必须先反审核。
- 待审核单据红冲后可以重新启用；已红冲单据可以物理删除。

### 出库记录

`StockRecordList.vue` 通过 `mode` 复用两种模式：

- `INBOUND`：读取入库单，允许执行入库审核相关操作。
- `OUTBOUND`：读取销售订单，仅展示成品流向和明细，不执行审核、反审核、红冲或删除。

### 原材料库存与金额

原材料库存相关页面以 `/api/stock-balances?type=raw-material` 为库存数据源：

- `MaterialProductList.vue` 映射并展示当前库存。
- `MaterialInventory.vue` 按物料、门店和仓库汇总库存数量。
- 库存金额由当前库存数量和已审核入库流水的平均单位成本计算。
- `averageUnitCost` 为平均单位成本。
- `inventoryAmount` 为库存金额。
- 历史入库流水缺少单价时按零成本参与数量口径，避免虚增库存金额。

## 主要页面

| 路由 | 页面 | 主要数据来源 |
| --- | --- | --- |
| `/admin/products` | 成品档案 | `/api/products` |
| `/admin/materials` | 原材料档案 | `/api/raw-material-products`、`/api/stock-balances` |
| `/admin/suppliers` | 供应商管理 | `/api/suppliers` |
| `/admin/inventory` | 成品库存 | `/api/products/inventory` |
| `/admin/inventory/materials` | 原材料库存 | `/api/raw-material-products`、`/api/stock-balances` |
| `/admin/stock/in` | 入库记录 | `/api/stock-inbounds` |
| `/admin/stock/out` | 出库记录 | `/api/orders` |
| `/admin/inventory/warehouse` | 仓库管理 | `/api/warehouses` |
| `/admin/orders` | 销售订单 | `/api/orders` |
| `/admin/customers` | 客户管理 | `/api/customers` |

## 库存关键接口

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/suppliers` | 查询供应商，可按门店和状态筛选 |
| `POST` | `/api/suppliers` | 新增供应商 |
| `PUT` | `/api/suppliers/:id` | 修改供应商 |
| `DELETE` | `/api/suppliers/:id` | 删除或停用供应商 |
| `GET` | `/api/stock-inbounds` | 查询入库单列表 |
| `GET` | `/api/stock-inbounds/:id` | 查询入库单及明细 |
| `POST` | `/api/stock-inbounds` | 提交待审核入库单 |
| `PUT` | `/api/stock-inbounds/:id` | 修改未审核入库单 |
| `POST` | `/api/stock-inbounds/:id/audit` | 审核并写入库存 |
| `DELETE` | `/api/stock-inbounds/:id/audit` | 反审核并回退库存 |
| `DELETE` | `/api/stock-inbounds/:id` | 红冲，或删除已红冲单据 |
| `POST` | `/api/stock-inbounds/:id/restart` | 重新启用已红冲单据 |
| `GET` | `/api/stock-balances` | 查询库存数量、平均成本和库存金额 |

完整字段定义和请求示例见 [API 接口文档](docs/API接口文档.md)。

## 数据存储

系统当前以 SQLite 为业务数据源，本地和 Docker 默认都使用 `data/order_system.db`。

库存核心表：

- `suppliers`：供应商档案
- `stock_inbounds`：入库单头
- `stock_inbound_items`：入库单明细
- `stock_balances`：按物料、仓库、门店、库位和批次保存的库存余额
- `stock_movements`：审核后生成的库存流水
- `raw_material_products`：原材料商品档案
- `products`：成品商品档案

`data/backup_before_cleanup/` 中的 JSON 文件仅用于历史迁移和备份参考，当前业务接口以 SQLite 为准。

修改或替换数据库前，应先停止后端服务并备份 `data/order_system.db`，避免正在运行的进程继续写入。

## 前端开发约定

- 页面和组件使用 Vue 3 `<script setup>`。
- 页面级组件放在 `src/views/`，可复用弹窗放在 `src/components/`。
- 组件样式优先使用 `<style scoped>`，公共样式放在 `src/assets/styles/`。
- API 请求统一使用 `src/api/request.js`，接口地址保持 `/api` 相对路径。
- 临时表单状态使用 Pinia；需要跨刷新保存的数据必须明确设计持久化方案。
- 不引入在线 CDN、远程字体或在线矢量图标。
- 金额和数量显示使用千分位、固定精度和 `tabular-nums`。
- 提交代码前至少运行一次 `npm run build`。

## 部署说明

### 同源部署

生产环境前端请求使用相对路径 `/api`。建议由 Flask 或内网反向代理同时提供静态文件和 API，避免跨域及地址硬编码。

### 离线部署

完整离线环境建议提前准备：

- 已安装的 `node_modules` 或内部 npm 镜像
- Python wheel 缓存或内部 pip 镜像
- 已构建的 Docker 镜像
- 已生成的前端静态文件
- SQLite 数据库备份

`backend/Dockerfile` 当前配置了在线 pip 镜像。严格断网环境下应使用预构建镜像，或把镜像源改为内网地址。

## 常见问题

### 提交入库单后库存没有变化

提交审核只创建待审核单据。请进入“入库记录”，打开单据抽屉并点击“审核”。只有审核接口成功返回后，库存才会增加。

### 审核按钮一直没有变成反审核

检查 `/api/stock-inbounds/:id/audit` 是否返回成功，并确认后端容器运行的是最新代码。挂载代码更新后如未生效，重启 `my_order_app`。

### 原材料库存金额为零

确认入库单已经审核，并检查入库明细是否填写单价。没有单价的历史流水按零成本计算。

### 选择门店后没有供应商或物料

检查供应商和商品档案中的 `storeId`/门店归属。入库弹窗只显示当前门店可用的数据。

### 前端能打开但 API 请求失败

确认 Flask 正在监听 `7899`，访问 `/api/health` 检查服务，并核对 `vite.config.js` 中的代理目标。

### Docker 启动后页面仍是旧版本

后端容器读取 `frontend/`，而 `npm run build` 默认输出 `dist/`。需要更新 `frontend/` 中的部署文件，并重启容器。

## 相关文档

- [API 接口文档](docs/API接口文档.md)
- [数据库表单说明](docs/数据库表单说明.md)
- [SQLite 迁移说明](MIGRATION_SQLITE.md)
- [SQLite 使用说明](README_SQLITE.md)
- [BUG 及优化记录](docs/BUG及优化文档.md)
