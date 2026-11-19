import { ADMIN_ROUTE_BRANCH_PERMISSIONS as permissions } from '@/utils/adminAccess'
import { ADMIN_PURCHASE_ORDER_PERMISSIONS, ADMIN_SALES_ORDER_PERMISSIONS } from '@/utils/accessControl'

const step = (target, title, description, options) => ({ target, title, description, ...options })
const action = (target, title, description, options) => step(target, title, description, { actionTarget: target, ...options })

const formModal = { layer: 2147483000 }
const mobileModal = { layer: 100001 }
const stockModal = { layer: 2147483001 }
const bankModal = { layer: 100000 }

const productSteps = [
  action('product-add', '打开物品表单', '点击高亮的新增按钮，或点击引导的「下一步」。'),
  step('product-stores', '选择可用门店', '勾选可使用该物品的门店。列表为空时，请先新建并启用门店。'),
  step('product-warehouse', '选择仓库和分类', '选择门店所属的仓库，再选分类。没有可用选项时，先在「仓库管理」添加仓库和分类。'),
  step('product-name', '填写物品名称', '名称必填。编号、规格型号和备注按实际情况填写。'),
  step('product-unit', '设置基本计量单位', '点击单位名称选中。没有对应单位时，可点「＋ 新增」添加。'),
  step('product-save', '保存物品档案', '点击「保存」。需要登记库存数量时，再从「新建入库单」开始。')
]

const purchaseOrderForm = { routeName: 'admin-purchase-order-create' }
const inboundForm = { routeName: 'admin-purchase-inbound-create' }
const salesForm = { routeName: 'admin-sales-create' }

const salesEntry = action('sales-add', '进入新增订单', '点击高亮的新增按钮，或点击引导的「下一步」。')
const salesSteps = [
  salesEntry,
  step('document-store', '选择门店', '选择销售业务所属的门店，客户和仓库选项会随门店切换。', salesForm),
  step('document-customer', '选择客户和仓库', '在客户框输入名称并从结果中选择，再选择出库仓库。', salesForm),
  step('document-contact', '核对联系人和电话', '确认带出的联系人和联系电话。缺少的必填信息可在单据上补齐。', salesForm),
  step('document-product', '录入商品明细', '在明细中搜索并选择成品，再录入大于 0 的数量。按实际业务填写件数、单价和税率，点「＋」可加行。', salesForm),
  step('document-save', '保存销售单', '核对客户、商品和本次收款。点击「保存并打印」保存单据并打开打印模板选择。', salesForm)
]

const mobileSalesSteps = [
  salesEntry,
  action('mobile-order-store', '选择门店', '点选销售归属的门店。如果列表为空，请先新建并启用门店。', {
    ...mobileModal, actionTarget: 'mobile-order-store-next'
  }),
  action('mobile-order-warehouse', '选择客户和仓库', '先从上方选择客户，再指定出库仓库。选齐后可点击表单底部「开始填写」。', {
    ...mobileModal, actionTarget: 'mobile-order-start'
  }),
  step('mobile-order-contact', '核对收货信息', '核对客户带出的收货人和联系电话，缺少时可直接补齐。'),
  action('mobile-order-add-item', '添加商品明细', '点击「新增商品」，打开商品明细弹窗。'),
  action('mobile-order-item', '选择商品并填写数量', '搜索并选中商品，填写正数数量，再按实际情况补充件数和单价。点「修改完成」返回单据。', {
    ...mobileModal,
    actionTarget: 'mobile-order-item-apply',
    advanceTarget: 'mobile-order-item-added',
    waitForClose: true
  }),
  step('mobile-order-submit', '提交销售订单', '确认收货信息、商品数量和金额后，点击「完成提交」保存订单。')
]

