<template>
  <div v-if="visible" class="print-designer-shell">
    <div
      class="print-designer-toolbar"
      :class="{ 'save-menu-open': saveMenuOpen }"
    >
      <div class="designer-title">
        <input
          v-model="templateName"
          class="designer-name-input"
          aria-label="模板名称"
          placeholder="模板名称"
        />
        <select
          v-model="businessType"
          class="designer-business-select"
          aria-label="业务类型"
          title="业务类型"
        >
          <option
            v-for="option in businessTypeOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
        <small>{{ pageSizeLabel }} · {{ paperTypeLabel }}打印 1 份</small>
      </div>
      <div class="designer-actions">
        <button type="button" class="designer-btn" @click="handlePreview">预览</button>
        <div ref="saveMenuRef" class="designer-save-menu">
          <div class="designer-save-split">
            <button
              type="button"
              class="designer-save-main"
              title="保存模板"
              @click="handleSave"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M5 3h12l2 2v16H5z"></path>
                <path d="M8 3v6h8V3"></path>
                <path d="M8 14h8v7H8z"></path>
              </svg>
              <span>保存模板</span>
            </button>
            <button
              type="button"
              class="designer-save-toggle"
              title="更多保存选项"
              aria-label="更多保存选项"
              :aria-expanded="saveMenuOpen"
              @click="saveMenuOpen = !saveMenuOpen"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="m7 9 5 5 5-5"></path>
              </svg>
            </button>
          </div>

          <div v-if="saveMenuOpen" class="designer-save-dropdown">
            <button type="button" @click="handleToolbarReorder">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M8 6h.01M8 12h.01M8 18h.01M16 6h.01M16 12h.01M16 18h.01"></path>
              </svg>
              <span>操作栏排序</span>
            </button>
            <button type="button" @click="handleOpenHelp">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M9.8 9a2.3 2.3 0 1 1 3.7 1.8c-.9.6-1.5 1-1.5 2.2"></path>
                <path d="M12 17h.01"></path>
              </svg>
              <span>帮助</span>
            </button>
            <button type="button" @click="handleOpenSettings">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"></path>
              </svg>
              <span>设置</span>
            </button>
          </div>
        </div>
        <button type="button" class="designer-btn" @click="handleClose">退出</button>
      </div>
    </div>
    <div class="print-designer-canvas">
      <print-designer ref="designerRef" @ready="configureDesigner"></print-designer>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import 'vue-print-designer'
import 'vue-print-designer/style.css'
import { toChineseMoney } from '@/utils/chineseMoney'

const props = defineProps({
  visible: { type: Boolean, default: false },
  template: { type: Object, default: null },
  templates: { type: Array, default: () => [] }
})

const emit = defineEmits(['save', 'close'])
const designerRef = ref(null)
const saveMenuRef = ref(null)
const saveMenuOpen = ref(false)
const templateName = ref('')
const businessType = ref('sale')
const paperType = ref('三联单')
const pageWidth = ref(210)
const pageHeight = ref(140)
const configured = ref(false)
const NEW_TEMPLATE_ID = '__order_system_new_template__'
const businessTypeOptions = [
  { value: 'sale', label: '销售' },
  { value: 'purchase', label: '采购' },
  { value: 'return', label: '退货' },
  { value: 'transfer', label: '调拨' },
  { value: 'inventory', label: '盘点' },
  { value: 'receipt', label: '收款' },
  { value: 'payment', label: '付款' }
]
const paperSizePresets = [
  { width: 210, height: 140, label: '三联单' },
  { width: 241, height: 140, label: '二等分' },
  { width: 210, height: 297, label: 'A4', rotate: true },
  { width: 297, height: 420, label: 'A3', rotate: true },
  { width: 148, height: 210, label: 'A5', rotate: true }
]
let activeDesignerTemplateId = ''
let activeCanvasSizeKey = ''
let designerDomObserver = null

const formatMillimeter = value => (
  Number.isInteger(Number(value))
    ? String(Number(value))
    : Number(value).toFixed(2).replace(/\.?0+$/, '')
)

