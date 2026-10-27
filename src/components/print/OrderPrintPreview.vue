<template>
  <div v-if="visible" class="order-print-preview-overlay">
    <div
      ref="dialogRef"
      class="order-print-preview-dialog"
      :class="{ 'with-template-picker': templateSelection }"
      role="dialog"
      aria-modal="true"
      :aria-label="title"
      tabindex="-1"
      @keydown.esc.prevent="handleClose"
    >
      <div class="order-print-preview-header">
        <div>
          <h3>{{ templateSelection ? title : template?.name || title }}</h3>
          <span>
            <template v-if="documentNumber">{{ documentNumber }} · </template>
            {{ previewLabel }}
            <template v-if="template"> · {{ template.pageWidth || 210 }}mm × {{ template.pageHeight || 140 }}mm</template>
            · {{ resolvedPrinterName }}
          </span>
        </div>
        <button type="button" class="preview-close" title="关闭" @click="handleClose">×</button>
      </div>

      <div class="preview-workspace">
        <aside v-if="templateSelection" class="preview-template-sidebar">
          <div class="preview-template-heading">
            <label :for="templatePickerId"><FileText :size="16" aria-hidden="true" />打印模板</label>
            <button
              type="button"
              class="preview-footer-button preview-icon-button preview-template-reload"
              title="刷新打印模板"
              aria-label="刷新打印模板"
              :disabled="templatesLoading || printing || sharingImage"
              @click="emit('reload-templates')"
            >
              <RefreshCw :size="15" aria-hidden="true" />
            </button>
          </div>
          <div
            ref="templatePickerRef"
            class="preview-template-picker"
            @keydown="handleTemplatePickerKeydown"
            @focusout="handleTemplatePickerFocusout"
          >
            <button
              :id="templatePickerId"
              ref="templateTriggerRef"
              type="button"
              class="preview-template-select"
              aria-label="打印模板"
              aria-haspopup="listbox"
              :aria-expanded="templateDropdownOpen"
              :aria-controls="`${templatePickerId}-list`"
              :title="template?.name || '打印模板'"
              :disabled="templatesLoading || printing || sharingImage || !templateOptions.length"
              @click="toggleTemplateDropdown"
            >
              <span>{{ template?.name || (templatesLoading ? '正在加载模板...' : '暂无可用模板') }}</span>
              <ChevronDown :size="16" aria-hidden="true" />
            </button>
            <div v-if="templateDropdownOpen" class="preview-template-dropdown">
              <div class="preview-template-search">
                <Search :size="15" aria-hidden="true" />
                <input
                  ref="templateSearchRef"
                  v-model="templateSearch"
                  type="text"
                  inputmode="search"
                  autocomplete="off"
                  placeholder="搜索模板..."
                  aria-label="搜索打印模板"
                  role="combobox"
                  aria-autocomplete="list"
                  aria-expanded="true"
                  :aria-controls="`${templatePickerId}-list`"
                  :aria-activedescendant="filteredTemplates.length ? `${templatePickerId}-option-${activeTemplateIndex}` : undefined"
                />
                <button
                  type="button"
                  title="清空搜索"
                  aria-label="清空搜索"
                  :disabled="!templateSearch"
                  @click="clearTemplateSearch"
                >
                  <X :size="14" aria-hidden="true" />
                </button>
              </div>
              <div
                :id="`${templatePickerId}-list`"
                ref="templateListRef"
                class="preview-template-options"
                role="listbox"
                aria-label="打印模板"
              >
                <button
                  v-for="(option, index) in filteredTemplates"
                  :id="`${templatePickerId}-option-${index}`"
                  :key="option.id"
                  type="button"
                  role="option"
                  tabindex="-1"
                  class="preview-template-option"
                  :class="{ active: index === activeTemplateIndex }"
                  :aria-selected="String(option.id) === String(template?.id)"
                  @mousedown.prevent
                  @mouseenter="activeTemplateIndex = index"
                  @click="selectTemplateOption(option)"
                >
                  <span>
                    <strong>{{ option.name }}</strong>
                    <small>{{ option.paperType || '自定义' }} · {{ option.pageWidth }} × {{ option.pageHeight }} mm</small>
                  </span>
                  <Check v-if="String(option.id) === String(template?.id)" :size="16" aria-hidden="true" />
                </button>
                <div v-if="!filteredTemplates.length" class="preview-template-empty" role="status">
                  没有匹配的模板
                </div>
              </div>
            </div>
          </div>
          <dl v-if="template" class="preview-template-details">
            <div><dt>纸张</dt><dd>{{ template.paperType || '自定义' }}</dd></div>
            <div><dt>尺寸</dt><dd>{{ template.pageWidth || 210 }} × {{ template.pageHeight || 140 }} mm</dd></div>
          </dl>
        </aside>
        <div class="order-print-preview-body" :aria-busy="loading || templatesLoading">
          <div v-if="templatesLoading" class="preview-state">正在加载打印模板...</div>
          <div v-else-if="templatesError" class="preview-state preview-error">
            <span>{{ templatesError }}</span>
            <button type="button" class="preview-footer-button" @click="emit('reload-templates')">
              <RefreshCw :size="15" aria-hidden="true" />重新加载
            </button>
          </div>
          <div v-else-if="loading" class="preview-state">正在生成预览...</div>
          <div v-else-if="errorMessage" class="preview-state preview-error">
            {{ errorMessage }}
          </div>
          <iframe
            v-else-if="previewHtml"
            ref="previewFrameRef"
            class="preview-frame"
            title="订单打印预览"
            :srcdoc="previewHtml"
            @load="handlePreviewLoad"
          ></iframe>
          <div v-else class="preview-state">
            {{ templateSelection ? '暂无可用的打印模板' : '暂无可预览内容' }}
          </div>
        </div>
      </div>

      <div class="order-print-preview-footer">
        <span
          role="status"
          aria-live="polite"
          :class="{ 'preview-footer-error': imageShareError || printErrorMessage || imageShareUnavailableReason }"
        >
          {{ imageShareError || printErrorMessage || imageShareMessage || imageShareUnavailableReason || printDestinationHint }}
        </span>
        <div class="preview-footer-actions">
          <button
            type="button"
            class="preview-footer-button preview-icon-button"
            title="打印设置"
            aria-label="打印设置"
            :disabled="printing || sharingImage"
            @click="settingsVisible = true"
          >
            <Settings :size="16" aria-hidden="true" />
          </button>
          <button
            v-if="activePrintConfig.mode === 'clodop'"
            type="button"
            class="preview-footer-button preview-icon-button"
            title="重新检测打印服务"
            aria-label="重新检测打印服务"
            :disabled="checkingPrintService || printing || sharingImage"
            @click="recheckPrintService"
          >
            <RefreshCw :size="16" aria-hidden="true" />
          </button>
          <button
            type="button"
            class="preview-footer-button preview-share-button"
            :title="imageShareTitle"
            :disabled="!imageShareReady"
            :aria-busy="preparingImage || sharingImage"
            @click="handleShareImage"
          >
            <LoaderCircle v-if="preparingImage || sharingImage" :size="16" class="preview-share-spinner" aria-hidden="true" />
            <Share2 v-else :size="16" aria-hidden="true" />
            {{ imageShareLabel }}
          </button>
          <button
            type="button"
            class="preview-footer-button preview-print-button"
            :title="printButtonTitle"
            :disabled="!printReady"
            @click="handlePrint"
          >
            <Printer :size="16" aria-hidden="true" />
            {{ printing ? '正在连接...' : '打印' }}
          </button>
          <button type="button" class="preview-footer-button" @click="handleClose">关闭</button>
        </div>
      </div>
    </div>

    <print-designer
      ref="designerRef"
      :key="designerInstanceKey"
      class="preview-driver"
      @ready="handleDesignerReady"
    ></print-designer>
  </div>

  <PrintClientSettingsDialog
    :visible="settingsVisible"
    @close="settingsVisible = false"
    @saved="handlePrintConfigSaved"
  />
