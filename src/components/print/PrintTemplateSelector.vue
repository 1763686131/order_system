<template>
  <Teleport to="body">
    <Transition name="print-template-modal">
      <div
        v-if="visible"
        class="print-template-dialog-overlay"
        @click.self="handleClose"
        @keydown.esc.prevent="handleClose"
      >
        <section
          ref="dialogRef"
          class="print-template-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="print-template-dialog-title"
          tabindex="-1"
        >
          <header class="print-template-dialog-header">
            <div class="print-template-dialog-title">
              <span class="print-template-dialog-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M6 9V2h12v7"></path>
                  <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                  <path d="M6 14h12v8H6z"></path>
                </svg>
              </span>
              <div>
                <h3 id="print-template-dialog-title">{{ title }}</h3>
                <span>{{ documentNumber || '-' }}</span>
              </div>
            </div>
            <button
              class="print-template-dialog-close"
              type="button"
              title="关闭"
              @click="handleClose"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="m6 6 12 12M18 6 6 18"></path>
              </svg>
            </button>
          </header>

          <div class="print-template-dialog-body">
            <p class="print-template-dialog-hint">{{ resolvedDescription }}</p>

            <div class="print-selector-section-heading">
              <span>打印模板</span>
            </div>
            <div class="print-selector-template-area">
              <div v-if="loading" class="print-template-dialog-state compact">
                <span class="print-template-loading-mark" aria-hidden="true"></span>
                正在加载打印模板...
              </div>
              <div v-else-if="errorMessage" class="print-template-dialog-state compact error">
                {{ errorMessage }}
                <button type="button" @click="loadTemplates">重新加载</button>
              </div>
              <div v-else-if="!templates.length" class="print-template-dialog-state compact">
                {{ resolvedEmptyText }}
              </div>
              <div v-else class="print-template-options" role="radiogroup" aria-label="打印模板">
                <button
                  v-for="template in templates"
                  :key="template.id"
                  type="button"
                  :class="[
                    'print-template-option',
                    { selected: String(selectedTemplateId) === String(template.id) }
                  ]"
                  role="radio"
                  :aria-checked="String(selectedTemplateId) === String(template.id)"
                  @click="selectedTemplateId = template.id"
                  @dblclick="handlePreview"
                >
                  <span class="print-template-radio" aria-hidden="true"></span>
                  <span class="print-template-option-copy">
                    <strong>{{ template.name }}</strong>
                    <span>{{ getPaperLabel(template) }}</span>
                  </span>
                  <span v-if="template.isDefault" class="print-template-default-tag">默认</span>
                </button>
              </div>
            </div>

            <div class="print-selector-section-heading printer-heading">
              <span>本地打印机</span>
              <button
                type="button"
                class="printer-refresh-button"
                title="重新检测本地打印机"
                :disabled="printerLoading"
                @click="loadPrinters"
              >
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="M20 11a8 8 0 1 0 2 5"></path>
                  <path d="M20 4v7h-7"></path>
                </svg>
              </button>
            </div>
            <div class="printer-selector-area">
              <div v-if="printerLoading" class="printer-selector-state">
                <span class="print-template-loading-mark small" aria-hidden="true"></span>
                正在读取本地打印机...
              </div>
              <div v-else-if="printerErrorMessage" class="printer-selector-state error">
                <span>{{ printerErrorMessage }}</span>
                <button type="button" @click="loadPrinters">重新检测</button>
              </div>
              <template v-else>
                <select
                  v-model="selectedPrinterName"
                  class="printer-select"
                  aria-label="本地打印机"
                  :disabled="!printers.length"
                >
                  <option value="" disabled>请选择本地打印机</option>
                  <option
                    v-for="printer in printers"
                    :key="`${printer.index}-${printer.name}`"
                    :value="printer.name"
                  >
                    {{ printer.name }}{{ printer.isDefault ? '（默认）' : '' }}
                  </option>
                </select>
                <div v-if="selectedPrinter" class="printer-meta">
                  <span>{{ selectedPrinter.driverName || '系统打印驱动' }}</span>
                  <span v-if="selectedPrinter.portName">{{ selectedPrinter.portName }}</span>
                </div>
                <div v-else class="printer-selector-state">
                  未检测到可用的本地打印机
                </div>
              </template>
            </div>
          </div>

          <footer class="print-template-dialog-footer">
            <span>{{ resolvedFooterHint }}</span>
            <div class="print-template-dialog-actions">
              <button
                type="button"
                class="selector-button selector-button-secondary"
                @click="handleClose"
              >
                取消
              </button>
              <button
                type="button"
                class="selector-button selector-button-primary"
                :disabled="!selectionReady"
                @click="handlePreview"
              >
                预览
              </button>
              <button
                type="button"
                class="selector-button selector-print-button"
                :title="printButtonTitle"
                :disabled="!printReady"
                @click="handlePrint"
              >
                打印
              </button>
            </div>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getTemplates } from '@/api/printTemplate'