const pageSizeLabel = computed(() => (
  `${formatMillimeter(pageWidth.value)}mm × ${formatMillimeter(pageHeight.value)}mm`
))

const paperTypeLabel = computed(() => paperType.value || '自定义纸张')

const canvasPixelToMillimeter = (value) => {
  const millimeter = Number(value) * 25.4 / 96
  if (!Number.isFinite(millimeter) || millimeter <= 0) return 0
  return Number(millimeter.toFixed(2))
}

const matchesPaperSize = (width, height, preset) => {
  const direct = Math.abs(width - preset.width) < 0.2 &&
    Math.abs(height - preset.height) < 0.2
  const rotated = preset.rotate &&
    Math.abs(width - preset.height) < 0.2 &&
    Math.abs(height - preset.width) < 0.2
  return direct || rotated
}

const detectPaperType = (width, height) => (
  paperSizePresets.find(preset => matchesPaperSize(width, height, preset))?.label || ''
)

const normalizeKnownPaperSize = (width, height) => {
  for (const preset of paperSizePresets) {
    const direct = Math.abs(width - preset.width) < 0.2 &&
      Math.abs(height - preset.height) < 0.2
    if (direct) {
      return { width: preset.width, height: preset.height }
    }

    const rotated = preset.rotate &&
      Math.abs(width - preset.height) < 0.2 &&
      Math.abs(height - preset.width) < 0.2
    if (rotated) {
      return { width: preset.height, height: preset.width }
    }
  }
  return { width, height }
}

const syncDesignerPageSize = () => {
  const designer = designerRef.value
  const canvasSize = designer?.designerStore?.canvasSize ||
    designer?.getTemplateData?.()?.canvasSize
  const convertedWidth = canvasPixelToMillimeter(canvasSize?.width)
  const convertedHeight = canvasPixelToMillimeter(canvasSize?.height)
  const {
    width: nextWidth,
    height: nextHeight
  } = normalizeKnownPaperSize(convertedWidth, convertedHeight)
  if (!nextWidth || !nextHeight) return

  const nextCanvasSizeKey = `${nextWidth}x${nextHeight}`
  const canvasSizeChanged = Boolean(
    activeCanvasSizeKey && activeCanvasSizeKey !== nextCanvasSizeKey
  )
  activeCanvasSizeKey = nextCanvasSizeKey
  pageWidth.value = nextWidth
  pageHeight.value = nextHeight

  if (canvasSizeChanged) {
    paperType.value = detectPaperType(nextWidth, nextHeight) || '自定义'
  }
}

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
  cloned.testData = {
    ...defaultVariables,
    ...(cloned.testData || {})
  }
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

const getDesignerTemplateId = (template) => (
  template?.id === undefined || template?.id === null
    ? ''
    : String(template.id)
)

const getTemplateUpdatedAt = (template) => {
  const timestamp = new Date(template?.updatedAt || template?.updated_at || '').getTime()
  return Number.isFinite(timestamp) ? timestamp : Date.now()
}

const getDesignerTemplateList = () => {
  const mappedTemplates = props.templates.map((template) => ({
    id: getDesignerTemplateId(template),
    name: template.name || '未命名模板',
    data: normalizeTableFooters(
      template.content ||
      template.design ||
      template.data ||
      defaultTemplateData
    ),
    updatedAt: getTemplateUpdatedAt(template),
    permissions: {
      editable: true,
      deletable: false,
      copyable: false
    },
    ext: {
      availableVariables
    }
  })).filter(template => template.id)

  if (getDesignerTemplateId(props.template)) {
    return mappedTemplates
  }

  return [
    {
      id: NEW_TEMPLATE_ID,
      name: props.template?.name || '销售三联单',
      data: normalizeTableFooters(
        props.template?.content ||
        props.template?.design ||
        props.template?.data ||
        defaultTemplateData
      ),
      updatedAt: Date.now(),
      permissions: {
        editable: true,
        deletable: false,
        copyable: false
      },
      ext: {
        availableVariables
      }
    },
    ...mappedTemplates
  ]
}