</template>

<script setup>
import { computed, getCurrentInstance, nextTick, ref, watch } from 'vue'
import { Check, ChevronDown, FileText, LoaderCircle, Printer, RefreshCw, Search, Settings, Share2, X } from '@lucide/vue'
import 'vue-print-designer'
import 'vue-print-designer/style.css'
import { openConfiguredPrintPreview } from '@/utils/lodopPrint'
import { getPrintClientConfig } from '@/utils/printClientConfig'
import { usePrintAvailability } from '@/composables/usePrintAvailability'
import { usePrintImageShare } from '@/composables/usePrintImageShare'
import { printImageFileName } from '@/utils/printImageShare'
import PrintClientSettingsDialog from '@/components/print/PrintClientSettingsDialog.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  template: { type: Object, default: null },
  templateSelection: { type: Boolean, default: false },
  templateOptions: { type: Array, default: () => [] },
  templatesLoading: { type: Boolean, default: false },
  templatesError: { type: String, default: '' },
  title: { type: String, default: '打印预览' },
  documentNumber: { type: [String, Number], default: '' },
  printEnabled: { type: Boolean, default: true },
  variables: { type: Object, default: () => ({}) },
  printer: { type: Object, default: null },
  previewLabel: { type: String, default: '当前订单数据预览' },
  autoPrint: { type: Boolean, default: false },
  trailingBlankRows: {
    type: Number,
    default: 1,
    validator: value => Number.isInteger(value) && value >= 0
  },
  hideZeroValues: { type: Boolean, default: true }
})