import { getLocalPrinters } from '@/utils/lodopPrint'

const printerStorageKey = 'order-system-selected-printer'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  businessType: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: '打印单据'
  },
  documentNumber: {
    type: [String, Number],
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  emptyText: {
    type: String,
    default: ''
  },
  footerHint: {
    type: String,
    default: ''
  },
  printEnabled: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close', 'preview', 'print'])

const dialogRef = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const templates = ref([])
const selectedTemplateId = ref(null)
const printerLoading = ref(false)
const printerErrorMessage = ref('')
const printers = ref([])
const selectedPrinterName = ref('')

const businessTypeLabels = {
  sale: '销售',
  purchase: '采购',
  return: '退货',
  transfer: '调拨',
  inventory: '盘点',
  receipt: '收款',
  payment: '付款'
}

const businessTypeLabel = computed(() => (
  businessTypeLabels[props.businessType] || '当前业务'
))

const resolvedDescription = computed(() => (
  props.description ||
  `选择一个${businessTypeLabel.value}模板和本地打印机。`
))

const resolvedEmptyText = computed(() => (
  props.emptyText ||
  `暂无可用的${businessTypeLabel.value}打印模板，请先在“打印模板”中创建并启用模板。`
))

const resolvedFooterHint = computed(() => (
  props.footerHint ||
  (
    selectedPrinter.value
      ? `将使用：${selectedPrinter.value.name}`
      : '请选择模板和本地打印机。'
  )
))

const selectedTemplate = computed(() => (
  templates.value.find(template => (
    String(template.id) === String(selectedTemplateId.value)
  )) || null
))

const selectedPrinter = computed(() => (
  printers.value.find(printer => printer.name === selectedPrinterName.value) || null
))

const selectionReady = computed(() => (
  Boolean(selectedTemplate.value && selectedPrinter.value) &&
  !loading.value &&
  !printerLoading.value
))

const printReady = computed(() => props.printEnabled && selectionReady.value)

const printButtonTitle = computed(() => {
  if (!props.printEnabled) return '打印功能已关闭'
  if (printerLoading.value) return '正在读取本地打印机'
  if (printerErrorMessage.value) return printerErrorMessage.value
  if (!selectedTemplate.value) return '请选择打印模板'
  if (!selectedPrinter.value) return '请选择本地打印机'
  return `使用 ${selectedPrinter.value.name} 打印`
})

const getPaperLabel = (template) => {
  const width = template?.pageWidth || 210
  const height = template?.pageHeight || 140
  return `${template?.paperType || '自定义纸张'} · ${width}×${height}mm`
}

const loadTemplates = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await getTemplates({
      businessType: props.businessType,
      enabledOnly: true
    })

    if (!response?.success) {
      throw new Error(response?.message || '打印模板加载失败')
    }

    templates.value = (response.data || [])
      .filter(template => (
        template.enabled &&
        template.businessType === props.businessType &&
        (template.content || template.design || template.data)
      ))
      .sort((left, right) => Number(right.isDefault) - Number(left.isDefault))

    selectedTemplateId.value = (
      templates.value.find(template => template.isDefault) ||
      templates.value[0] ||
      {}
    ).id ?? null
  } catch (error) {
    console.error(`加载${businessTypeLabel.value}打印模板失败:`, error)
    templates.value = []
    selectedTemplateId.value = null
    errorMessage.value = error?.message || '打印模板加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const loadPrinters = async () => {
  printerLoading.value = true
  printerErrorMessage.value = ''

  try {
    let storedPrinterName = ''
    try {
      storedPrinterName = localStorage.getItem(printerStorageKey) || ''
    } catch {
      storedPrinterName = ''
    }

    const previousSelection = selectedPrinterName.value || storedPrinterName
    printers.value = await getLocalPrinters()

    selectedPrinterName.value = (
      printers.value.find(printer => printer.name === previousSelection) ||
      printers.value.find(printer => printer.isDefault) ||
      printers.value[0] ||
      {}
    ).name || ''

    if (!printers.value.length) {
      printerErrorMessage.value = 'C-Lodop 未检测到本地打印机。'
    }
  } catch (error) {
    console.error('读取本地打印机失败:', error)
    printers.value = []
    selectedPrinterName.value = ''
    printerErrorMessage.value = error?.message || '本地打印机读取失败'
  } finally {
    printerLoading.value = false
  }
}

