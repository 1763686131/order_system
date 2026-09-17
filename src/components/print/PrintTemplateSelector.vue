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
              <span>打印方式</span>
            </div>
            <button
              type="button"
              class="print-client-summary"
              @click="settingsVisible = true"
            >
              <span class="print-client-summary-icon" aria-hidden="true">
                <svg v-if="printConfig.mode === 'browser'" viewBox="0 0 24 24">
                  <rect x="3" y="4" width="18" height="13" rx="1"></rect>
                  <path d="M8 21h8M12 17v4"></path>
                </svg>
                <svg v-else viewBox="0 0 24 24">
                  <path d="M6 9V2h12v7"></path>
                  <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                  <path d="M6 14h12v8H6z"></path>
                </svg>
              </span>
              <span class="print-client-summary-copy">
                <strong>{{ printModeLabel }}</strong>
                <span>{{ printModeDescription }}</span>
              </span>
              <span class="print-client-settings-action">
                设置
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m9 6 6 6-6 6"></path>
                </svg>
              </span>
            </button>
            <p v-if="printConfigError" class="print-client-config-error">
              {{ printConfigError }}
            </p>
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

  <PrintClientSettingsDialog
    :visible="settingsVisible"
    @close="settingsVisible = false"
    @saved="handlePrintConfigSaved"
  />
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getTemplates } from '@/api/printTemplate'
import PrintClientSettingsDialog from '@/components/print/PrintClientSettingsDialog.vue'
import {
  getPrintClientConfig,
  getPrintServiceBaseUrl
} from '@/utils/printClientConfig'

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
const settingsVisible = ref(false)
const printConfig = ref(getPrintClientConfig())

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
  `选择一个${businessTypeLabel.value}模板和打印方式。`
))

const resolvedEmptyText = computed(() => (
  props.emptyText ||
  `暂无可用的${businessTypeLabel.value}打印模板，请先在“打印模板”中创建并启用模板。`
))

const resolvedFooterHint = computed(() => (
  props.footerHint || `将使用：${printModeLabel.value}`
))

const selectedTemplate = computed(() => (
  templates.value.find(template => (
    String(template.id) === String(selectedTemplateId.value)
  )) || null
))

const selectedPrinter = computed(() => (
  printConfig.value.mode === 'clodop' && printConfig.value.printerName
    ? { name: printConfig.value.printerName }
    : null
))

const selectionReady = computed(() => (
  Boolean(
    selectedTemplate.value &&
    (
      printConfig.value.mode === 'browser' ||
      printConfig.value.printerName
    )
  ) &&
  !loading.value
))

const printReady = computed(() => props.printEnabled && selectionReady.value)

const printModeLabel = computed(() => (
  printConfig.value.mode === 'browser'
    ? '浏览器打印'
    : `C-Lodop · ${printConfig.value.printerName || '未选择打印机'}`
))

const printModeDescription = computed(() => (
  printConfig.value.mode === 'browser'
    ? '预览和打印将交给浏览器打印窗口'
    : `${getPrintServiceBaseUrl(printConfig.value)} · 本地配置`
))

const printConfigError = computed(() => (
  printConfig.value.mode === 'clodop' && !printConfig.value.printerName
    ? '请先进入设置，检测并选择一台 C-Lodop 打印机。'
    : ''
))

const printButtonTitle = computed(() => {
  if (!props.printEnabled) return '打印功能已关闭'
  if (!selectedTemplate.value) return '请选择打印模板'
  if (printConfigError.value) return printConfigError.value
  return `使用 ${printModeLabel.value} 打印`
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

const handleClose = () => {
  settingsVisible.value = false
  emit('close')
}

const handlePreview = () => {
  if (!selectionReady.value) return
  emit('preview', selectedTemplate.value, selectedPrinter.value)
}

const handlePrint = () => {
  if (!printReady.value) return
  emit('print', selectedTemplate.value, selectedPrinter.value)
}

const handlePrintConfigSaved = (config) => {
  printConfig.value = config || getPrintClientConfig()
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
    printConfig.value = getPrintClientConfig()
    settingsVisible.value = false
    await nextTick()
    dialogRef.value?.focus()
    await loadTemplates()
  },
  { immediate: true }
)

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

.print-client-summary {
  display: grid;
  width: 100%;
  min-height: 68px;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: 11px;
  padding: 11px 13px;
  color: #283548;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 6px;
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.print-client-summary:hover {
  background: #f7fcfa;
  border-color: #a9e5d2;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.08);
}

.print-client-summary:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

.print-client-summary-icon {
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  color: #08745a;
  background: #e9f8f3;
  border-radius: 5px;
}

.print-client-summary-icon svg,
.print-client-settings-action svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.print-client-summary-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
}

.print-client-summary-copy strong,
.print-client-summary-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.print-client-summary-copy strong {
  font-size: 13px;
}

.print-client-summary-copy span {
  color: #8490a1;
  font-size: 11px;
}

.print-client-settings-action {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: #08745a;
  font-size: 12px;
  font-weight: 650;
}

.print-client-settings-action svg {
  width: 15px;
  height: 15px;
}

.print-client-config-error {
  margin: 7px 0 0;
  color: #b4232f;
  font-size: 11px;
  line-height: 1.5;
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