const getCurrentDatabaseTemplate = () => {
  const currentId = String(
    designerRef.value?.templateStore?.currentTemplateId || ''
  )
  if (!currentId || currentId === NEW_TEMPLATE_ID) {
    return props.template || null
  }
  return props.templates.find(template => (
    getDesignerTemplateId(template) === currentId
  )) || props.template || null
}

const syncActiveTemplateName = () => {
  const designer = designerRef.value
  const currentId = String(designer?.templateStore?.currentTemplateId || '')
  if (!currentId || currentId === activeDesignerTemplateId) return

  activeDesignerTemplateId = currentId
  const databaseTemplate = props.templates.find(template => (
    getDesignerTemplateId(template) === currentId
  ))
  const selectedTemplate = databaseTemplate || props.template || null
  const internalTemplate = designer.getTemplate?.(currentId)
  templateName.value = databaseTemplate?.name ||
    internalTemplate?.name ||
    props.template?.name ||
    '销售三联单'
  businessType.value = selectedTemplate?.businessType || 'sale'
  paperType.value = selectedTemplate?.paperType || '三联单'
  activeCanvasSizeKey = ''
}

const ensureLiveTableFooters = () => {
  const designer = designerRef.value
  syncActiveTemplateName()
  syncDesignerPageSize()
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

const getDesignerDomRoot = () => (
  designerRef.value?.shadowRoot || designerRef.value || null
)

const customizeDesignerChrome = () => {
  const root = getDesignerDomRoot()
  if (!root?.querySelectorAll) return

  const nativeSaveButton = Array.from(root.querySelectorAll('header button')).find(
    button => button.textContent?.replace(/\s+/g, '') === '保存'
  )
  const header = nativeSaveButton?.closest('header')
  const nativeActionSection = header
    ? Array.from(header.children).find(child => child.contains(nativeSaveButton))
    : null

  nativeActionSection?.style.setProperty('display', 'none', 'important')

  Array.from(root.querySelectorAll('button')).forEach((button) => {
    const label = button.textContent?.replace(/\s+/g, '') || ''
    if (label === '新建模板' || label === '新建模版') {
      button.style.setProperty('display', 'none', 'important')
    }
  })
}

const installDesignerChromeObserver = () => {
  designerDomObserver?.disconnect()
  designerDomObserver = null

  const root = getDesignerDomRoot()
  if (!root) return

  customizeDesignerChrome()
  designerDomObserver = new MutationObserver(customizeDesignerChrome)
  designerDomObserver.observe(root, { childList: true, subtree: true })
}

const stopDesignerChromeObserver = () => {
  designerDomObserver?.disconnect()
  designerDomObserver = null
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
  designer.setTemplateContextMenu({
    mode: 'replace',
    items: [
      { key: 'viewJson', actionKey: 'viewJson', label: '查看 JSON' },
      { key: 'testData', actionKey: 'testData', label: '测试数据' }
    ]
  })
  designer.setTemplates(getDesignerTemplateList(), {
    currentTemplateId: getDesignerTemplateId(props.template) || NEW_TEMPLATE_ID
  })
  await nextTick()
  syncActiveTemplateName()
  installDesignerChromeObserver()
  startFooterFixTimer()
}

const openDesigner = async () => {
  configured.value = false
  activeDesignerTemplateId = ''
  activeCanvasSizeKey = ''
  saveMenuOpen.value = false
  templateName.value = props.template?.name || '销售三联单'
  businessType.value = props.template?.businessType || 'sale'
  paperType.value = props.template?.paperType || '三联单'
  pageWidth.value = Number(props.template?.pageWidth) || 210
  pageHeight.value = Number(props.template?.pageHeight) || 140
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
      saveMenuOpen.value = false
      stopFooterFixTimer()
      stopDesignerChromeObserver()
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
  const currentTemplate = getCurrentDatabaseTemplate()
  const currentId = String(designer.templateStore?.currentTemplateId || '')
  emit('save', {
    ...currentTemplate,
    id: currentId && currentId !== NEW_TEMPLATE_ID
      ? currentTemplate?.id ?? currentId
      : null,
    name: templateName.value || currentTemplate?.name || '销售三联单',
    businessType: businessType.value || 'sale',
    paperType: paperType.value || '自定义',
    pageWidth: pageWidth.value || 210,
    pageHeight: pageHeight.value || 140,
    enabled: currentTemplate?.enabled !== false,
    content: design,
    updatedAt: Date.now()
  })
}

const handleToolbarReorder = () => {
  saveMenuOpen.value = false
  window.dispatchEvent(new CustomEvent('designer:toolbar-reorder'))
}

const handleOpenHelp = () => {
  saveMenuOpen.value = false
  designerRef.value?.designerStore?.setShowHelp(true)
}

const handleOpenSettings = () => {
  saveMenuOpen.value = false
  designerRef.value?.designerStore?.setShowSettings(true)
}

const handleOutsidePointerDown = (event) => {
  if (!saveMenuRef.value?.contains(event.target)) {
    saveMenuOpen.value = false
  }
}

const handleNativeSaveEvent = (event) => {
  if (!props.visible) return
  event.stopImmediatePropagation()
  handleSave()
}

const handleClose = () => emit('close')

onMounted(() => {
  window.addEventListener('pointerdown', handleOutsidePointerDown)
  window.addEventListener('designer:save', handleNativeSaveEvent, true)
})

onBeforeUnmount(() => {
  stopFooterFixTimer()
  stopDesignerChromeObserver()
  window.removeEventListener('pointerdown', handleOutsidePointerDown)
  window.removeEventListener('designer:save', handleNativeSaveEvent, true)
})
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
  position: relative;
  z-index: 2;
  height: 58px;
  flex: 0 0 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  background: #fff;
  border-bottom: 1px solid #d9e0e8;
}

