# 订单与进销存管理系统

基于 Vue 3、Vite、Pinia、Flask 和 SQLite 的内网业务管理系统，覆盖销售订单、物流出库、客户应收、收款历史、商品与原材料档案、供应商、仓库库存、入库审核、打印模板、回单和运费对账等流程。

系统采用前后端分离开发、同源部署的方式运行。所有前端资源均由本地项目构建，不依赖在线 CDN、Google Fonts 或在线图标库，适合纯内网和本地环境。

## 当前版本

| 项目 | 内容 |
| --- | --- |
| 应用版本 | `3.0.0`（以 `package.json` 为准） |
| 权限/API 文档版本 | `5.1` |
| 文档更新 | `2026-09-26` |
| 前端 | Vue 3、Vite 8、Pinia、Vue Router、Axios、XLSX、vue-print-designer |
| 后端 | Python、Flask、SQLite |
| 开发端口 | 前端 `3000`，后端 `7899` |
| API 前缀 | `/api` |
| 主数据库 | `data/order_system.db` |

## 主要功能

- 销售订单创建、编辑、复制、查询及状态流转
- 退货订单管理、退货单录入、审核、反审核及客户应收/库存联动
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
- 数据库打印模板、可视化设计、业务变量预览、浏览器打印和 C-Lodop 本地打印
- 首次部署超级管理员初始化、员工档案、登录账号和角色组管理
- 员工头像裁剪、缩放、上传、替换和物理文件清理
- 部门配置、员工多部门归属、部门员工维护和职位内联编辑
- 后台顶栏通讯录，支持部门折叠、员工搜索、头像、职位、电话和在线状态
- 后台路由权限、触屏操作权限、门店/仓库数据范围和登录设备管理
- 操作日志：记录账号安全、角色权限、员工部门及指定业务写操作，支持筛选和清空
- 物流复制字段设置：支持字段启停、删除、新增、排序、变量拖拽/点击插入和复制预览
- 原材料触屏出库、审核和库存流水

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

### 首次部署

1. 启动前后端并打开登录页。
2. 登录页请求 `GET /api/auth/bootstrap-status`。
3. 如果数据库中不存在“启用账号 + 启用全权限角色组”的超级管理员，页面显示创建超级管理员表单。
4. 输入管理员姓名、登录账号和至少 8 位密码完成初始化。
5. 初始化成功后创建入口关闭，后续只显示登录表单。

系统不再默认创建账号 `1` 或任何固定密码。判断条件是有效超级管理员是否存在，而不是用户表是否为空；如果数据库中仍有普通账号但超级管理员已被删除，初始化入口会重新开放。

## 项目结构

