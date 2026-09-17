<template>
  <div v-if="visible" class="print-designer-shell">
    <div class="print-designer-toolbar">
      <div class="designer-title">
        <input
          v-model="templateName"
          class="designer-name-input"
          aria-label="模板名称"
          placeholder="模板名称"
        />
        <small>210mm × 140mm · 三联单打印 1 份</small>
      </div>
      <div class="designer-actions">
        <button type="button" class="designer-btn" @click="handlePreview">预览</button>
        <button type="button" class="designer-btn designer-btn-primary" @click="handleSave">
          保存模板
        </button>
        <button type="button" class="designer-btn" @click="handleClose">退出</button>
      </div>
    </div>
    <div class="print-designer-canvas">
      <print-designer ref="designerRef" @ready="configureDesigner"></print-designer>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import 'vue-print-designer'
import 'vue-print-designer/style.css'
import { toChineseMoney } from '@/utils/chineseMoney'

const props = defineProps({
  visible: { type: Boolean, default: false },
  template: { type: Object, default: null }
})

const emit = defineEmits(['save', 'close'])
const designerRef = ref(null)
const templateName = ref('')
const configured = ref(false)

const defaultVariables = {
  storeId: 'store-001',
  storeName: '示例门店',
  customerId: 'customer-001',
  customerName: '示例客户',
  warehouseId: 'warehouse-001',
  warehouseName: '默认仓库',
  orderDate: '2026-09-13',
  orderNumber: 'ZG20260913001',
  orderNo: 'ZG20260913001',
  contactPerson: '张三',
  contactPhone: '13800000000',
  contactAddress: '浙江省杭州市示例地址',
  projectName: '示例工程项目',
  logisticsService: '送货上门',
  goodsPackaging: '袋装',
  packaging: '袋装',
  salesPerson: '柯晓',
  creator: '下单员',
  orderRemark: '这是订单备注',
  taxEnabled: true,
  taxRate: 13,
  totalPackages: 2,
  totalQuantity: 100,
  totalAmount: '1250.00',
  totalTaxAmount: '1412.50',
  discountAmount: '1250.00',
  otherFees: '0.00',
  settlementAccount: '默认结算账户',
  customerReceivable: '0.00',
  shouldReceive: '1250.00',
  amountInWords: toChineseMoney('1250.00'),
  currentPayment: '1250.00',
  currentDebt: '0.00',
  items: [
    {
      index: 1,
      productId: 'product-001',
      goodsName: '示例商品',
      spec: '标准规格',
      unit: '公斤',
      warehouseId: 'warehouse-001',
      warehouseName: '默认仓库',
      currentStock: 1000,
      baseUnitId: 'unit-kg',
      conversionRate: 50,
      unitConversions: [{ unit: '袋', value: 50 }],
      packages: 2,
      quantity: 100,
      price: 12.5,
      taxRate: 13,
      taxIncludedPrice: 14.13,
      amount: 1250,
      totalAmount: 1412.5,
      remark: '商品备注'
    }
  ]
}

