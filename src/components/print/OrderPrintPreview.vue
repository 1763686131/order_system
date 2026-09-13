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
        <span>此处仅用于验证模板和订单数据绑定，不会提交打印任务。</span>
        <button type="button" class="preview-footer-button" @click="handleClose">关闭</button>
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
import { nextTick, ref, watch } from 'vue'
import 'vue-print-designer'
import 'vue-print-designer/style.css'

const props = defineProps({
  visible: { type: Boolean, default: false },
  template: { type: Object, default: null },
  variables: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close'])
const designerRef = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const previewHtml = ref('')
const designerReady = ref(false)

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
  const value = cell && typeof cell === 'object' ? cell.value : cell
  if (typeof value !== 'string') return ''
  const match = value.match(/@[A-Za-z0-9_.-]+/)
  return match ? normalizeVariableKey(match[0]) : ''
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
    return
  }

  element.footerData = element.footerData.map((row, rowIndex) => {
    const nextRow = { ...(row || {}) }

    columns.forEach((column, columnIndex) => {
      const field = String(column?.field || `col${columnIndex + 1}`).trim()
      const variable = getTableFooterVariable(column)
      if (!variable && !(rowIndex === 0 && columnIndex === 0)) return

      const current = nextRow[field]
      const currentValue = current && typeof current === 'object' ? current.value : current
      if (currentValue !== undefined && currentValue !== null && String(currentValue) !== '') return

      nextRow[field] = {
        ...(current && typeof current === 'object' ? current : {}),
        value: rowIndex === 0 && columnIndex === 0 ? '合计' : variable
      }
    })

    return nextRow
  })
}

const clonePreviewDesign = (design, variables) => {
  const cloned = JSON.parse(JSON.stringify(design))
  const runtimeVariables = variables && typeof variables === 'object' ? variables : {}
  const items = Array.isArray(runtimeVariables.items) ? runtimeVariables.items : []

  cloned.testData = {
    ...(cloned.testData || {}),
    ...runtimeVariables
  }

  if (!Array.isArray(cloned.pages)) {
    return cloned
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

  cloned.pages.forEach((page) => {
    ;(page.elements || []).forEach((element) => {
      if (!element || !['table', 'TABLE'].includes(element.type)) {
        return
      }

      const columns = Array.isArray(element.columns) ? element.columns : []
      const layoutRows = Array.isArray(element.data) ? element.data : []
      const sampleItem = items[0] || {}
      const fieldMap = new Map()
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
        element.variable = '@items'
      }
    })
  })

  return cloned
}

const loadPreview = async () => {
  const designer = designerRef.value
  if (!designer || !props.template) return

  loading.value = true
  errorMessage.value = ''
  previewHtml.value = ''

  try {
    const design = props.template.design || props.template.data
    if (!design) {
      throw new Error('该模板还没有保存设计内容，请先在模板管理中完成设计并保存。')
    }

    const previewDesign = clonePreviewDesign(design, props.variables)
    designer.setLanguage('zh')
    designer.loadTemplateData(previewDesign)
    await designer.setTestData(props.variables || {}, { merge: false })
    await designer.setTemplateVariables(props.variables || {}, { merge: false })
    await designer.setVariables(props.variables || {}, { merge: false })
    const html = await designer.getPreviewHtml()
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

const handleClose = () => emit('close')
</script>

<style scoped>
.order-print-preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
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

.preview-footer-button {
  height: 34px;
  padding: 0 16px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #475569;
  cursor: pointer;
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
}
</style>
