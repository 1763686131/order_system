<template>
  <div v-if="visible" class="order-print-preview-overlay">
    <div class="order-print-preview-dialog">
      <div class="order-print-preview-header">
        <div>
          <h3>{{ template?.name || '打印预览' }}</h3>
          <span>当前订单数据预览 · {{ template?.pageWidth || 210 }}mm × {{ template?.pageHeight || 140 }}mm</span>
        </div>
        <button type="button" class="preview-close" title="关闭" @click="handleClose">×</button>
      </div>

      <div class="order-print-preview-body">
        <div v-if="loading" class="preview-state">正在生成预览...</div>
        <div v-else-if="errorMessage" class="preview-state preview-error">
          {{ errorMessage }}
        </div>
        <iframe
          v-else-if="previewHtml"
          class="preview-frame"
          title="订单打印预览"
          :srcdoc="previewHtml"
        ></iframe>
        <div v-else class="preview-state">暂无可预览内容</div>
      </div>

      <div class="order-print-preview-footer">
        <span :class="{ 'preview-footer-error': printErrorMessage }">
          {{ printErrorMessage || '点击打印后将在 C-Lodop 中确认打印机和纸张效果。' }}
        </span>
        <div class="preview-footer-actions">
          <button
            type="button"
            class="preview-footer-button preview-print-button"
            :title="printButtonTitle"
            :disabled="loading || printing || !renderedHtml"
            @click="handlePrint"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M6 9V2h12v7"></path>
              <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
              <path d="M6 14h12v8H6z"></path>
            </svg>
            {{ printing ? '正在连接...' : '打印' }}
          </button>
          <button type="button" class="preview-footer-button" @click="handleClose">关闭</button>
        </div>
      </div>
    </div>

    <print-designer
      ref="designerRef"
      class="preview-driver"
      @ready="handleDesignerReady"
    ></print-designer>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import 'vue-print-designer'
import 'vue-print-designer/style.css'
import { openLodopPrintPreview } from '@/utils/lodopPrint'

const props = defineProps({
  visible: { type: Boolean, default: false },
  template: { type: Object, default: null },
  variables: { type: Object, default: () => ({}) },
  trailingBlankRows: {
    type: Number,
    default: 1,
    validator: value => Number.isInteger(value) && value >= 0
  },
  hideZeroValues: { type: Boolean, default: true }
})

const emit = defineEmits(['close'])
const designerRef = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const previewHtml = ref('')
const renderedHtml = ref('')
const designerReady = ref(false)
const printing = ref(false)
const printErrorMessage = ref('')

const printButtonTitle = computed(() => {
  if (loading) return '正在生成打印内容'
  if (!renderedHtml.value) return '暂无可打印内容'
  return '使用 C-Lodop 打印'
})

const normalizeTableCellAlignment = (html) => {
  if (typeof DOMParser === 'undefined') return html

  const document = new DOMParser().parseFromString(
    `<body>${String(html || '')}</body>`,
    'text/html'
  )

  document.body.querySelectorAll('table th, table td').forEach((cell) => {
    cell.style.setProperty('vertical-align', 'middle', 'important')
    cell.style.setProperty('line-height', 'normal', 'important')
  })

  return document.body.innerHTML
}

const wrapPreviewHtml = (html) => `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <style>
      html, body { margin: 0; padding: 0; background: #eef1f5; }
      body { min-height: 100vh; display: flex; justify-content: center; padding: 24px; box-sizing: border-box; }
      * { box-sizing: border-box; }
    </style>
  </head>
  <body>${html}</body>
</html>`

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
  const candidates = cell && typeof cell === 'object'
    ? [cell.value, cell.field]
    : [cell]

  for (const value of candidates) {
    if (typeof value !== 'string') continue
    const match = value.match(/@[A-Za-z0-9_.-]+/)
    if (match) return normalizeVariableKey(match[0])
  }
  return ''
}