```text
order_system/
├─ backend/
│  ├─ app.py                         # Flask 入口、蓝图注册和静态文件服务
│  ├─ routes/
│  │  ├─ auth.py                     # 初始化、登录、退出、当前账号和密码修改
│  │  ├─ access.py                   # 权限目录、角色组、成员和数据范围
│  │  ├─ employees.py                # 员工档案和可选登录账号
│  │  ├─ departments.py              # 部门配置和部门员工数量
│  │  ├─ directory.py                # 后台通讯录与在线状态
│  │  ├─ messages.py                 # 一对一留言、已读状态和私有附件
│  │  ├─ notifications.py            # 当前员工的审核与系统通知
│  │  ├─ admin_realtime.py           # 留言和通知变化的 SSE 长连接
│  │  ├─ peer_transfers.py            # WebRTC 文件直传信令与状态机
│  │  ├─ operation_logs.py           # 操作日志筛选、分页读取与授权清空
│  │  ├─ logistics_copy.py          # 物流复制字段共享配置的读写接口
│  │  ├─ users.py                    # 账号维护和管理员重置密码
│  │  ├─ orders.py                   # 销售订单和物流状态接口
│  │  ├─ products.py                 # 成品、单位、属性和成品库存接口
│  │  ├─ raw_material_products.py    # 原材料商品档案接口
│  │  ├─ stock_inbounds.py           # 供应商、入库单、审核、库存余额和流水
│  │  ├─ material_outbounds.py        # 触屏原材料出库草稿、配置、审核和库存扣减
│  │  ├─ stores.py                   # 门店接口
│  │  ├─ warehouses.py               # 仓库接口
│  │  ├─ customers.py                # 客户、应收欠款与账户汇总接口
│  │  ├─ payment_receipts.py         # 收款单、附件、审核和反审核接口
│  │  ├─ settings.py                 # 系统路径和登录设备会话管理
│  │  ├─ print_templates.py          # 打印模板 CRUD、默认模板和历史模板迁移
│  │  ├─ freight.py                  # 运费与对账接口
│  │  └─ hr_reports.py               # 人事报告接口
│  ├─ utils/
│  │  ├─ auth.py                     # Session、权限装饰器和当前用户序列化
│  │  ├─ avatar_storage.py            # 员工头像校验、保存、删除和历史 Base64 迁移
│  │  ├─ access_scope.py             # 角色门店/仓库范围合并与数据过滤
│  │  ├─ permission_catalog.py       # 触屏、后台路由和销售订单操作权限目录
│  │  ├─ operation_logs.py           # 写操作审计规则、日志脱敏与自动记录
│  │  ├─ notifications.py            # 审核通知收件人匹配与完成处理
│  │  ├─ db.py                       # SQLite 连接、建表和结构升级
│  │  └─ db_helper.py                # 历史数据兼容读写
│  ├─ tools/                         # 数据备份等维护脚本
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ start.bat
├─ src/
│  ├─ api/
│  │  ├─ request.js                  # Axios 实例、Cookie 会话和统一响应处理
│  │  ├─ printTemplate.js            # 打印模板接口与字段标准化
│  │  └─ logisticsCopy.js            # 物流复制字段配置接口
│  ├─ stores/
│  │  ├─ user.js                     # 登录、用户和权限状态
│  │  ├─ order.js                    # 销售订单状态
│  │  ├─ orderDraft.js               # 销售订单草稿
│  │  ├─ stockDraft.js               # 入库单会话内存草稿
│  │  └─ nomi.js                     # 辅助工具状态
│  ├─ components/
│  │  ├─ CustomModal.vue             # 自定义通用弹窗组件（符合设计规范）
│  │  ├─ common/
│  │  │  ├─ StockInOrderModal.vue    # 原材料/成品共用入库弹窗
│  │  │  ├─ ConfirmModal.vue         # 通用确认弹窗
│  │  │  ├─ SearchOrderModal.vue     # 全局订单搜索
│  │  │  ├─ ShippedOrderActionModal.vue #物流发货-回单上传窗口
│  │  │  └─ NomiFloatingAI.vue       # nomi小人
│  │  ├─ admin/
│  │  │  ├─ AvatarCropper.vue        # 员工头像拖动、缩放和裁剪弹窗
│  │  │  ├─ DirectoryPanel.vue       # 后台通讯录搜索、部门折叠和员工状态
│  │  │  ├─ MessageInbox.vue         # 留言会话与审核通知双模式面板
│  │  │  ├─ ChatWindow.vue           # 可拖动的一对一留言和附件窗口
│  │  │  ├─ LogisticsCopySettingsDialog.vue # 物流复制字段、变量和预览设置
│  │  │  ├─ ProductFormModal.vue     # 成品/原材料共用档案弹窗
│  │  │  └─ StoreFormModal.vue       # 门店维护弹窗
│  │  ├─ print/
│  │  │  ├─ PrintDesignerEditor.vue  # 可视化模板设计器封装
│  │  │  ├─ PrintTemplateSelector.vue # 模板、打印方式和打印机选择
│  │  │  ├─ PrintClientSettingsDialog.vue # C-Lodop 服务与打印机设置
│  │  │  └─ OrderPrintPreview.vue    # 业务变量渲染、预览和打印
│  │  └─ front/                      # 前台订单、发货和原材料弹窗
│  ├─ views/
│  │  ├─ Admin.vue                   # 后台布局、菜单、入库弹窗和物流复制设置注册
│  │  ├─ MainView.vue                # 前台业务容器
│  │  ├─ front/                      # 订单、已出库和原材料流水页面
│  │  └─ admin/
│  │     ├─ products/
│  │     │  ├─ ProductList.vue       # 成品档案
│  │     │  ├─ MaterialProductList.vue
│  │     │  ├─ InventoryList.vue     # 成品库存
│  │     │  ├─ MaterialInventory.vue # 原材料库存及库存金额
│  │     │  ├─ MaterialOutboundList.vue # 原材料出库审核与触屏端配置
│  │     │  └─ StockRecordList.vue   # 入库/出库记录通用组件
│  │     ├─ sales/                   # 销售管理
│  │     │  ├─ UnifiedOrderList.vue  # 销售订单和物流订单列表
│  │     │  ├─ OrderForm.vue         # 订单录入和编辑表单
│  │     │  ├─ ReturnOrderList.vue   # 退货订单列表
│  │     │  ├─ ReturnOrderForm.vue   # 退货单录入和编辑表单
│  │     │  └─ CustomerList.vue      # 客户列表、编辑弹窗（支持期初欠款和储值管理）
│  │     ├─ purchase/                # 采购管理
│  │     │  ├─ PurchaseOrders.vue    # 采购订单
│  │     │  ├─ PurchaseInbound.vue   # 采购入库
│  │     │  └─ SupplierList.vue      # 供应商管理
│  │     ├─ inventory/               # 仓库管理
│  │     ├─ finance/
│  │     │  ├─ Receivables.vue        # 客户应收欠款汇总
│  │     │  ├─ PaymentHistory.vue     # 收款历史、收款单录入与审核
│  │     │  ├─ BankAccounts.vue       # 银行账户管理（卡片展示、翻转查看余额）
│  │     │  ├─ DebtDetails.vue        # 欠款详情页面（应收/应付通用，显示期初欠款和储值记录）
│  │     │  └─ ...                   # 物流、快递运费对账
│  │     ├─ system/                  # 角色组、门店、打印模板、操作日志和系统配置
│  │     │  ├─ RoleGroupManage.vue   # 权限、成员、会话策略和数据范围
│  │     │  ├─ Settings.vue          # 系统参数配置（含银行卡图片路径配置）
│  │     │  ├─ PrintTemplate.vue     # 打印模板管理
│  │     │  └─ OperationLogs.vue     # 操作日志筛选、分页、详情和清空
│  │     └─ hr/
│  │        ├─ AccountManage.vue     # 员工档案、可选登录账号和头像上传
│  │        ├─ DepartmentManage.vue  # 部门配置、员工归属和职位维护
│  │        └─ Reports.vue           # 人事检测报告
│  ├─ router/index.js                # 前端路由和登录守卫
│  ├─ utils/
│  │  ├─ accessControl.js            # 权限、角色并集和数据范围过滤
│  │  ├─ adminAccess.js              # 后台菜单分支和路由权限映射
│  │  ├─ adminRealtime.js            # 后台组件共享的 EventSource 客户端
│  │  ├─ peerFileTransfer.js          # WebRTC DataChannel 分块收发
│  │  ├─ logisticsCopy.js             # 物流复制字段、变量映射和格式化
│  │  ├─ lodopPrint.js               # C-Lodop 检测、打印机读取和打印输出
│  │  ├─ printClientConfig.js        # 本地打印配置和默认端口
│  │  ├─ chineseMoney.js             # 金额中文大写
│  │  └─ ...                         # Excel、日期、单位和通用工具
│  └─ assets/styles/                 # 本地全局样式
├─ data/
│  ├─ order_system.db                # 当前 SQLite 业务数据库
│  └─ backup_before_cleanup/         # 历史 JSON 备份
├─ docs/
│  ├─ API接口文档.md                 # 完整 API 参数、响应、权限和业务规则
│  ├─ 工作进度.md                    # 留言、附件与审核通知阶段进度
│  ├─ 打印机项目实现.md              # 打印模板、预览、浏览器打印和 C-Lodop 实现
│  ├─ 组件样式规范.md                 # 后台页面视觉和组件复用规范
│  ├─ 权限角色分组优化方案.md        # 账号、员工、角色组和数据范围设计
│  ├─ 银行账户管理-后端开发提示词.md  # 银行账户模块后端开发指引
│  └─ BUG及优化文档.md               # 问题与优化记录
├─ uploads/                          # 回单、头像、收款附件、报告和银行卡图片等上传文件
│  ├─ employee-avatars/              # 员工头像，内部继续按 YYYY-MM 分目录
│  ├─ chat-attachments/              # 私有聊天附件，必须通过鉴权接口下载
│  └─ bank-cards/                    # 银行卡相关文件（由系统配置指定路径）
│     ├─ backgrounds/                # 银行卡背景图
│     └─ icons/                      # 银行 LOGO 图标
├─ frontend/                         # Flask/Docker 当前使用的生产静态文件
├─ dist/                             # Vite 默认构建输出
├─ frontend old/                     # 旧版前端，仅保留参考
├─ vite.config.js
├─ package.json
├─ 版本更新日志.md
└─ README.md
```