const emit = defineEmits(['close', 'select-template', 'reload-templates'])
const dialogRef = ref(null)
const designerRef = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const previewHtml = ref('')
const previewFrameRef = ref(null)
const renderedHtml = ref('')
const printing = ref(false)
const printErrorMessage = ref('')
const autoPrintConsumed = ref(false)
const settingsVisible = ref(false)
const templatePickerId = `preview-template-select-${getCurrentInstance().uid}`
const templatePickerRef = ref(null)
const templateTriggerRef = ref(null)
const templateSearchRef = ref(null)
const templateListRef = ref(null)
const templateDropdownOpen = ref(false)
const templateSearch = ref('')
const activeTemplateIndex = ref(0)
const {
  printConfig: activePrintConfig,
  checkingPrintService,
  printAvailable,
  printUnavailableReason,
  refreshPrintAvailability,
  cancelPrintCheck
} = usePrintAvailability(() => props.printer)
const renderedTemplateId = ref(null)
const designerInstanceKey = ref(0)
let renderRequestId = 0
const {
  preparing: preparingImage,
  sharing: sharingImage,
  ready: preparedImageReady,
  unavailableReason: imageShareUnavailableReason,
  label: imageShareLabel,
  title: imageShareTitle,
  error: imageShareError,
  message: imageShareMessage,
  prepare: prepareShareImage,
  share: shareImage,
  invalidate: invalidateShareImage
} = usePrintImageShare({
  fileName: computed(() => printImageFileName(
    props.template?.name || props.title,
    props.documentNumber || props.variables?.orderNumber || props.variables?.orderNo
  ))
})

const imageShareReady = computed(() => (
  props.visible && !props.templatesLoading && !props.templatesError &&
  !loading.value && !errorMessage.value && !printing.value &&
  !preparingImage.value && !sharingImage.value && Boolean(renderedHtml.value) &&
  renderedTemplateId.value === getTemplateIdentity(props.template) &&
  (preparedImageReady.value || Boolean(imageShareError.value))
))

const handleShareImage = () => {
  if (!imageShareReady.value) return
  printErrorMessage.value = ''
  if (preparedImageReady.value) shareImage()
  else prepareShareImage(previewFrameRef.value?.contentDocument?.getElementById('preview-paper-content'))
}

const filteredTemplates = computed(() => {
  const keyword = templateSearch.value.trim().toLocaleLowerCase()
  return props.templateOptions.filter(option => (
    [option.name, option.paperType, `${option.pageWidth}×${option.pageHeight}`]
      .join(' ')
      .toLocaleLowerCase()
      .includes(keyword)
  ))
})

const closeTemplateDropdown = (restoreFocus = false) => {
  templateDropdownOpen.value = false
  templateSearch.value = ''
  if (restoreFocus) templateTriggerRef.value?.focus()
}

const scrollActiveTemplateIntoView = () => {
  const list = templateListRef.value
  const option = list?.querySelector('.active')
  if (!option) return
  const top = option.offsetTop - list.offsetTop
  if (top < list.scrollTop) list.scrollTop = top
  else if (top + option.offsetHeight > list.scrollTop + list.clientHeight) {
    list.scrollTop = top + option.offsetHeight - list.clientHeight
  }
}

