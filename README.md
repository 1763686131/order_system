# 订单与进销存管理系统

基于 Vue 3、Vite、Pinia、Flask 和 SQLite 的内网业务管理系统，覆盖销售订单、物流出库、客户应收、收款历史、商品与原材料档案、供应商、仓库库存、入库审核、回单和运费对账等流程。

系统采用前后端分离开发、同源部署的方式运行。所有前端资源均由本地项目构建，不依赖在线 CDN、Google Fonts 或在线图标库，适合纯内网和本地环境。

## 当前版本

| 项目 | 内容 |
| --- | --- |
| 应用版本 | `3.0.0` |
| 文档更新 | `2026-09-11` |
| 前端 | Vue 3、Vite 8、Pinia、Vue Router、Axios、XLSX |
| 后端 | Python、Flask、SQLite |
| 开发端口 | 前端 `3000`，后端 `7899` |
| API 前缀 | `/api` |
| 主数据库 | `data/order_system.db` |

## 主要功能

- 销售订单创建、编辑、复制、查询及状态流转
- 退货订单管理、录入退货单及退货处理流程
- 成品和原材料档案独立维护
- 门店、仓库、客户、供应商和单位等基础资料管理
- 客户期初欠款、储值余额和应收欠款汇总
- 收款历史、收款单草稿、附件、打印和 Excel 导出
- 收款单审核入账、反审核回滚及客户账户流水追溯
- 成品库存与原材料库存查询
- 原材料采购入库和成品生产完工入库
- 入库单待审核、审核、反审核、红冲、重新启用和删除
- 入库记录与出库记录统一流水组件
- 回单上传、查看、旋转和删除
- 物流、快递运费对账及 Excel 导出
- 用户、角色和细粒度权限管理
- 原材料使用/生产流水记录

## 2026-09-11 更新

### 订单录入与列表

- 订单详情由侧边抽屉调整为居中弹窗，点击表格行即可打开，列表不再保留重复的”小眼睛”查看按钮。
- 销售订单恢复”复制为新订单”，点击后进入订单录入页并带入原单数据；物流列表的复制按钮用于复制物流信息文本。
- 新结构的已发货销售订单支持审核和反审核。审核后显示”已过帐”，隐藏修改、删除并锁定勾选；反审核成功后恢复为”已发货”。
- 物流录入、修改和回单管理保持独立流程，上传物流回单不再依赖订单是否审核，任意状态均可上传或更新。
- 订单详情统一展示商品税率、税额、含税金额以及应收、已收、未收汇总，其中已收使用绿色、未收使用红色强调。
- 订单录入的含税开关默认关闭；关闭时税率、含税单价和含税金额统一按 `0` 提交，开启后才计算并保存含税数据。

### 退货订单管理

- 新增退货订单列表页面 (`/admin/orders/returns`)，支持退货单录入、查询、筛选、分页和状态管理。
- 退货单支持按待处理、处理中、已完成和已拒绝四种状态筛选，每个状态显示实时数量徽章。
- 录入退货单弹窗包含基本信息（原订单号、退货日期、客户信息）、退货商品信息和退货原因及备注三个部分。
- 退货单号自动生成，格式为 `RTYYYYMMDDNNNN`，与收款单号 `SK` 前缀区分。
- 退货详情弹窗展示完整退货信息，包括退货单号、原订单号、客户名称、退货商品、退货数量、退货金额和处理状态。
- 待处理状态的退货单显示”处理退货”操作按钮，已完成和已拒绝状态仅支持查看详情。
- 页面设计遵循后台列表页视觉规范，保持与订单列表、收款历史等页面的视觉一致性。

### 财务收款模块

- 新增”应收欠款”页面，按客户展示客户 ID、联系人、电话、期初欠款、增加的应收欠款、收回欠款、优惠和当前应收欠款。
- 新增”收款历史”页面，支持按门店滑块筛选、自动生成收款单号、分页、复选、Excel 导出和收款单打印。
- 新增收款单居中弹窗，包含基本信息、收款信息和其他信息三部分，支持客户选择、收款方式、优惠金额、备注和附件图片。
- 收款单保存后首先进入待审核草稿，不会立即改变客户的应收欠款或储值余额。
- 收款单审核时按”优惠抵欠款 → 实收抵欠款 → 多收转预收储值”的顺序入账，并写入客户账户流水。
- 已审核收款单隐藏修改、删除，改为显示反审核；反审核会恢复客户欠款和本次增加的储值余额。
- 如果本次收款产生的预收储值已经被后续订单使用，系统会阻止反审核，避免客户储值出现错误负数。
- 应收欠款页面会同步收款审核产生的收回欠款和优惠金额，客户账户保持”应收欠款存正数、净额按储值余额减应收欠款计算”的口径。
- 新增”银行账户”页面，采用真实银行卡样式展示企业账户信息，支持卡片 3D 翻转查看账户余额。
- 银行账户管理支持录入账户名称、账号、开户行、行号、账户余额等信息。
- 银行卡片支持自定义背景颜色、背景图片和银行 LOGO 图标，图片上传路径可在系统配置中管理。
- 卡片正面展示芯片、银行名称、卡号（每 4 位分组）和行号信息；背面展示磁条、签名区和账户余额（大号金额显示）。
- 单击卡片触发 3D 翻转查看余额，双击打开编辑弹窗修改账户信息。