## 权限与数据范围

### 身份关系

```text
员工档案 employees
  ├─ 可选登录账号 users
  ├─ employee_departments
  │    └─ 部门 departments（支持一名员工归属多个部门）
  └─ employee_roles
       └─ 角色组 roles
            ├─ role_permissions -> permissions
            ├─ role_stores -> stores
            └─ role_warehouses -> warehouses
```

员工可以没有登录账号，但登录账号必须绑定员工档案。员工可以同时归属多个部门，
`employee_departments` 的第一项为主部门。权限组成员维护使用员工 ID，因此可以先
建立员工档案、部门归属和岗位权限，之后再开通账号。部门归属不等于权限，权限组仍
通过 `employee_roles` 独立维护。

### 权限合并

- 多个角色组的权限编码取并集。
- 多个角色组的门店、仓库 ID 取并集，不会互相覆盖。
- 任一启用角色组具有 `full_access = 1` 时，账号为超级管理员并获得全部权限和全部数据范围。
- `canAccessAdmin` 只表示允许进入后台；后台具体大类仍需对应 `admin.route.*` 权限。
- `longSession` 只控制会话期限。任一角色启用后，该账号使用 365 天滑动续期；否则为 7 天。
- 未配置任何门店范围的非超级管理员不会看到门店订单，这不是“默认查看全部”。

### 集中接入

业务组件不要自行判断 `isSuperAdmin`、拼接角色权限或重复实现门店过滤。前端统一从 `useUserStore()` 获取当前账号，再调用：

```js
import {
  filterAccessibleOptions,
  filterRecordsByScope,
  hasPermission
} from '@/utils/accessControl'
```

后端接口必须使用权限装饰器，并在涉及门店或仓库数据时调用 `backend/utils/access_scope.py`。前端过滤用于界面体验，后端过滤才是数据安全边界。