const openTemplateDropdown = async () => {
  if (props.templatesLoading || printing.value || sharingImage.value || !props.templateOptions.length) return
  templateSearch.value = ''
  activeTemplateIndex.value = Math.max(0, props.templateOptions.findIndex(option => (
    String(option.id) === String(props.template?.id)
  )))
  templateDropdownOpen.value = true
  await nextTick()
  templateSearchRef.value?.focus()
  scrollActiveTemplateIntoView()
}

const toggleTemplateDropdown = () => {
  if (templateDropdownOpen.value) closeTemplateDropdown()
  else openTemplateDropdown()
}

const selectTemplateOption = (option) => {
  if (!option || props.templatesLoading || printing.value || sharingImage.value) return
  emit('select-template', option.id)
  closeTemplateDropdown(true)
}

const clearTemplateSearch = () => {
  templateSearch.value = ''
  templateSearchRef.value?.focus()
}

const handleTemplatePickerKeydown = (event) => {
  if (event.isComposing) return
  if (event.key === 'Escape' && templateDropdownOpen.value) {
    event.preventDefault()
    event.stopPropagation()
    closeTemplateDropdown(true)
  } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!templateDropdownOpen.value) {
      openTemplateDropdown()
      return
    }
    const count = filteredTemplates.value.length
    if (count) {
      activeTemplateIndex.value = (activeTemplateIndex.value + (event.key === 'ArrowDown' ? 1 : -1) + count) % count
    }
  } else if (event.key === 'Enter' && event.target === templateSearchRef.value) {
    event.preventDefault()
    selectTemplateOption(filteredTemplates.value[activeTemplateIndex.value])
  }
}

const handleTemplatePickerFocusout = (event) => {
  if (!templatePickerRef.value?.contains(event.relatedTarget)) closeTemplateDropdown()
}

watch(filteredTemplates, () => {
  activeTemplateIndex.value = 0
})

watch(activeTemplateIndex, async () => {
  await nextTick()
  scrollActiveTemplateIntoView()
})

watch(templateDropdownOpen, (open, previousOpen, onCleanup) => {
  if (!open) return
  const handlePointerDown = (event) => {
    if (!templatePickerRef.value?.contains(event.target)) closeTemplateDropdown()
  }
  document.addEventListener('pointerdown', handlePointerDown)
  onCleanup(() => document.removeEventListener('pointerdown', handlePointerDown))
})

watch(
  [() => props.visible, () => props.templatesLoading, () => props.templateSelection, printing],
  () => closeTemplateDropdown()
)

const getTemplateIdentity = (template) => {
  const templateId = template?.id
  return templateId === undefined || templateId === null
    ? ''
    : String(templateId)
}

const resolvedPrinterName = computed(() => (
  activePrintConfig.value.mode === 'browser'
    ? '浏览器打印'
    : activePrintConfig.value.printerName || props.printer?.name || '未选择打印机'
))

const printDestinationHint = computed(() => {
  if (checkingPrintService.value) return '正在检测打印服务，预览不受影响。'
  if (!printAvailable.value) return printUnavailableReason.value
  return activePrintConfig.value.mode === 'browser'
    ? '点击打印后将打开浏览器打印窗口。'
    : `点击打印后将在 C-Lodop 中使用 ${resolvedPrinterName.value}。`
})

const printReady = computed(() => (
  props.visible &&
  props.printEnabled &&
  !props.templatesLoading &&
  !props.templatesError &&
  !loading.value &&
  !printing.value &&
  !sharingImage.value &&
  !checkingPrintService.value &&
  printAvailable.value &&
  Boolean(renderedHtml.value) &&
  Boolean(getTemplateIdentity(props.template)) &&
  renderedTemplateId.value === getTemplateIdentity(props.template)
))

const printButtonTitle = computed(() => {
  if (!props.printEnabled) return '打印功能已关闭'
  if (props.templatesLoading) return '正在加载打印模板'
  if (loading.value) return '正在生成打印内容'
  if (!renderedHtml.value) return '暂无可打印内容'
  if (!getTemplateIdentity(props.template)) return '请先保存模板后再打印'
  if (checkingPrintService.value) return '正在检测打印服务'
  if (!printAvailable.value) return printUnavailableReason.value
  return activePrintConfig.value.mode === 'browser'
    ? '使用浏览器打印'
    : `使用 ${resolvedPrinterName.value} 打印`
})