const getCellLiteralValue = (cell) => {
  const value = cell && typeof cell === 'object' ? cell.value : cell
  if (value === undefined || value === null || getCellVariableKey(cell)) {
    return ''
  }
  return value
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

const createDefaultTableFooter = (columns) => columns.reduce((row, column, index) => {
  const field = String(column?.field || `col${index + 1}`).trim()
  const variable = getTableFooterVariable(column)
  row[field] = { value: index === 0 ? '合计' : variable }
  return row
}, {})

const fillTableFooterDefaults = (element) => {
  const columns = Array.isArray(element?.columns) ? element.columns : []
  if (columns.length === 0) return

  if (!Array.isArray(element.footerData) || element.footerData.length === 0) {
    element.footerData = [createDefaultTableFooter(columns)]
  }
}

const appendTrailingBlankRows = (rows, columns, count) => {
  const blankRowCount = Math.max(0, Math.floor(Number(count) || 0))
  if (blankRowCount === 0) return rows

  const blankRows = Array.from({ length: blankRowCount }, () => (
    (columns || []).reduce((row, column) => {
      const field = String(column?.field || '').trim()
      if (field) row[field] = ''
      return row
    }, {})
  ))

  return [...rows, ...blankRows]
}

const formatTableDataValue = (value, hideZeroValues) => {
  if (!hideZeroValues) return value
  if (typeof value === 'number') return value === 0 ? '' : value
  if (typeof value !== 'string') return value

  const normalized = value.trim()
  return normalized && /^[+-]?0(?:\.0+)?$/.test(normalized) ? '' : value
}

const formatTableDataRow = (row, hideZeroValues) => (
  Object.entries(row || {}).reduce((formattedRow, [field, value]) => {
    formattedRow[field] = formatTableDataValue(value, hideZeroValues)
    return formattedRow
  }, {})
)

const clonePreviewDesign = (
  design,
  variables,
  trailingBlankRows = 0,
  hideZeroValues = true
) => {
  const cloned = JSON.parse(JSON.stringify(design))
  const runtimeVariables = variables && typeof variables === 'object'
    ? JSON.parse(JSON.stringify(variables))
    : {}
  const items = Array.isArray(runtimeVariables.items) ? runtimeVariables.items : []

  if (!Array.isArray(cloned.pages)) {
    cloned.testData = {
      ...(cloned.testData || {}),
      ...runtimeVariables
    }
    return { design: cloned, variables: runtimeVariables }
  }

  // 设计器中有些表格只把 @goodsName、@quantity 等字段放进了单元格，
  // 没有设置表格的数据变量。预览时自动识别这种明细表并绑定到 @items，
  // 否则设计器只会继续显示保存时的示例行或原始占位符。
  const detailFields = [
    'index',
    'productId',
    'goodsName',
    'spec',
    'unit',
    'warehouseName',
    'packages',
    'quantity',
    'price',
    'taxRate',
    'taxIncludedPrice',
    'amount',
    'remark'
  ]

  cloned.pages.forEach((page, pageIndex) => {
    ;(page.elements || []).forEach((element, elementIndex) => {
      if (!element || !['table', 'TABLE'].includes(element.type)) {
        return
      }

      const columns = Array.isArray(element.columns) ? element.columns : []
      const layoutRows = Array.isArray(element.data) ? element.data : []
      const sampleItem = items[0] || {}
      const fieldMap = new Map()
      const explicitBindings = new Map()
      const dataVariableKey = normalizeVariableKey(element.variable)
      const columnsVariableKey = normalizeVariableKey(element.columnsVariable)
      const footerDataVariableKey = normalizeVariableKey(element.footerDataVariable)

      // 自定义表格默认没有 footerData，打开“显示表脚”也不会凭空生成表脚行。
      // 预览时补一行可绑定订单合计的表脚，用户仍可在设计器中继续编辑它。
      fillTableFooterDefaults(element)

      // @items 是明细数据源，不是列定义或页脚数据源。
      // 如果设计器误把它保存到了这两个属性，必须清掉，否则列标题会被
      // 商品对象覆盖，最终只剩下空白表格。
      if (columnsVariableKey === 'items') {
        element.columnsVariable = ''
      }
      if (footerDataVariableKey === 'items') {
        element.footerDataVariable = ''
      }

      if (items.length === 0) {
        return
      }

      columns.forEach((column) => {
        const currentField = String(column?.field || '').trim()
        if (!currentField) return

        const sampleCell = layoutRows
          .map(row => row?.[currentField])
          .find(cell => getCellVariableKey(cell))
        const variableKey = getCellVariableKey(sampleCell)
        if (variableKey && Object.prototype.hasOwnProperty.call(sampleItem, variableKey)) {
          explicitBindings.set(currentField, variableKey)
        }
      })

      // 只要表格中有任意显式单元格变量，就尊重设计者的列级绑定。
      // 未写 @变量 的列保持设计值（通常为空），不再按字段名自动取商品数据。
      const usesExplicitBindings = explicitBindings.size > 0

      columns.forEach((column) => {
        const currentField = String(column?.field || '').trim()
        if (!currentField) return

        if (explicitBindings.has(currentField)) {
          fieldMap.set(currentField, explicitBindings.get(currentField))
          return
        }

        if (usesExplicitBindings) {
          return
        }

        if (Object.prototype.hasOwnProperty.call(sampleItem, currentField)) {
          fieldMap.set(currentField, currentField)
          return
        }

        const header = String(column?.header || '').trim()
        const headerFieldMap = {
          '序号': 'index',
          '商品名称': 'goodsName',
          '商品信息': 'goodsName',
          '规格型号': 'spec',
          '单位': 'unit',
          '数量': 'quantity',
          '件数': 'packages',
          '包装数': 'packages',
          '单价': 'price',
          '金额': 'amount',
          '含税单价': 'taxIncludedPrice',
          '含税金额': 'totalAmount',
          '备注': 'remark'
        }
        const headerField = headerFieldMap[header]
        if (headerField && Object.prototype.hasOwnProperty.call(sampleItem, headerField)) {
          fieldMap.set(currentField, headerField)
        }
      })

      if (fieldMap.size > 0) {
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
        fillTableFooterDefaults(element)
      }

      const serialized = JSON.stringify({
        columns: element.columns || [],
        data: element.data || []
      })
      const hasDetailBinding = detailFields.some((field) => (
        serialized.includes(`@${field}`) ||
        (Array.isArray(element.columns) && element.columns.some(column => column?.field === field))
      ))

      if (hasDetailBinding || dataVariableKey === 'items' || columnsVariableKey === 'items') {
        const tableVariableKey = `__previewItems_${pageIndex}_${elementIndex}`

        if (usesExplicitBindings) {
          const tableRows = items.map((item) => {
            const row = {}

            columns.forEach((column) => {
              const sourceField = String(column?.field || '').trim()
              if (!sourceField) return

              const renderedField = fieldMap.get(sourceField) || sourceField
              const variableKey = explicitBindings.get(sourceField)
              if (variableKey) {
                row[renderedField] = formatTableDataValue(
                  item?.[variableKey] ?? '',
                  hideZeroValues
                )
                return
              }

              const layoutRow = layoutRows.find(layout => (
                layout && Object.prototype.hasOwnProperty.call(layout, sourceField)
              ))
              row[renderedField] = getCellLiteralValue(layoutRow?.[sourceField])
            })

            return row
          })
          runtimeVariables[tableVariableKey] = appendTrailingBlankRows(
            tableRows,
            element.columns,
            trailingBlankRows
          )
          element.variable = `@${tableVariableKey}`
        } else if (trailingBlankRows > 0 || hideZeroValues) {
          runtimeVariables[tableVariableKey] = appendTrailingBlankRows(
            items.map(item => formatTableDataRow(item, hideZeroValues)),
            element.columns,
            trailingBlankRows
          )
          element.variable = `@${tableVariableKey}`
        } else {
          element.variable = '@items'
        }
      }
    })
  })

  cloned.testData = {
    ...(cloned.testData || {}),
    ...runtimeVariables
  }

  return { design: cloned, variables: runtimeVariables }
}

const loadPreview = async () => {
  const designer = designerRef.value
  if (!designer || !props.template) return

  loading.value = true
  errorMessage.value = ''
  previewHtml.value = ''
  renderedHtml.value = ''
  printErrorMessage.value = ''

  try {
    const design = props.template.content || props.template.design || props.template.data
    if (!design) {
      throw new Error('该模板还没有保存设计内容，请先在模板管理中完成设计并保存。')
    }

    const previewRuntime = clonePreviewDesign(
      design,
      props.variables,
      props.trailingBlankRows,
      props.hideZeroValues
    )
    designer.setLanguage('zh')
    designer.loadTemplateData(previewRuntime.design)
    await designer.setTestData(previewRuntime.variables, { merge: false })
    await designer.setTemplateVariables(previewRuntime.variables, { merge: false })
    await designer.setVariables(previewRuntime.variables, { merge: false })
    const html = normalizeTableCellAlignment(await designer.getPreviewHtml())
    renderedHtml.value = html
    previewHtml.value = wrapPreviewHtml(html)
  } catch (error) {
    errorMessage.value = error?.message || '模板预览生成失败'
  } finally {
    loading.value = false
  }
}

const handleDesignerReady = async () => {
  designerReady.value = true
  await loadPreview()
}

const openPreview = async () => {
  designerReady.value = false
  loading.value = true
  errorMessage.value = ''
  previewHtml.value = ''
  renderedHtml.value = ''
  printErrorMessage.value = ''
  await nextTick()
  if (designerRef.value?.getTemplateData?.()) {
    designerReady.value = true
    await loadPreview()
  }
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) openPreview()
  }
)