## 财务与客户账户规则

### 账户口径

- `customers.initial_receivable` 保存客户期初欠款，`initial_receivable_at` 保存录入或最后修改时间。
- `customers.balance` 保存客户储值余额，`balance_at` 保存储值调整时间。
- `customers.receivable` 保存客户当前应收欠款，由期初欠款、订单欠款、收款和退货联动计算，欠款始终使用正数。
- 修改期初欠款时，应收欠款自动调整：`新应收 = 旧应收 - 旧期初欠款 + 新期初欠款`。
- 输入 0 或留空保存客户时，系统会清空对应的金额字段和时间戳字段。
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

### 原材料触屏出库

- 员工在前台触屏弹窗录入出库数量、成品数量和备注标签，提交后生成草稿，不立即扣减库存。
- 管理员在“库存 / 原材料出库”中审核草稿；审核会按先进先出扣减 `stock_balances` 并写入 `stock_movements`。
- 反审核会按原库存流水回补对应批次和库位。
- 默认门店、默认仓库、可操作原材料和默认原材料由原材料出库页面统一配置。
- 旧 `/api/materials` 使用/生产流水接口已经下线；库存统一由入库、出库审核和 `stock_movements` 维护。

## 主要页面

| 路由 | 页面 | 主要数据来源 |
| --- | --- | --- |
| `/admin/products` | 成品档案 | `/api/products` |
| `/admin/materials` | 原材料档案 | `/api/raw-material-products`、`/api/stock-balances` |
| `/admin/purchase/orders` | 采购订单 | 采购订单接口 |
| `/admin/purchase/suppliers` | 供应商管理 | `/api/suppliers` |
| `/admin/purchase/inbound` | 采购入库 | 入库接口 |
| `/admin/inventory` | 成品库存 | `/api/products/inventory` |
| `/admin/inventory/materials` | 原材料库存 | `/api/raw-material-products`、`/api/stock-balances`、`/api/stock-movements` |
| `/admin/inventory/material-outbounds` | 原材料出库审核与触屏配置 | `/api/material-outbounds`、`/api/material-outbound-settings` |
| `/admin/stock/in` | 入库记录 | `/api/stock-inbounds` |
| `/admin/stock/out` | 出库记录 | `/api/orders` |
| `/admin/inventory/warehouse` | 仓库管理 | `/api/warehouses` |
| `/admin/sales` | 销售订单 | `/api/orders` |
| `/admin/sales/returns` | 退货订单 | `/api/returns` |
| `/admin/sales/returns/create` | 新增退货单 | `/api/stores`、`/api/customers`、`/api/warehouses`、`/api/returns` |
| `/admin/sales/returns/edit/:id` | 修改退货单草稿 | `/api/returns/:id` |
| `/admin/customers` | 客户管理 | `/api/customers` |
| `/admin/finance/receivables` | 应收欠款 | `/api/customers/receivables` |
| `/admin/finance/payment-history` | 收款历史 | `/api/payment-receipts` |
| `/admin/finance/bank-accounts` | 银行账户管理 | `/api/bank-accounts`、`/api/upload/bank-*` |
| `/admin/finance/debt-details/:type/:targetId` | 欠款详情 | 前端模拟数据（待接入后端 API） |
| `/admin/system/print-template` | 打印模板管理和设计器 | `/api/print-templates` |
| `/admin/system/operation-logs` | 操作日志查询、筛选和清空 | `/api/admin/operation-logs` |
| `/admin/hr/employees` | 员工档案、登录账号和头像维护 | `/api/admin/employees`、`/api/admin/employees/:id/avatar` |
| `/admin/hr/departments` | 部门配置和部门员工管理 | `/api/admin/departments`、`/api/admin/employees` |

## 员工与头像关键接口

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/admin/employees` | 查询员工档案、部门、账号和头像路径 |
| `POST` | `/api/admin/employees` | 创建员工档案，可同时开通登录账号 |
| `PUT` | `/api/admin/employees/:id` | 修改员工档案、密码和账号状态 |
| `POST` | `/api/admin/employees/:id/avatar` | 上传或替换裁剪后的员工头像 |
| `DELETE` | `/api/admin/employees/:id/avatar` | 清空头像路径并删除受管物理文件 |
| `DELETE` | `/api/admin/employees/:id/account` | 解绑登录账号并保留员工档案 |

头像上传使用 `multipart/form-data`，文件字段名为 `avatar`。前端
`AvatarCropper.vue` 只负责浏览器内预览和裁剪，确认后把裁剪结果暂存在当前页面；
`AccountManage.vue` 保存员工成功后才调用头像接口。取消裁剪、关闭员工抽屉或未点击保存
都不会上传文件。完整请求和响应见
[API 接口文档](docs/API接口文档.md#16-员工档案和可选登录账号)。

## 操作日志关键接口

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/admin/operation-logs` | 按日期、操作人、模块、动作、结果和关键字读取日志 |
| `DELETE` | `/api/admin/operation-logs` | 清空历史日志并保留本次清空记录 |