const normalizePrintHtml = (html, design) => {
  if (typeof DOMParser === 'undefined') return html

  const document = new DOMParser().parseFromString(
    `<body>${String(html || '')}</body>`,
    'text/html'
  )

  document.body.querySelectorAll('table th, table td').forEach((cell) => {
    cell.style.setProperty('vertical-align', 'middle', 'important')
    cell.style.setProperty('line-height', 'normal', 'important')
  })

  const textElements = (design?.pages || [])
    .flatMap(page => page?.elements || [])
    .filter(element => (
      String(element?.type || '').toLowerCase() === 'text' &&
      String(element?.style?.writingMode || '').startsWith('vertical')
    ))
  const wrappers = Array.from(document.body.querySelectorAll('[data-element-id]'))

  textElements.forEach((element) => {
    const writingMode = element.style.writingMode || 'vertical-rl'
    const textOrientation = element.style.textOrientation || 'mixed'
    const matchingWrappers = wrappers.filter(wrapper => (
      wrapper.getAttribute('data-element-id') === String(element.id)
    ))

    matchingWrappers.forEach((wrapper) => {
      wrapper.dataset.lodopVerticalWrapper = 'true'

      const contentNodes = Array.from(
        wrapper.querySelectorAll('[data-text-content="true"]')
      )
      const fallbackContent = contentNodes.length === 0
        ? Array.from(wrapper.querySelectorAll('div')).find(node => (
            node.children.length === 0 && node.textContent?.trim()
          ))
        : null
      const targets = [wrapper, ...contentNodes]
      const printableContentNodes = contentNodes.length > 0
        ? contentNodes
        : [fallbackContent || wrapper]

      if (fallbackContent) targets.push(fallbackContent)

      targets.forEach((target) => {
        target.style.setProperty('writing-mode', writingMode, 'important')
        target.style.setProperty('-webkit-writing-mode', writingMode, 'important')
        target.style.setProperty('text-orientation', textOrientation, 'important')
      })

      printableContentNodes.forEach((target) => {
        target.dataset.lodopVerticalText = 'true'
        target.dataset.lodopVerticalAlign = element.style.verticalAlign || 'top'
      })
    })
  })

  return document.body.innerHTML
}

const wrapPreviewHtml = (html) => `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      html, body { margin: 0; padding: 0; background: #eef1f5; }
      body { min-height: 100vh; display: flex; justify-content: safe center; padding: 24px; box-sizing: border-box; }
      #preview-paper-content { width: max-content; flex: 0 0 auto; align-self: flex-start; }
      * { box-sizing: border-box; }
      @media (max-width: 780px) {
        body { padding: 12px; }
      }
    </style>
  </head>
  <body><div id="preview-paper-content" data-preview-request="${renderRequestId}">${html}</div></body>
</html>`

const fitPreviewToWidth = () => {
  const previewDocument = previewFrameRef.value?.contentDocument
  const content = previewDocument?.getElementById('preview-paper-content')
  if (!content) return

  const pages = Array.from(content.querySelectorAll('.print-page'))
  const paperWidth = Math.max(0, ...pages.map(page => page.offsetWidth)) || content.scrollWidth
  if (!paperWidth) return

  const bodyStyle = previewDocument.defaultView.getComputedStyle(previewDocument.body)
  const availableWidth = previewDocument.documentElement.clientWidth -
    parseFloat(bodyStyle.paddingLeft) - parseFloat(bodyStyle.paddingRight)
  content.style.zoom = String(Math.min(1, Math.max(1, availableWidth) / paperWidth))
}

const handlePreviewLoad = () => {
  const content = previewFrameRef.value?.contentDocument?.getElementById('preview-paper-content')
  if (!props.visible || loading.value || content?.dataset.previewRequest !== String(renderRequestId)) return
  fitPreviewToWidth()
  prepareShareImage(content)
}