const availableVariables = [
  {
    id: 'orderInfo',
    label: '订单信息',
    children: [
      { id: 'orderNumber', label: '单据编号' },
      { id: 'orderNo', label: '订单号（兼容别名）' },
      { id: 'orderDate', label: '单据日期' },
      { id: 'storeName', label: '门店名称' },
      { id: 'customerName', label: '客户名称' },
      { id: 'warehouseName', label: '仓库名称' },
      { id: 'storeId', label: '门店ID' },
      { id: 'customerId', label: '客户ID' },
      { id: 'warehouseId', label: '仓库ID' }
    ]
  },
  {
    id: 'contactInfo',
    label: '联系人信息',
    children: [
      { id: 'contactPerson', label: '联系人' },
      { id: 'contactPhone', label: '联系方式' },
      { id: 'contactAddress', label: '联系地址' },
      { id: 'projectName', label: '工程项目' }
    ]
  },
  {
    id: 'businessInfo',
    label: '业务信息',
    children: [
      { id: 'logisticsService', label: '物流服务' },
      { id: 'goodsPackaging', label: '包装方式' },
      { id: 'packaging', label: '包装' },
      { id: 'salesPerson', label: '业务员' },
      { id: 'creator', label: '制单人' },
      { id: 'orderRemark', label: '订单备注' }
    ]
  },
  {
    id: 'items',
    label: '商品明细（用于表格数据变量）',
    isArray: true,
    children: [
      { id: 'index', label: '序号' },
      { id: 'productId', label: '商品ID' },
      { id: 'goodsName', label: '商品信息' },
      { id: 'spec', label: '规格型号' },
      { id: 'unit', label: '单位（公斤/吨/件等）' },
      { id: 'warehouseName', label: '所属仓库' },
      { id: 'currentStock', label: '当前库存' },
      { id: 'baseUnitId', label: '基础单位ID' },
      { id: 'conversionRate', label: '单位换算比例' },
      { id: 'packages', label: '件数/包装数' },
      { id: 'quantity', label: '数量（可表示公斤数）' },
      { id: 'price', label: '单价（元）' },
      { id: 'taxRate', label: '税率（%）' },
      { id: 'taxIncludedPrice', label: '含税单价' },
      { id: 'amount', label: '金额（元）' },
      { id: 'totalAmount', label: '含税金额' },
      { id: 'remark', label: '商品备注' }
    ]
  },
  {
    id: 'summaryInfo',
    label: '合计与收款',
    children: [
      { id: 'totalPackages', label: '合计件数' },
      { id: 'totalQuantity', label: '合计数量' },
      { id: 'totalAmount', label: '合计金额' },
      { id: 'totalTaxAmount', label: '合计含税金额' },
      { id: 'discountAmount', label: '折扣金额/本单金额' },
      { id: 'otherFees', label: '其他费用' },
      { id: 'settlementAccount', label: '结算账户' },
      { id: 'customerReceivable', label: '客户欠款' },
      { id: 'shouldReceive', label: '本单应收' },
      { id: 'amountInWords', label: '金额中文大写' },
      { id: 'currentPayment', label: '本次收款' },
      { id: 'currentDebt', label: '本单欠款' }
    ]
  },
  {
    id: 'taxInfo',
    label: '税务信息',
    children: [
      { id: 'taxEnabled', label: '是否含税' },
      { id: 'taxRate', label: '默认税率（%）' }
    ]
  }
]

const defaultTemplateData = {
  canvasSize: { width: 794, height: 529 },
  pages: [{ id: 'sale-page', elements: [] }],
  unit: 'mm',
  testData: defaultVariables,
  ext: {
    availableVariables
  }
}

const normalizeVariableKey = (value) => {
  const token = String(value ?? '').trim()
  if (!token) return ''
  if (token.startsWith('@')) return token.slice(1).trim()
  if (token.startsWith('{#') && token.endsWith('}')) {
    return token.slice(2, -1).trim()
  }
  return token
}

const getCellVariableKey = (cell) => {
  const value = cell && typeof cell === 'object' ? cell.value : cell
  if (typeof value !== 'string') return ''
  const match = value.match(/@[A-Za-z0-9_.-]+/)
  return match ? normalizeVariableKey(match[0]) : ''
}

const tableHeaderFieldMap = {
  序号: 'index',
  商品名称: 'goodsName',
  商品信息: 'goodsName',
  规格型号: 'spec',
  单位: 'unit',
  数量: 'quantity',
  件数: 'packages',
  包装数: 'packages',
  单价: 'price',
  金额: 'amount',
  含税单价: 'taxIncludedPrice',
  含税金额: 'totalAmount',
  备注: 'remark'
}