日志页只读取写操作和账号安全事件；其自身的列表读取、筛选和详情查看不会生成日志。
销售单操作对象显示单据编号。完整参数、权限码和响应字段见
[API 接口文档](docs/API接口文档.md#18-操作日志)。

## 通讯录关键接口

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/admin/directory` | 查询启用部门、在职员工、头像、电话、职位和在线状态 |

通讯录接口只返回后台通讯录所需的公开联系信息，不返回身份证、家庭住址、紧急联系人
和账号权限等敏感字段。员工属于多个部门时会出现在对应的多个部门中，没有有效部门
归属的员工由前端归入“未分配部门”。

`online` 由服务端根据员工是否存在有效登录会话以及最近活动时间计算。当前在线窗口为
最近 `10` 分钟，服务端最多每 `5` 分钟更新一次会话活动时间。完整响应字段和在线规则见
[API 接口文档](docs/API接口文档.md#162-后台通讯录)。

## 留言与通知关键接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/api/admin/messages/conversations` | 最近会话、联系人和未读数 |
| `GET` | `/api/admin/messages/with/:employeeId/messages` | 查询并已读与指定员工的留言 |
| `POST` | `/api/admin/messages` | 发送文字留言 |
| `POST` | `/api/admin/messages/read-all` | 全部留言已读 |
| `POST` | `/api/admin/messages/attachments` | 上传最大 10MB 的私有附件 |
| `GET` | `/api/admin/messages/attachments/:id/download` | 会话参与者下载附件 |
| `GET` | `/api/admin/notifications` | 当前员工的审核通知 |
| `GET` | `/api/admin/realtime/events` | 留言和通知变化的 SSE 实时事件流 |
| `POST` | `/api/admin/peer-transfers` | 创建在线文件直传请求 |
| `GET` | `/api/admin/peer-transfers/pending` | 查询待接收的直传请求 |
| `POST` | `/api/admin/peer-transfers/:id/respond` | 同意或拒绝直传请求 |
| `POST` | `/api/admin/peer-transfers/:id/status` | 更新直传、完成、取消或失败状态 |
| `POST` | `/api/admin/notifications/:id/read` | 标记单条通知已读 |
| `POST` | `/api/admin/notifications/read-all` | 全部通知已读 |

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
| `GET` | `/api/bank-accounts` | 查询银行账户，可按门店筛选 |
| `GET` | `/api/bank-accounts/options` | 查询订单、收款单和退货单使用的结算账户选项（默认账户优先） |
| `POST` | `/api/bank-accounts` | 新增银行账户 |
| `PUT` | `/api/bank-accounts/:id` | 修改银行账户 |
| `DELETE` | `/api/bank-accounts/:id` | 删除未被业务单据引用的银行账户 |
| `POST` | `/api/upload/bank-card-background` | 上传银行卡背景图（不超过 5 MB） |
| `POST` | `/api/upload/bank-icon` | 上传银行图标（不超过 2 MB） |

银行账户图片目录由 `/api/settings/paths` 的 `bankCardBgPath` 和 `bankIconPath` 配置；数据库只保存 `/uploads/bank-cards/...` 访问路径。

## 退货单关键接口

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/returns` | 查询退货单列表，可按门店、客户和状态筛选 |
| `GET` | `/api/returns/:id` | 查询退货单及商品明细 |
| `POST` | `/api/returns` | 新增待审核退货单草稿，不影响客户和库存 |
| `PUT` | `/api/returns/:id` | 修改待审核退货单草稿 |
| `POST` | `/api/returns/:id/audit` | 审核退货单，核销客户应收并返还库存 |
| `POST` | `/api/returns/:id/reverse-audit` | 反审核，恢复客户应收并回退库存 |
| `DELETE` | `/api/returns/:id` | 删除待审核草稿；已审核单据需先反审核 |

退货单状态为 `draft`（待审核）和 `audited`（已审核），`completed` 仅用于兼容历史已入账数据。保存、修改、审核、反审核和删除均在后端事务中执行，避免只更新客户账户或只更新库存的半成功状态。

销售订单审核请求体为 `{ "audit_state": 1 }`，反审核为 `{ "audit_state": 0 }`。收款附件仅支持 `jpg`、`jpeg`、`png`、`webp` 和 `gif`，整个 multipart 请求体不能超过 `10 MiB`。完整参数和响应示例见 [API 接口文档](docs/API接口文档.md#12-收款单与应收核销)。

## 打印模板与打印客户端

打印功能分成服务器模板和客户端打印配置两部分。

### 服务器模板

模板数据保存在 SQLite 的 `print_templates` 表，所有用户共享：

```text
模板名称
业务类型
纸张类型和毫米尺寸
是否默认
是否启用
vue-print-designer 设计 JSON
```

关键接口：

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/print-templates` | 查询模板，可按业务类型和启用状态过滤 |
| `GET` | `/api/print-templates/:id` | 获取完整模板 |
| `POST` | `/api/print-templates` | 新建模板 |
| `PUT` | `/api/print-templates/:id` | 更新模板元数据和设计 JSON |
| `DELETE` | `/api/print-templates/:id` | 删除非默认模板 |
| `POST` | `/api/print-templates/:id/set-default` | 设置同业务类型默认模板 |
| `POST` | `/api/print-templates/migrate` | 迁移旧 localStorage 模板 |

GET 响应使用数据库下划线字段，`src/api/printTemplate.js` 会标准化为前端驼峰字段。完整请求和响应见 [API 接口文档](docs/API接口文档.md#16-打印模板管理)。

### 前端组件结构

| 组件 | 职责 |
| --- | --- |
| `PrintDesignerEditor.vue` | 编辑模板、变量、表格和纸张尺寸 |
| `PrintTemplateSelector.vue` | 按业务类型选择模板和打印方式 |
| `PrintClientSettingsDialog.vue` | 设置浏览器/C-Lodop、端口和打印机 |
| `OrderPrintPreview.vue` | 将模板和业务变量生成统一预览 HTML |
| `lodopPrint.js` | 将预览 HTML 交给浏览器或 C-Lodop |
| `printClientConfig.js` | 读取、校验和保存当前电脑的打印配置 |

业务页面只负责把原始单据转换为统一打印变量。不要在每个页面重复实现模板读取、C-Lodop 检测或打印 HTML 生成。

### 客户端本地配置

以下配置只属于当前电脑和浏览器：

```text
browser/clodop 打印方式
C-Lodop 协议、主机和端口
本地打印机名称
```

localStorage 键：

```text
order-system-print-client-config
```

首次使用默认采用 C-Lodop，主机为 `localhost`。HTTP 页面默认端口 `8000`，HTTPS 页面默认端口 `8443`，打印机名称需要检测后选择。

## 物流复制字段设置

物流复制字段设置保存在 SQLite，所有后台账号读取同一份配置。
后台用户可以在顶栏通知区域旁打开设置弹窗，配置物流列表复制文本的字段、名称、模板和顺序。

### 组件职责

| 文件 | 职责 |
| --- | --- |
| `src/components/admin/LogisticsCopySettingsDialog.vue` | 配置弹窗、字段编辑、变量插入、拖拽、排序、删除和实时预览 |
| `src/utils/logisticsCopy.js` | 默认字段、变量目录、订单变量映射和复制文本格式化 |
| `src/api/logisticsCopy.js` | 配置读取和保存 API |
| `backend/routes/logistics_copy.py` | 后台鉴权、字段校验和配置读写 |
| `src/views/Admin.vue` | 注册顶栏入口和弹窗组件 |
| `src/views/admin/sales/UnifiedOrderList.vue` | 在物流列表调用统一格式化方法并执行复制 |

### 配置保存

设置面板通过 `GET /api/settings/logistics-copy` 读取，点击保存时调用 `PUT /api/settings/logistics-copy`，后端在 `logistics_copy_settings.fields_json` 中保存有序字段数组。首次无配置时使用内置默认值；每次物流列表点击复制均从服务器读取最新配置。读写需要后台访问权限，读取失败不会复制旧缓存。旧版 `admin_logistics_copy_fields` 本地数据不再使用或自动迁移。

每个字段至少包含以下结构：

```json
{
  "key": "receiver_name",
  "name": "姓名",
  "template": "姓名：@receiverName",
  "enabled": true
}
```

字段属性说明：

| 属性 | 说明 |
| --- | --- |
| `key` | 字段唯一标识，内置字段不能重复；自定义行使用 `custom_` 前缀 |
| `name` | 设置面板中显示的字段名称 |
| `template` | 实际复制的文本模板，可以包含普通文字和变量 |
| `enabled` | 是否输出到复制结果 |
| `custom` | 是否为用户新增的自定义行 |

保存设置时会进行字段规范化：清理无效字段和重复字段、补齐必要的字段结构，
并按照当前编辑顺序保存。删除的内置字段不会在下次打开时自动恢复；点击“恢复默认”
才会重新加载全部内置字段。

### 变量模板

变量可以通过点击插入，也可以从变量字段区域拖动到左侧模板编辑框。当前变量目录如下：

| 分类 | 变量 |
| --- | --- |
| 订单信息 | `storeName`、`orderNumber`、`orderDate`、`customerName`、`warehouseName`、`projectName` |
| 收货信息 | `receiverName`、`receiverPhone`、`receiverAddress` |
| 联系人信息 | `contactPerson`、`contactPhone`、`contactAddress` |
| 商品信息 | `goodsName`、`spec`、`unit`、`allGoods`、`allSpecs`、`allQuantity`、`goodsWeight`、`goodsQuantity`、`totalQuantity`、`totalPackages`、`goodsPackaging` |
| 物流信息 | `logisticsService`、`shippingMethod`、`logisticsNo`、`shippedDate`、`freightTotal` |
| 其他 | `salesPerson`、`creator`、`orderRemark`、`discountAmount`、`otherFees`、`totalAmount`、`totalTaxAmount`、`currentPayment`、`currentDebt`、`settlementAccount`、`shouldReceive`、`amountInWords` |

推荐使用 `@变量名` 语法，例如：

```text
姓名：@receiverName
电话：@receiverPhone
商品：@goodsName
```

格式化器同时兼容旧配置中的 `{变量名}` 语法。变量没有值时会替换为空字符串；
如果一个模板只包含变量且所有变量都为空，该行会被跳过。纯文字模板不会因为没有变量
而被过滤。最终复制结果按字段顺序换行，并在有内容时追加结尾换行。

### 默认数据映射

物流列表复制时由 `formatLogisticsOrderForCopy()` 统一生成变量：

- 标题使用门店名称生成 `【门店订单】`。
- 收货人、电话和地址优先读取物流信息，缺失时回退到订单联系人信息。
- 商品名称优先读取第一条商品明细，并组合规格。
- 重量、件数、包装、物流服务、发货方式、物流单号和发货日期从订单及物流字段转换。
- 运费从运费明细合计生成，金额变量来自订单打印变量。
- 同时保留历史下划线变量别名，兼容早期保存的模板。

复制按钮只负责调用统一格式化结果并写入系统剪贴板，不应在业务列表组件中重新拼接
姓名、电话、地址等固定文本。新增变量时，应同时更新 `LOGISTICS_COPY_VARIABLE_GROUPS`
和 `getLogisticsCopyValues()`。

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
- `bank_accounts`：门店银行账户、卡片样式、图片访问路径和余额
- `return_orders`：退货单头、实退金额、退款金额、审核状态和客户流水关联
- `return_order_items`：退货商品、仓库、数量、单价、税额和备注明细
- `customer_account_transactions`：订单审核、收款审核和反审核产生的客户账户流水
- `print_templates`：打印模板元数据、纸张尺寸和设计器 JSON

账号权限核心表：

- `users`：登录账号、密码哈希、状态、权限版本和最后登录时间
- `employees`：员工主档及可选账号关联
- `departments`：部门名称、上下级关系、启停状态和排序
- `employee_departments`：员工与部门的多对多关系及主部门标记
- `roles`：角色组、后台访问、长会话和全权限标记
- `permissions`、`role_permissions`：权限目录和角色权限关系
- `employee_roles`：员工与角色组关系
- `role_stores`、`role_warehouses`：角色组门店和仓库范围
- `auth_sessions`：设备会话、IP、活动时间、到期时间和撤销状态
- `operation_logs`：操作人快照、模块/动作、目标单据、来源、请求元数据和结果

退货单审核会在 `stock_balances`、`stock_movements` 中留下可追溯的库存返还记录；反审核按退货单号删除对应库存流水并恢复审核前库存。

收款附件保存到 `uploads/payment-receipts/YYYY-MM/`，数据库仅保存附件访问地址。删除待审核收款单或替换附件时，后端会同步清理不再使用的文件。

员工头像保存到 `uploads/employee-avatars/YYYY-MM/`。`employees.avatar_url` 和绑定账号的
`users.avatar_url` 保存同一个 `/uploads/employee-avatars/...` 访问路径，不保存 Base64
图片内容。替换或删除头像时只会删除该目录中的受管文件，并限制文件操作不能越过头像
根目录。

`data/backup_before_cleanup/` 中的 JSON 文件仅用于历史迁移和备份参考，当前业务接口以 SQLite 为准。

打印模板本身保存在 SQLite；C-Lodop 地址、端口和打印机名称保存在每台客户端浏览器的 `localStorage`，不会随数据库备份迁移到其他电脑。

修改或替换数据库前，应先停止后端服务并备份 `data/order_system.db`，避免正在运行的进程继续写入。

## 前端开发约定

- 页面和组件使用 Vue 3 `<script setup>`。
- 页面级组件放在 `src/views/`，可复用弹窗放在 `src/components/`。
- 组件样式优先使用 `<style scoped>`，公共样式放在 `src/assets/styles/`。
- API 请求统一使用 `src/api/request.js`，接口地址保持 `/api` 相对路径。
- 登录和身份统一依赖服务端 Session Cookie，禁止重新增加 `Username`、`Role` 等客户端身份请求头。
- 页面权限、角色并集和数据范围统一使用 `src/utils/accessControl.js`；后台菜单与路由权限映射统一使用 `src/utils/adminAccess.js`。
- 后端权限校验统一使用 `backend/utils/auth.py` 的装饰器，门店/仓库数据过滤统一使用 `backend/utils/access_scope.py`。
- 打印模板请求统一使用 `src/api/printTemplate.js`，页面不要直接处理后端下划线字段。
- 打印弹窗、预览和 C-Lodop 设置统一复用 `src/components/print/`，不要在业务页面复制实现。
- 业务单据必须先转换为统一打印变量，再交给 `OrderPrintPreview.vue` 渲染。
- 打印模板保存到服务器；只与本机相关的打印服务和打印机配置才允许保存到 `localStorage`。
- 临时表单状态使用 Pinia；需要跨刷新保存的数据必须明确设计持久化方案。
- 不引入在线 CDN、远程字体或在线矢量图标。
- 金额和数量显示使用千分位、固定精度和 `tabular-nums`。
- 后台列表、筛选栏、状态标签、表格、分页和弹窗优先遵循 [后台列表页视觉与组件样式规范](docs/组件样式规范.md)。
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

### 第一次部署的默认账号和密码是什么

没有默认账号和密码。数据库不存在有效超级管理员时，登录页会显示初始化表单，由现场管理员创建首个超级管理员。初始化完成后表单自动关闭。

### 为什么员工已经有账号但看不到后台菜单

角色组需要同时启用 `canAccessAdmin` 和对应的 `admin.route.*` 权限。`canAccessAdmin` 只允许进入后台，不代表自动拥有全部后台页面。

### 为什么销售订单列表没有数据或没有门店滑块

先检查员工所属角色组的门店范围。非超级管理员只会收到授权门店的订单；没有门店权限时列表为空，只有一个门店时不显示门店滑块，两个及以上门店时才显示选择器。

### 为什么重复登录没有新增设备行

登录请求会携带浏览器或触屏设备持久化的 `device.id`。同一账号和同一设备再次登录时，
系统会更新原会话记录并刷新 token、最近活动和到期时间；只有更换设备 ID，或登录时没有
提交设备 ID，才会新增独立会话记录。设备类型中的 `admin`/`touch` 表示账号是否拥有
后台访问能力，不表示当前使用的是哪条前端路由。

### 一个员工可以同时属于多个部门吗

可以。员工档案中使用部门多选，部门关系保存在 `employee_departments`，第一项是主部门，
其余是兼任部门。部门管理页面可以从当前部门移除员工或修改其职位；这些操作不会自动
改变角色组、后台访问权限或门店/仓库数据范围。

### 同一员工加入多个角色组会不会冲突

权限、门店和仓库范围都取并集；任一角色允许后台访问或长会话，对应能力即生效；任一角色是全权限角色时账号获得完整权限。角色不会按先后顺序互相覆盖。

### 保存收款单后客户欠款为什么没有变化

保存只创建 `draft` 待审核单据，不会入账。请在“收款历史”操作栏点击“审核”，审核成功后应收欠款、储值余额和客户账户流水才会同步更新。

### 收款单或销售订单为什么无法反审核

系统会保护已经发生后续业务的账户流水。收款单产生的预收储值被后续订单使用后不能直接反审核；销售订单形成的欠款被后续收款核销后也不能直接反审核。需要先按时间倒序撤销关联的后续业务。

### 结算账户从哪里来

结算账户来自“银行账户”页面中当前门店的账户配置。订单、收款单和退货单会按门店过滤下拉选项，并自动带出该门店的默认账户；没有默认账户时回退到该门店第一条账户。如果门店暂未配置银行账户，仍兼容历史的“门店名称 + 结算账户”文字。

### 银行账户余额什么时候变化

草稿保存和修改不会改变银行账户余额。审核销售订单或收款单时增加实际收款，退货单审核时仅按“本次退款”减少余额；反审核会回退相反金额。实退金额用于核销客户应收，不等同于现金退款。

### 提交入库单后库存没有变化

提交审核只创建待审核单据。请进入“入库记录”，打开单据抽屉并点击“审核”。只有审核接口成功返回后，库存才会增加。

### 保存退货单后客户欠款和库存没有变化

退货单保存只是创建 `draft` 待审核草稿，不会入账或返还库存。请在退货订单列表点击“审核”；审核成功后才会按实退货金额核销客户应收，并按商品明细返还对应门店和仓库库存。

### 退货单为什么不能修改或删除

`audited`（以及兼容历史 `completed`）单据已经写入客户流水和库存流水，系统会隐藏修改、删除操作。先点击“反审核”恢复为 `draft`，确认客户应收和库存恢复后再修改或删除。

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

### 打印模板为什么换一台电脑后仍然存在

模板已经保存到 SQLite，通过 `/api/print-templates` 读取，因此登录同一个系统的其他电脑也能看到模板。

### 为什么换一台电脑后需要重新选择打印机

C-Lodop 地址、端口和打印机名称只保存在当前浏览器的 `localStorage`。每台电脑安装的打印机和驱动不同，所以这些配置不会上传服务器。

### 第一次部署是否有 C-Lodop 端口

有。HTTP 页面默认使用 `localhost:8000`，HTTPS 页面默认使用 `localhost:8443`。默认地址不代表服务一定已经启动，首次打印仍需检测 C-Lodop 并选择本地打印机。

## 相关文档

- [版本更新日志](版本更新日志.md)
- [API 接口文档](docs/API接口文档.md)
- [打印机项目实现](docs/打印机项目实现.md)
- [后台列表页视觉与组件样式规范](docs/组件样式规范.md)
- [权限角色分组优化方案](docs/权限角色分组优化方案.md)
- [BUG 及优化记录](docs/BUG及优化文档.md)

## 版本更新日志

完整版本更新记录见 [版本更新日志](版本更新日志.md)。