watch(previewFrameRef, (frame, previousFrame, onCleanup) => {
  if (!frame) return
  const observer = new ResizeObserver(fitPreviewToWidth)
  observer.observe(frame)
  onCleanup(() => observer.disconnect())
})

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
  invalidateShareImage()
  const designer = designerRef.value
  const template = props.template
  const requestId = ++renderRequestId
  if (!designer || !template) {
    loading.value = false
    return
  }

  const isCurrentRequest = () => (
    requestId === renderRequestId &&
    props.visible &&
    props.template === template
  )

  loading.value = true
  errorMessage.value = ''
  previewHtml.value = ''
  renderedHtml.value = ''
  renderedTemplateId.value = null
  printErrorMessage.value = ''

  try {
    const design = template.content || template.design || template.data
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
    const html = normalizePrintHtml(
      await designer.getPreviewHtml(),
      previewRuntime.design
    )
    if (!isCurrentRequest()) return

    renderedHtml.value = html
    previewHtml.value = wrapPreviewHtml(html)
    renderedTemplateId.value = getTemplateIdentity(template)
  } catch (error) {
    if (!isCurrentRequest()) return
    errorMessage.value = error?.message || '模板预览生成失败'
  } finally {
    if (isCurrentRequest()) loading.value = false
  }
}

const handleDesignerReady = async () => {
  await loadPreview()
}

const resetPreview = () => {
  invalidateShareImage()
  autoPrintConsumed.value = false
  loading.value = Boolean(props.template)
  errorMessage.value = ''
  previewHtml.value = ''
  renderedHtml.value = ''
  renderedTemplateId.value = null
  printErrorMessage.value = ''
  renderRequestId += 1
  designerInstanceKey.value += 1
}

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) {
      invalidateShareImage()
      cancelPrintCheck()
      settingsVisible.value = false
      autoPrintConsumed.value = false
      renderRequestId += 1
      loading.value = false
      renderedTemplateId.value = null
      renderedHtml.value = ''
      previewHtml.value = ''
      return
    }
    refreshPrintAvailability()
    resetPreview()
    await nextTick()
    if (props.visible) dialogRef.value?.focus()
  },
  { immediate: true }
)

watch(
  [() => props.variables, () => props.template, () => props.trailingBlankRows, () => props.hideZeroValues],
  () => {
    if (props.visible) resetPreview()
  },
  { deep: true }
)

const handlePrint = async () => {
  const currentTemplateId = getTemplateIdentity(props.template)
  if (!printReady.value) return
  const currentRenderRequestId = renderRequestId

  printing.value = true
  printErrorMessage.value = ''

  try {
    const available = await refreshPrintAvailability()
    if (
      !available ||
      !props.visible ||
      !props.printEnabled ||
      props.templatesLoading ||
      props.templatesError ||
      getTemplateIdentity(props.template) !== currentTemplateId ||
      currentRenderRequestId !== renderRequestId ||
      loading.value ||
      !renderedHtml.value
    ) return

    const orderNumber = props.variables?.orderNumber || props.variables?.orderNo || ''
    const taskName = [props.template?.name || '单据打印', orderNumber]
      .filter(Boolean)
      .join(' - ')

    await openConfiguredPrintPreview({
      html: renderedHtml.value,
      taskName,
      pageWidth: props.template?.pageWidth,
      pageHeight: props.template?.pageHeight,
      printer: props.printer
    })
    emit('close')
  } catch (error) {
    printErrorMessage.value = error?.message || '调用打印服务失败'
    refreshPrintAvailability()
  } finally {
    printing.value = false
  }
}

watch(
  [() => props.visible, () => props.autoPrint, renderedHtml, renderedTemplateId, loading, checkingPrintService, printAvailable],
  async ([visible, autoPrint, html]) => {
    if (!visible) {
      autoPrintConsumed.value = false
      return
    }
    const currentTemplateId = getTemplateIdentity(props.template)
    if (
      !autoPrint ||
      !html ||
      !currentTemplateId ||
      renderedTemplateId.value !== currentTemplateId ||
      loading.value ||
      checkingPrintService.value ||
      autoPrintConsumed.value ||
      printing.value
    ) {
      return
    }

    autoPrintConsumed.value = true
    if (!printAvailable.value) return
    await nextTick()
    await handlePrint()
  }
)

const handlePrintConfigSaved = (config) => {
  printErrorMessage.value = ''
  refreshPrintAvailability(config || getPrintClientConfig())
}