### 库存模块

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
│  │  ├─ customers.py                # 客户、应收欠款与账户汇总接口
│  │  ├─ payment_receipts.py         # 收款单、附件、审核和反审核接口
│  │  ├─ settings.py                 # 系统配置、路径管理和目录浏览接口
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
│  │     │  ├─ UnifiedOrderList.vue  # 销售订单和物流订单列表
│  │     │  ├─ OrderForm.vue         # 订单录入和编辑表单
│  │     │  └─ ReturnOrderList.vue   # 退货订单列表
│  │     ├─ inventory/               # 仓库管理
│  │     ├─ customers/               # 客户管理
│  │     ├─ finance/
│  │     │  ├─ Receivables.vue        # 客户应收欠款汇总
│  │     │  ├─ PaymentHistory.vue     # 收款历史、收款单录入与审核
│  │     │  ├─ BankAccounts.vue       # 银行账户管理（卡片展示、翻转查看余额）
│  │     │  └─ ...                   # 物流、快递运费对账
│  │     ├─ system/                  # 用户、角色、门店和系统配置
│  │     │  └─ Settings.vue          # 系统参数配置（含银行卡图片路径配置）
│  │     └─ hr/                      # 人事报告
│  ├─ router/index.js                # 前端路由和登录守卫
│  ├─ utils/                         # Excel、日期、单位和通用工具
│  └─ assets/styles/                 # 本地全局样式
├─ data/
│  ├─ order_system.db                # 当前 SQLite 业务数据库
│  └─ backup_before_cleanup/         # 历史 JSON 备份
├─ docs/
│  ├─ API接口文档.md                 # 完整 API 参数、响应和业务规则
│  ├─ 后台列表页视觉与组件样式规范.md # 后台页面视觉和组件复用规范
│  ├─ 数据库表单说明.md              # 数据表说明
│  ├─ 银行账户管理-后端开发提示词.md  # 银行账户模块后端开发指引
│  └─ BUG及优化文档.md               # 问题与优化记录
├─ uploads/                          # 回单、收款附件、报告和银行卡图片等上传文件
│  └─ bank-cards/                    # 银行卡相关文件（由系统配置指定路径）
│     ├─ backgrounds/                # 银行卡背景图
│     └─ icons/                      # 银行 LOGO 图标
├─ frontend/                         # Flask/Docker 当前使用的生产静态文件
├─ dist/                             # Vite 默认构建输出
├─ frontend old/                     # 旧版前端，仅保留参考
├─ vite.config.js
├─ package.json
└─ README.md
```

## 财务与客户账户规则

### 账户口径

- `customers.initial_receivable` 保存客户期初欠款。
- `customers.receivable` 保存当前应收欠款，欠款始终使用正数。
- `customers.balance` 保存客户可用的预收储值余额。
- 客户账户净额按 `balance - receivable` 计算；结果为负数表示客户仍有欠款。
- `customer_account_transactions` 保存订单审核、收款审核及其反审核流水，用于后续对账和追溯。

### 销售订单审核

只有已发货、采用新数据结构并已关联客户的销售订单可以审核。审核后的页面状态显示为“已过帐”，并禁止修改、删除；反审核成功后恢复为“已发货”，重新允许修改和删除。

审核时先计算订单本次应收，再优先使用客户储值，剩余部分增加客户应收欠款：

```text
订单本次应收 = max(应收金额 - 本次已收, 0)
使用储值     = min(客户储值余额, 订单本次应收)
当前应收净增 = 订单本次应收 - 使用储值
```

应收欠款列表中的“增加应收”统计已审核订单的本次应收总额，“收回欠款”包含审核时使用的客户储值和后续收款中的现金核销，当前应收则直接读取客户账户的实时欠款。订单审核和反审核都会写入客户账户流水。若该订单形成的欠款已经被后续收款单核销，系统会阻止直接反审核，避免破坏对账链路。

### 收款单状态与入账

| 数据库状态 | 页面含义 | 是否影响客户账户 | 可执行操作 |
| --- | --- | --- | --- |
| `draft` | 待审核 | 否 | 审核、打印、修改、删除 |
| `audited` | 已审核 | 是 | 反审核、打印 |

收款单采用“先保存、后审核”模式。草稿中的核销额和预收额仅作为当前欠款下的计算预览，保存草稿不会改变客户应收欠款或储值余额。正式审核时会按客户最新账户余额重新计算，并在同一数据库事务中完成以下处理：

```text
优惠金额先抵减欠款
  -> 实际收款抵减剩余欠款
  -> 超出欠款的实收金额转为预收储值
  -> 更新客户账户
  -> 写入 customer_payment 流水