export const tutorialTopics = [
  {
    id: 'store',
    title: '新建门店',
    location: '设置 → 门店管理',
    routeName: 'admin-stores',
    permissions: [permissions.SYSTEM.STORES],
    steps: [
      action('store-add', '打开门店表单', '点击「新增门店」，或点击引导的「下一步」。'),
      step('store-code', '填写门店编码', '为门店填写唯一编码，只使用字母、数字和下划线。编码创建后不可修改。'),
      step('store-name', '填写门店名称', '填写员工容易辨认的门店名称。保持「启用」即可在后续业务中选择该门店。'),
      step('store-save', '保存门店', '核对编码和名称后，点击「保存」。')
    ]
  },
  {
    id: 'warehouse',
    title: '新建仓库',
    location: '库存 → 仓库管理',
    routeName: 'admin-inventory-warehouse',
    permissions: [permissions.INVENTORY.WAREHOUSE],
    steps: [
      step('warehouse-store', '先选所属门店', '从「选择门店」下拉框选中一个启用的门店。若没有可选门店，请先完成「新建门店」。'),
      action('warehouse-add', '打开仓库表单', '点击「新增仓库」进入所选门店的仓库表单。'),
      step('warehouse-code', '填写仓库 ID 和名称', '填写仓库 ID，再填写仓库名称。所属门店沿用上一步的选择。'),
      step('warehouse-save', '保存仓库', '点击「保存」。建好后，可以用仓库卡片上的「新增分类」设置物品分类。')
    ]
  },
  {
    id: 'product',
    title: '新建物品（成品）',
    shortTitle: '成品',
    location: '库存 → 成品库存',
    routeName: 'admin-inventory',
    permissions: [permissions.INVENTORY.PRODUCTS],
    steps: productSteps
  },
  {
    id: 'material',
    title: '新建物品（原材料）',
    shortTitle: '原材料',
    location: '库存 → 原材料库存',
    routeName: 'admin-inventory-materials',
    permissions: [permissions.INVENTORY.MATERIALS],
    steps: productSteps
  },
  {
    id: 'supplier',
    title: '新建供应商',
    location: '采购 → 供应商管理',
    routeName: 'admin-purchase-suppliers',
    permissions: [permissions.PURCHASE.SUPPLIERS],
    steps: [
      action('supplier-add', '打开供应商表单', '点击「新增供应商」，或点击引导的「下一步」。'),
      step('supplier-store', '设置供应商归属', '可指定所属门店。多门店共用的供应商可选择「通用供应商」。', formModal),
      step('supplier-required-fields', '填写供应商名称', '供应商名称必填。编号选填，填写时要保持唯一。联系人、电话和结算资料可按需填写。', formModal),
      step('supplier-submit', '创建供应商', '核对资料后点击「创建」。', formModal)
    ]
  },
  {
    id: 'customer',
    title: '新建客户',
    location: '销售 → 客户列表',
    routeName: 'admin-customers',
    permissions: [permissions.SALES.CUSTOMERS],
    steps: [
      action('customer-add', '打开客户表单', '点击「新增客户」，或点击引导的「下一步」。'),
      step('customer-store', '选择所属门店', '核对默认门店，或选择对应门店。如果列表为空，请先完成「新建门店」。', formModal),
      step('customer-required-fields', '填写客户名称和编号', '客户名称和编号都必填，编号需唯一。联系人、电话和财务信息可按需填写。', formModal),
      step('customer-submit', '创建客户', '核对资料后点击「创建」。', formModal)
    ]
  },
  {
    id: 'purchase-order',
    title: '新建采购订单',
    location: '采购 → 采购订单',
    routeName: 'admin-purchase-orders',
    permissions: [permissions.PURCHASE.ORDERS, ADMIN_PURCHASE_ORDER_PERMISSIONS.CREATE],
    steps: [
      action('purchase-order-add', '打开采购申请', '在采购订单页点击「新增采购单」。'),
      step('document-store', '选择申请门店', '选择申请门店，并确认申请日期。预计到货日期可一起填写。', purchaseOrderForm),
      step('document-item-warehouse', '选择明细仓库和商品', '先为明细选择仓库和分类，再搜索并选中商品，填写大于 0 的申请数量。', purchaseOrderForm),
      step('document-invoice', '确认发票要求', '保留「需要发票」时，填写含税单价和税点，系统会计算含税金额。无需发票时可取消勾选。', purchaseOrderForm),
      step('document-order-actions', '保存草稿或提交审核', '可以先保存草稿。核对申请和金额后，点击「提交审核」交给审核人员。', purchaseOrderForm)
    ]
  },
  {
    id: 'purchase-inbound',
    title: '新建入库单',
    location: '采购 → 采购入库申请',
    routeName: 'admin-purchase-inbound',
    permissions: [permissions.PURCHASE.INBOUND],
    steps: [
      action('purchase-inbound-add', '打开进货单', '在采购入库申请页点击「新增入库单」。'),
      step('document-store', '选择门店和仓库', '按实际到货选择门店、仓库和入库日期。页面提供「入库类型」时，按成品或原材料切换。', inboundForm),
      step('document-product', '选择入库物品', '从明细下拉列表选中物品。需要多条时，可用行首的「＋」添加明细。', inboundForm),
      step('document-batch', '填写实收数量和批次号', '逐行填写实收数量和批次号。应收数量和货位编码按实际情况填写。', inboundForm),
      step('document-save', '保存进货单', '确认本次实际到货的数据后，点击「保存并打印」。独立进货单保存后会登记库存。', inboundForm)
    ]
  },
  {
    id: 'stock-inbound',
    title: '新建入库单（库存记录）',
    location: '库存 → 入库记录',
    routeName: 'admin-stock-in',
    permissions: [permissions.INVENTORY.STOCK_IN],
    steps: [
      action('stock-in-add', '打开入库单弹窗', '在入库记录页点击「新增入库单」。'),
      step('stock-in-warehouse', '填写单据基本信息', '核对单据日期，选中门店、目标仓库和供应商。', stockModal),
      step('stock-in-product', '填写原材料入库明细', '选择物料，再填写大于 0 的实收数量和批次号。缺少行时点「添加物料行」。', stockModal),
      step('stock-in-submit', '提交入库单审核', '点击「提交审核」登记待审核单据，审核通过后增加库存。', stockModal)
    ]
  },
  {
    id: 'sale',
    title: '新建销售订单',
    location: '销售 → 销售订单',
    routeName: 'admin-sales',
    permissions: [permissions.SALES.ORDERS, ADMIN_SALES_ORDER_PERMISSIONS.CREATE],
    steps: salesSteps,
    mobileSteps: mobileSalesSteps
  },
  {
    id: 'bank-account',
    title: '新建银行账户',
    location: '财务 → 银行账户',
    routeName: 'admin-finance-bank-accounts',
    permissions: [permissions.FINANCE.BANK_ACCOUNTS],
    steps: [
      action('bank-account-add', '打开银行账户表单', '点击「录入账户」，或点击引导的「下一步」。'),
      step('bank-account-store', '选择账户所属门店', '选择使用该银行账户的门店。列表为空时，请先完成「新建门店」。', bankModal),
      step('bank-account-number', '填写银行账户资料', '填写账户名称、账号和开户行。银行行号可按实际资料填写。', bankModal),
      step('bank-account-balance', '核对账户余额', '填写录入时的实际余额。需要设为该门店默认结算账户时，勾选「默认账户」。', bankModal),
      step('bank-account-submit', '添加银行账户', '再次核对账号、开户行和余额后，点击「添加」。', bankModal)
    ]
  }
]