watch(
  () => props.variables,
  () => {
    if (props.visible && designerReady.value) loadPreview()
  },
  { deep: true }
)

watch(
  () => props.template,
  () => {
    if (props.visible && designerReady.value) loadPreview()
  },
  { deep: true }
)

watch(
  () => props.trailingBlankRows,
  () => {
    if (props.visible && designerReady.value) loadPreview()
  }
)

watch(
  () => props.hideZeroValues,
  () => {
    if (props.visible && designerReady.value) loadPreview()
  }
)

const handlePrint = async () => {
  if (!renderedHtml.value || printing.value) return

  printing.value = true
  printErrorMessage.value = ''

  try {
    const orderNumber = props.variables?.orderNumber || props.variables?.orderNo || ''
    const taskName = [props.template?.name || '单据打印', orderNumber]
      .filter(Boolean)
      .join(' - ')

    await openLodopPrintPreview({
      html: renderedHtml.value,
      taskName,
      pageWidth: props.template?.pageWidth,
      pageHeight: props.template?.pageHeight
    })
    emit('close')
  } catch (error) {
    printErrorMessage.value = error?.message || '调用 C-Lodop 打印失败'
  } finally {
    printing.value = false
  }
}

const handleClose = () => emit('close')
</script>

<style scoped>
.order-print-preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147483000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.58);
}