.print-designer-toolbar.save-menu-open {
  z-index: 4;
}

.designer-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
  color: #172033;
  font-size: 16px;
  font-weight: 650;
}

.designer-name-input {
  width: 220px;
  min-width: 160px;
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

.designer-business-select {
  width: 108px;
  height: 32px;
  padding: 0 28px 0 10px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #334155;
  font-size: 14px;
  cursor: pointer;
}

.designer-business-select:focus {
  outline: 2px solid rgba(15, 159, 120, 0.2);
  border-color: #0f9f78;
}

.designer-title small {
  color: #7b8798;
  font-size: 12px;
  font-weight: 400;
  white-space: nowrap;
}

.designer-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
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

.designer-save-menu {
  position: relative;
}

.designer-save-split {
  display: flex;
  height: 34px;
  filter: drop-shadow(0 1px 1px rgba(15, 23, 42, 0.08));
}

.designer-save-main,
.designer-save-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: #0f9f78;
  color: #fff;
  cursor: pointer;
  transition: background 0.15s ease;
}

.designer-save-main:hover,
.designer-save-toggle:hover {
  background: #087f62;
}

.designer-save-main {
  gap: 7px;
  padding: 0 13px;
  border-right: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 5px 0 0 5px;
  font-size: 14px;
}

.designer-save-toggle {
  width: 34px;
  padding: 0;
  border-radius: 0 5px 5px 0;
}

.designer-save-main svg,
.designer-save-toggle svg,
.designer-save-dropdown svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.designer-save-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 20;
  width: 170px;
  padding: 5px;
  border: 1px solid #dbe2ea;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
}

.designer-save-dropdown button {
  width: 100%;
  height: 36px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0 10px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #334155;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.designer-save-dropdown button:hover {
  background: #f1f5f9;
  color: #0f766e;
}

.print-designer-canvas {
  position: relative;
  z-index: 3;
  min-height: 0;
  flex: 1;
}

.print-designer-canvas print-designer {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