const recheckPrintService = () => {
  printErrorMessage.value = ''
  refreshPrintAvailability()
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

.order-print-preview-dialog.with-template-picker {
  width: min(1280px, 96vw);
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

.order-print-preview-header > div {
  min-width: 0;
  padding-right: 12px;
  overflow-wrap: anywhere;
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
  flex: 0 0 auto;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #64748b;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.preview-workspace {
  display: flex;
  min-height: 0;
  flex: 1;
}

.preview-template-sidebar {
  box-sizing: border-box;
  width: 228px;
  flex: 0 0 auto;
  padding: 16px;
  background: #fff;
  border-right: 1px solid #d9e0e8;
}

.preview-template-heading,
.preview-template-heading label {
  display: flex;
  align-items: center;
  gap: 7px;
}

.preview-template-heading {
  justify-content: space-between;
  margin-bottom: 10px;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.preview-template-heading label {
  white-space: nowrap;
}

.preview-template-heading .preview-template-reload {
  width: 28px;
  height: 28px;
}

.preview-template-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  height: 38px;
  padding: 0 9px;
  color: #172033;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  font: inherit;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
}

.preview-template-select span {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.preview-template-select svg {
  flex: 0 0 auto;
}

.preview-template-select:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

.preview-template-select:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

.preview-template-picker {
  position: relative;
  min-width: 0;
}

.preview-template-picker,
.preview-template-picker * {
  box-sizing: border-box;
}

.preview-template-dropdown {
  position: absolute;
  top: calc(100% + 5px);
  left: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-height: min(340px, calc(100dvh - 260px));
  overflow: hidden;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.14);
}

.preview-template-search {
  display: flex;
  align-items: center;
  gap: 7px;
  flex: 0 0 auto;
  padding: 6px 8px;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.preview-template-search > svg {
  flex: 0 0 auto;
}

.preview-template-search input {
  width: 100%;
  min-width: 0;
  height: 28px;
  padding: 0;
  color: #172033;
  font: inherit;
  font-size: 13px;
  background: transparent;
  border: 0;
  outline: none;
}

.preview-template-search button {
  display: inline-flex;
  width: 24px;
  height: 24px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 3px;
  cursor: pointer;
}

.preview-template-search button:disabled {
  visibility: hidden;
}

.preview-template-options {
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.preview-template-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  min-height: 54px;
  padding: 9px 10px;
  color: #334155;
  font: inherit;
  text-align: left;
  background: #fff;
  border: 0;
  cursor: pointer;
}

.preview-template-option.active {
  background: #f1f5f9;
}

.preview-template-option[aria-selected="true"] {
  color: #087f63;
  background: #ecfdf5;
}

.preview-template-option span {
  min-width: 0;
}

.preview-template-option strong,
.preview-template-option small {
  display: block;
  overflow-wrap: anywhere;
}

.preview-template-option strong {
  font-size: 13px;
  font-weight: 500;
}

.preview-template-option small {
  margin-top: 3px;
  color: #64748b;
  font-size: 11px;
}

.preview-template-option svg {
  flex: 0 0 auto;
}

.preview-template-empty {
  padding: 18px 10px;
  color: #64748b;
  font-size: 12px;
  text-align: center;
}

.preview-template-details {
  display: grid;
  gap: 12px;
  margin: 20px 0 0;
  color: #64748b;
  font-size: 12px;
}

.preview-template-details div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.preview-template-details dd {
  margin: 0;
  color: #475569;
  text-align: right;
  overflow-wrap: anywhere;
}

.order-print-preview-body {
  min-width: 0;
  min-height: 0;
  flex: 1;
}

.preview-frame {
  display: block;
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
  flex-direction: column;
  gap: 12px;
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

.order-print-preview-footer > span {
  min-width: 0;
  overflow-wrap: anywhere;
}

.preview-footer-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
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
  white-space: nowrap;
}

.preview-share-button {
  min-width: 100px;
}

.preview-share-spinner {
  animation: preview-share-spin 1s linear infinite;
}

@keyframes preview-share-spin {
  to { transform: rotate(360deg); }
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

.preview-icon-button {
  width: 34px;
  flex: 0 0 auto;
  padding: 0;
}

.preview-footer-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

  .order-print-preview-dialog,
  .order-print-preview-dialog.with-template-picker {
    width: 100vw;
    height: 100vh;
    height: 100dvh;
    border-radius: 0;
  }

  .preview-workspace {
    flex-direction: column;
  }

  .preview-template-sidebar {
    display: grid;
    grid-template-columns: 96px minmax(0, 1fr);
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 14px;
    border-right: 0;
    border-bottom: 1px solid #d9e0e8;
  }

  .preview-template-heading {
    margin: 0;
  }

  .preview-template-heading label svg,
  .preview-template-details {
    display: none;
  }

  .preview-template-search input {
    font-size: 16px;
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