const normalizeTableDetailBinding = (element) => {
  if (!element || !['table', 'TABLE'].includes(element.type)) return

  const dataVariableKey = normalizeVariableKey(element.variable)
  const columnsVariableKey = normalizeVariableKey(element.columnsVariable)

  // @items 是明细行数据源，不是列定义。误放到“列定义变量”时自动纠正。
  if (columnsVariableKey === 'items') {
    if (!dataVariableKey) {
      element.variable = '@items'
    }
    element.columnsVariable = ''
  }
  if (normalizeVariableKey(element.footerDataVariable) === 'items') {
    element.footerDataVariable = ''
  }

  if (normalizeVariableKey(element.variable) !== 'items') return

  const sampleItem = defaultVariables.items?.[0] || {}
  const columns = Array.isArray(element.columns) ? element.columns : []
  const layoutRows = Array.isArray(element.data) ? element.data : []
  const fieldMap = new Map()

  columns.forEach((column) => {
    const currentField = String(column?.field || '').trim()
    if (!currentField) return
    if (Object.prototype.hasOwnProperty.call(sampleItem, currentField)) {
      fieldMap.set(currentField, currentField)
      return
    }

    const sampleCell = layoutRows
      .map(row => row?.[currentField])
      .find(cell => getCellVariableKey(cell))
    const variableKey = getCellVariableKey(sampleCell)
    if (variableKey && Object.prototype.hasOwnProperty.call(sampleItem, variableKey)) {
      fieldMap.set(currentField, variableKey)
      return
    }

    const header = String(column?.header || '').trim()
    const headerField = tableHeaderFieldMap[header]
    if (headerField && Object.prototype.hasOwnProperty.call(sampleItem, headerField)) {
      fieldMap.set(currentField, headerField)
    }
  })

  if (fieldMap.size === 0) return

  element.columns = columns.map((column) => ({
    ...column,
    field: fieldMap.get(column.field) || column.field
  }))
  element.data = layoutRows.map((row) => {
    const nextRow = { ...row }
    fieldMap.forEach((targetField, sourceField) => {
      if (sourceField === targetField || row?.[sourceField] === undefined) return
      if (nextRow[targetField] === undefined) {
        nextRow[targetField] = nextRow[sourceField]
      }
      delete nextRow[sourceField]
    })
    return nextRow
  })
  element.footerData = (element.footerData || []).map((row) => {
    const nextRow = { ...row }
    fieldMap.forEach((targetField, sourceField) => {
      if (sourceField === targetField || row?.[sourceField] === undefined) return
      if (nextRow[targetField] === undefined) {
        nextRow[targetField] = nextRow[sourceField]
      }
      delete nextRow[sourceField]
    })
    return nextRow
  })
}

const getTableFooterVariable = (column) => {
  const field = String(column?.field || '').trim().toLowerCase()
  const header = String(column?.header || '').trim()

  if (field === 'packages' || field === 'package' || field === 'qtypackages' || header.includes('件数') || header.includes('包装')) {
    return '@totalPackages'
  }
  if (field === 'quantity' || field === 'qty' || header.includes('数量')) {
    return '@totalQuantity'
  }
  if (field === 'totalamount' || field === 'taxamount' || header.includes('含税金额')) {
    return '@totalTaxAmount'
  }
  if (field === 'amount' || field === 'total' || header.includes('金额')) {
    return '@totalAmount'
  }
  return ''
}

const createDefaultTableFooter = (columns) => {
  const footerRow = {}

  columns.forEach((column, index) => {
    const field = String(column?.field || `col${index + 1}`).trim()
    const variable = getTableFooterVariable(column)
    footerRow[field] = {
      value: index === 0 ? '合计' : variable
    }
  })

  return footerRow
}

const normalizeTableFooters = (design) => {
  const cloned = JSON.parse(JSON.stringify(design || {}))
  cloned.ext = {
    ...(cloned.ext || {}),
    availableVariables
  }

  ;(cloned.pages || []).forEach((page) => {
    ;(page.elements || []).forEach((element) => {
      if (!element || !['table', 'TABLE'].includes(element.type)) return
      normalizeTableDetailBinding(element)
      if (!Array.isArray(element.columns) || element.columns.length === 0) return

      if (!Array.isArray(element.footerData) || element.footerData.length === 0) {
        element.footerData = [createDefaultTableFooter(element.columns)]
      }
    })
  })

  return cloned
}