const handleClose = () => emit('close')

const handlePreview = () => {
  if (!selectionReady.value) return
  emit('preview', selectedTemplate.value, selectedPrinter.value)
}

const handlePrint = () => {
  if (!printReady.value) return
  emit('print', selectedTemplate.value, selectedPrinter.value)
}

const handleTemplatesUpdated = () => {
  if (props.visible) {
    loadTemplates()
  }
}

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) return
    selectedTemplateId.value = null
    await nextTick()
    dialogRef.value?.focus()
    await Promise.all([loadTemplates(), loadPrinters()])
  },
  { immediate: true }
)

watch(selectedPrinterName, (name) => {
  if (!name) return
  try {
    localStorage.setItem(printerStorageKey, name)
  } catch {
    // Local storage may be disabled; the current selection still remains usable.
  }
})

watch(
  () => props.businessType,
  () => {
    if (props.visible) {
      loadTemplates()
    }
  }
)

onMounted(() => {
  window.addEventListener('order-system-print-templates-updated', handleTemplatesUpdated)
})

onBeforeUnmount(() => {
  window.removeEventListener('order-system-print-templates-updated', handleTemplatesUpdated)
})
</script>

<style scoped>
.print-template-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147482500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(1px);
}

.print-template-dialog {
  display: flex;
  width: min(620px, calc(100vw - 48px));
  max-height: min(720px, calc(100vh - 48px));
  flex-direction: column;
  overflow: hidden;
  color: #172033;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 8px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
  outline: none;
}

.print-template-dialog-header {
  display: flex;
  min-height: 74px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid #e2e8f0;
}

.print-template-dialog-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.print-template-dialog-icon {
  display: inline-flex;
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  align-items: center;
  justify-content: center;
  color: #08745a;
  background: #e9f8f3;
  border-radius: 7px;
}

.print-template-dialog-icon svg,
.print-template-dialog-close svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.print-template-dialog-title > div {
  min-width: 0;
}

.print-template-dialog-title h3 {
  margin: 0 0 4px;
  font-size: 16px;
  letter-spacing: 0;
}

.print-template-dialog-title span:not(.print-template-dialog-icon) {
  display: block;
  overflow: hidden;
  color: #7a8698;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.print-template-dialog-close {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #68758a;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
}

.print-template-dialog-close:hover {
  color: #273245;
  background: #f0f3f6;
}

.print-template-dialog-body {
  min-height: 220px;
  overflow-y: auto;
  padding: 18px;
  background: #f8fafb;
}

.print-selector-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 8px;
  color: #334155;
  font-size: 12px;
  font-weight: 650;
}

.print-selector-template-area {
  min-height: 72px;
}

.printer-heading {
  margin-top: 18px;
}

.printer-refresh-button {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}

.printer-refresh-button:hover:not(:disabled) {
  color: #08745a;
  background: #e9f8f3;
}

.printer-refresh-button:disabled {
  cursor: wait;
  opacity: 0.5;
}

.printer-refresh-button svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.printer-selector-area {
  min-height: 70px;
}

.printer-select {
  width: 100%;
  height: 40px;
  padding: 0 36px 0 12px;
  color: #273245;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  font-size: 13px;
}

.printer-select:focus {
  border-color: #0f9f78;
  outline: 2px solid rgba(15, 159, 120, 0.12);
}

.printer-meta {
  display: flex;
  min-width: 0;
  justify-content: space-between;
  gap: 12px;
  margin-top: 7px;
  color: #8490a1;
  font-size: 11px;
}

.printer-meta span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.printer-selector-state {
  min-height: 40px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7a8698;
  font-size: 12px;
}

.printer-selector-state.error {
  color: #b4232f;
}

.printer-selector-state button {
  flex: 0 0 auto;
  padding: 4px 8px;
  color: #08745a;
  background: #fff;
  border: 1px solid #a9e5d2;
  border-radius: 4px;
  cursor: pointer;
}