```

例如客户欠款 `2000.00` 元，收款 `2200.00` 元，优惠 `100.00` 元：最终核销欠款 `2000.00` 元，其中现金核销 `1900.00` 元，剩余 `300.00` 元转为客户预收储值。

反审核会恢复本单核销的欠款并扣回本单产生的预收储值。如果这部分预收储值已经被后续订单使用，系统会拒绝反审核。

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
| `/admin/orders/returns` | 退货订单 | 前端模拟数据（待接入后端 API） |
| `/admin/customers` | 客户管理 | `/api/customers` |
| `/admin/finance/receivables` | 应收欠款 | `/api/customers/receivables` |
| `/admin/finance/payment-history` | 收款历史 | `/api/payment-receipts` |
| `/admin/finance/bank-accounts` | 银行账户管理 | 前端模拟数据（待接入后端 API） |

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

## 财务关键接口

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/customers/receivables` | 查询客户期初欠款、应收增加、收回欠款、优惠和当前应收汇总 |
| `GET` | `/api/customers/:id/receivable` | 查询指定客户的当前应收欠款 |
| `PUT` | `/api/orders/:id` | 仅提交 `audit_state` 审核或反审核销售订单并联动客户账户 |
| `GET` | `/api/payment-receipts` | 查询收款单，可按门店、状态和关键词筛选 |
| `GET` | `/api/payment-receipts/next-number` | 按单据日期生成 `SKYYYYMMDDNNN` 收款单号 |
| `POST` | `/api/payment-receipts/attachments` | 上传收款附件图片 |
| `POST` | `/api/payment-receipts` | 新增待审核收款单 |
| `PUT` | `/api/payment-receipts/:id` | 修改待审核收款单 |
| `DELETE` | `/api/payment-receipts/:id` | 删除待审核收款单及其附件 |
| `POST` | `/api/payment-receipts/:id/audit` | 审核入账并更新客户欠款、储值和账户流水 |
| `DELETE` | `/api/payment-receipts/:id/audit` | 反审核并回退客户账户数据 |

销售订单审核请求体为 `{ "audit_state": 1 }`，反审核为 `{ "audit_state": 0 }`。收款附件仅支持 `jpg`、`jpeg`、`png`、`webp` 和 `gif`，整个 multipart 请求体不能超过 `10 MiB`。完整参数和响应示例见 [API 接口文档](docs/API接口文档.md#12-收款单与应收核销)。

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

客户财务核心表：

- `customers`：客户档案、期初欠款、当前应收欠款和预收储值余额
- `payment_receipts`：收款单草稿、审核状态以及核销和预收快照
- `customer_account_transactions`：订单审核、收款审核和反审核产生的客户账户流水

收款附件保存到 `uploads/payment-receipts/YYYY-MM/`，数据库仅保存附件访问地址。删除待审核收款单或替换附件时，后端会同步清理不再使用的文件。

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
- 后台列表、筛选栏、状态标签、表格、分页和弹窗优先遵循 [后台列表页视觉与组件样式规范](docs/后台列表页视觉与组件样式规范.md)。
- 提交代码前至少运行一次 `npm run build`。

## 部署说明

### 同源部署

生产环境前端请求使用相对路径 `/api`。建议由 Flask 或内网反向代理同时提供静态文件和 API，避免跨域及地址硬编码。

当前 Flask/Docker 容器读取 `frontend/`，而 Vite 默认输出到 `dist/`。Windows 环境构建并发布前端可执行：

```powershell
npm run build
Copy-Item -LiteralPath dist\index.html -Destination frontend\index.html -Force
Copy-Item -Path dist\assets\* -Destination frontend\assets -Force
docker restart my_order_app
```

发布后访问 `http://localhost:7899/api/health` 检查后端，再强制刷新浏览器确认加载了新的静态资源。更新数据库结构前应先备份 `data/order_system.db`。

### 离线部署

完整离线环境建议提前准备：

- 已安装的 `node_modules` 或内部 npm 镜像
- Python wheel 缓存或内部 pip 镜像
- 已构建的 Docker 镜像
- 已生成的前端静态文件
- SQLite 数据库备份

`backend/Dockerfile` 当前配置了在线 pip 镜像。严格断网环境下应使用预构建镜像，或把镜像源改为内网地址。

## 常见问题

### 保存收款单后客户欠款为什么没有变化

保存只创建 `draft` 待审核单据，不会入账。请在“收款历史”操作栏点击“审核”，审核成功后应收欠款、储值余额和客户账户流水才会同步更新。

### 收款单或销售订单为什么无法反审核

系统会保护已经发生后续业务的账户流水。收款单产生的预收储值被后续订单使用后不能直接反审核；销售订单形成的欠款被后续收款核销后也不能直接反审核。需要先按时间倒序撤销关联的后续业务。

### 收款单的结算账户为什么不能手工填写

结算账户根据所选客户归属门店自动生成，格式为“门店名称 + 结算账户”，用来避免收款单记入错误门店。收款方式仍可选填。

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
- [后台列表页视觉与组件样式规范](docs/后台列表页视觉与组件样式规范.md)
- [数据库表单说明](docs/数据库表单说明.md)
- [SQLite 迁移说明](MIGRATION_SQLITE.md)
- [SQLite 使用说明](README_SQLITE.md)
- [BUG 及优化记录](docs/BUG及优化文档.md)