.order-print-preview-dialog {
  width: min(1120px, 96vw);
  height: min(820px, 94vh);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #eef1f5;
  border: 1px solid #cbd5e1;
  border-radius: 7px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.25);
}

.order-print-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 0 0 auto;
  padding: 14px 18px;
  background: #fff;
  border-bottom: 1px solid #d9e0e8;
}

.order-print-preview-header h3 {
  margin: 0 0 4px;
  color: #172033;
  font-size: 16px;
}

.order-print-preview-header span,
.order-print-preview-footer span {
  color: #7b8798;
  font-size: 12px;
}

.preview-close {
  width: 32px;
  height: 32px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #64748b;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.order-print-preview-body {
  min-height: 0;
  flex: 1;
}

.preview-frame {
  width: 100%;
  height: 100%;
  border: 0;
  background: #eef1f5;
}

.preview-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #64748b;
  font-size: 14px;
  text-align: center;
}

.preview-error {
  color: #b4232f;
}

.preview-footer-error {
  color: #b4232f !important;
  white-space: pre-line;
}

.order-print-preview-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex: 0 0 auto;
  padding: 11px 18px;
  background: #fff;
  border-top: 1px solid #d9e0e8;
}

.preview-footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-footer-button {
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 16px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #475569;
  cursor: pointer;
}

.preview-footer-button svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.preview-print-button {
  color: #fff;
  background: #0f9f78;
  border-color: #0f9f78;
}

.preview-print-button:disabled {
  color: #94a3b8;
  background: #f1f5f9;
  border-color: #d8e0e8;
  cursor: not-allowed;
}

.preview-driver {
  position: fixed;
  left: -10000px;
  top: -10000px;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
}

@media (max-width: 780px) {
  .order-print-preview-overlay {
    padding: 0;
  }

  .order-print-preview-dialog {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .order-print-preview-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .preview-footer-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