.print-template-dialog-hint {
  margin: 0 0 13px;
  color: #647086;
  font-size: 12px;
}

.print-template-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.print-template-option {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  align-items: center;
  gap: 11px;
  width: 100%;
  min-height: 64px;
  padding: 11px 13px;
  color: #283548;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
}

.print-template-option:hover {
  border-color: #a9e5d2;
  background: #f7fcfa;
}

.print-template-option.selected {
  border-color: #0f9f78;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.12);
}

.print-template-radio {
  position: relative;
  width: 16px;
  height: 16px;
  border: 1px solid #aab4c3;
  border-radius: 50%;
}

.print-template-option.selected .print-template-radio {
  border-color: #0f9f78;
}

.print-template-option.selected .print-template-radio::after {
  position: absolute;
  inset: 3px;
  content: '';
  background: #0f9f78;
  border-radius: 50%;
}

.print-template-option-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
}

.print-template-option-copy strong,
.print-template-option-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.print-template-option-copy strong {
  font-size: 13px;
}

.print-template-option-copy span {
  color: #8490a1;
  font-size: 11px;
}

.print-template-default-tag {
  padding: 3px 7px;
  color: #08745a;
  background: #e9f8f3;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 650;
}

.print-template-dialog-state {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  flex-direction: column;
  padding: 24px;
  color: #7a8698;
  font-size: 13px;
  text-align: center;
}

.print-template-dialog-state.compact {
  min-height: 72px;
  padding: 12px;
}

.print-template-dialog-state.error {
  color: #b4232f;
}

.print-template-dialog-state button {
  height: 30px;
  padding: 0 12px;
  color: #08745a;
  background: #fff;
  border: 1px solid #a9e5d2;
  border-radius: 4px;
  cursor: pointer;
}

.print-template-loading-mark {
  width: 24px;
  height: 24px;
  border: 2px solid #d9e0e8;
  border-top-color: #0f9f78;
  border-radius: 50%;
  animation: print-template-spin 0.8s linear infinite;
}

.print-template-loading-mark.small {
  width: 18px;
  height: 18px;
}

.print-template-dialog-footer {
  display: flex;
  min-height: 68px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 18px;
  border-top: 1px solid #e2e8f0;
}

.print-template-dialog-footer > span {
  color: #8a96a8;
  font-size: 11px;
}

.print-template-dialog-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.selector-button {
  height: 38px;
  min-width: 72px;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.selector-button-secondary {
  color: #475569;
  background: #fff;
  border-color: #94a3b8;
}

.selector-button-secondary:hover {
  color: #08745a;
  border-color: #0f9f78;
}

.selector-button-primary {
  color: #08745a;
  background: #e9f8f3;
  border-color: #a9e5d2;
}

.selector-button-primary:hover:not(:disabled) {
  color: #065f49;
  background: #d8f3ea;
  border-color: #68cdb0;
}

.selector-print-button {
  color: #fff;
  background: #0f9f78;
  border-color: #0f9f78;
}

.selector-print-button:hover:not(:disabled) {
  background: #08745a;
  border-color: #08745a;
}

.selector-button:disabled,
.selector-print-button:disabled {
  color: #94a3b8;
  background: #f1f5f9;
  border-color: #d8e0e8;
  cursor: not-allowed;
}

.print-template-modal-enter-active,
.print-template-modal-leave-active {
  transition: opacity 0.2s ease;
}

.print-template-modal-enter-active .print-template-dialog,
.print-template-modal-leave-active .print-template-dialog {
  transition: transform 0.22s ease, opacity 0.2s ease;
}

.print-template-modal-enter-from,
.print-template-modal-leave-to {
  opacity: 0;
}

.print-template-modal-enter-from .print-template-dialog,
.print-template-modal-leave-to .print-template-dialog {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
}

@keyframes print-template-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 780px) {
  .print-template-dialog-overlay {
    padding: 0;
  }

  .print-template-dialog {
    width: 100vw;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
  }

  .print-template-dialog-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .print-template-dialog-actions {
    width: 100%;
  }

  .selector-button {
    flex: 1;
    min-width: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .print-template-modal-enter-active,
  .print-template-modal-leave-active,
  .print-template-modal-enter-active .print-template-dialog,
  .print-template-modal-leave-active .print-template-dialog {
    transition: none;
  }
}
</style>