let footerFixTimer = null

const ensureLiveTableFooters = () => {
  const designer = designerRef.value
  const pages = designer?.designerStore?.pages
  if (!Array.isArray(pages)) return

  pages.forEach((page) => {
    ;(page.elements || []).forEach((element) => {
      if (!element || !['table', 'TABLE'].includes(element.type)) return
      normalizeTableDetailBinding(element)
      if (!Array.isArray(element.columns) || element.columns.length === 0) return

      if (!Array.isArray(element.footerData) || element.footerData.length === 0) {
        element.footerData = [createDefaultTableFooter(element.columns)]
      }
    })
  })
}

const startFooterFixTimer = () => {
  if (footerFixTimer !== null) return
  ensureLiveTableFooters()
  footerFixTimer = window.setInterval(ensureLiveTableFooters, 300)
}

const stopFooterFixTimer = () => {
  if (footerFixTimer === null) return
  window.clearInterval(footerFixTimer)
  footerFixTimer = null
}

const configureDesigner = async () => {
  const designer = designerRef.value
  if (!designer || configured.value || !designer.getTemplateData?.()) return

  configured.value = true
  designer.setBranding({
    title: '订单打印模板设计器',
    showLogo: false,
    showTitle: true
  })
  designer.setLanguage('zh')
  await designer.setTestData(defaultVariables, { merge: false })
  await designer.setTemplateVariables(defaultVariables, { merge: false })
  designer.loadTemplateData(normalizeTableFooters(
    props.template?.content ||
    props.template?.design ||
    props.template?.data ||
    defaultTemplateData
  ))
  startFooterFixTimer()
}

const openDesigner = async () => {
  configured.value = false
  templateName.value = props.template?.name || '销售三联单'
  await nextTick()
  const designer = designerRef.value
  if (designer?.getTemplateData?.()) {
    configureDesigner()
  }
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      openDesigner()
    } else {
      stopFooterFixTimer()
    }
  }
)

const handlePreview = async () => {
  const designer = designerRef.value
  if (!designer) return
  ensureLiveTableFooters()
  await designer.setVariables(defaultVariables, { merge: false })
  await designer.preview()
}

const handleSave = async () => {
  const designer = designerRef.value
  if (!designer) return
  await nextTick()
  ensureLiveTableFooters()
  const design = normalizeTableFooters(designer.getTemplateData())
  emit('save', {
    ...props.template,
    name: templateName.value || props.template?.name || '销售三联单',
    businessType: props.template?.businessType || 'sale',
    paperType: props.template?.paperType || '三联单',
    pageWidth: 210,
    pageHeight: 140,
    enabled: props.template?.enabled !== false,
    content: design,  // 后端期望的是 content 字段
    updatedAt: Date.now()
  })
}

const handleClose = () => emit('close')

onBeforeUnmount(stopFooterFixTimer)
</script>

<style scoped>
.print-designer-shell {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  background: #eef1f5;
}

.print-designer-toolbar {
  height: 58px;
  flex: 0 0 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  background: #fff;
  border-bottom: 1px solid #d9e0e8;
}

.designer-title {
  display: flex;
  align-items: baseline;
  gap: 14px;
  color: #172033;
  font-size: 16px;
  font-weight: 650;
}

.designer-name-input {
  width: 220px;
  height: 32px;
  padding: 0 9px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  color: #172033;
  font-size: 15px;
  font-weight: 650;
}

.designer-name-input:focus {
  outline: 2px solid rgba(15, 159, 120, 0.2);
  border-color: #0f9f78;
}

.designer-title small {
  color: #7b8798;
  font-size: 12px;
  font-weight: 400;
}

.designer-actions {
  display: flex;
  gap: 8px;
}

.designer-btn {
  height: 34px;
  padding: 0 14px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #475569;
  cursor: pointer;
}

.designer-btn-primary {
  border-color: #0f9f78;
  background: #0f9f78;
  color: #fff;
}

.print-designer-canvas {
  min-height: 0;
  flex: 1;
}

.print-designer-canvas print-designer {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
