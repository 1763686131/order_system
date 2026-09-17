<template>
  <Teleport to="body">
    <Transition name="print-template-modal">
      <div
        v-if="visible"
        class="print-template-dialog-overlay"
        @click.self="handleClose"
        @keydown.esc.prevent="handleEscape"
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

            <div class="print-selector-layout">
              <section class="print-selector-column print-client-column">
                <div class="print-selector-section-heading">
                  <span>打印机设置</span>
                  <small>本机配置</small>
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

                <dl class="print-client-facts">
                  <div>
                    <dt>输出方式</dt>
                    <dd>{{ printConfig.mode === 'browser' ? '浏览器' : 'C-Lodop' }}</dd>
                  </div>
                  <div>
                    <dt>目标设备</dt>
                    <dd>{{ printTargetLabel }}</dd>
                  </div>
                  <div>
                    <dt>服务地址</dt>
                    <dd>{{ printServiceLabel }}</dd>
                  </div>
                </dl>

                <p v-if="printConfigError" class="print-client-config-error">
                  {{ printConfigError }}
                </p>
              </section>

              <section class="print-selector-column print-template-column">
                <div class="print-selector-section-heading">
                  <span>打印模板</span>
                  <small v-if="templates.length">{{ templates.length }} 个可用</small>
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
                  <div
                    v-else
                    ref="templateSelectRef"
                    class="print-template-combobox"
                  >
                    <button
                      type="button"
                      class="print-template-trigger"
                      role="combobox"
                      aria-haspopup="listbox"
                      aria-controls="print-template-listbox"
                      :aria-expanded="templateDropdownOpen"
                      @click="toggleTemplateDropdown"
                    >
                      <span class="print-template-trigger-icon" aria-hidden="true">
                        <svg viewBox="0 0 24 24">
                          <path d="M5 3h11l3 3v15H5z"></path>
                          <path d="M16 3v4h4"></path>
                          <path d="M8 12h8M8 16h6"></path>
                        </svg>
                      </span>
                      <span class="print-template-trigger-copy">
                        <strong>{{ selectedTemplate?.name || '请选择打印模板' }}</strong>
                        <span>
                          {{ selectedTemplate ? getPaperLabel(selectedTemplate) : '未选择模板' }}
                        </span>
                      </span>
                      <span
                        v-if="selectedTemplate?.isDefault"
                        class="print-template-default-tag"
                      >
                        默认
                      </span>
                      <svg
                        class="print-template-chevron"
                        :class="{ open: templateDropdownOpen }"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path d="m7 9 5 5 5-5"></path>
                      </svg>
                    </button>

                    <Transition name="print-template-dropdown">
                      <div
                        v-if="templateDropdownOpen"
                        class="print-template-dropdown"
                      >
                        <label class="print-template-search">
                          <svg viewBox="0 0 24 24" aria-hidden="true">
                            <circle cx="11" cy="11" r="7"></circle>
                            <path d="m20 20-4-4"></path>
                          </svg>
                          <input
                            ref="templateSearchRef"
                            v-model.trim="templateSearch"
                            type="search"
                            placeholder="搜索模板名称或纸张"
                            aria-label="搜索打印模板"
                          />
                        </label>

                        <div
                          id="print-template-listbox"
                          class="print-template-dropdown-list"
                          role="listbox"
                          aria-label="打印模板"
                        >
                          <button
                            v-for="template in filteredTemplates"
                            :key="template.id"
                            type="button"
                            :class="[
                              'print-template-dropdown-option',
                              {
                                selected:
                                  String(selectedTemplateId) === String(template.id)
                              }
                            ]"
                            role="option"
                            :aria-selected="
                              String(selectedTemplateId) === String(template.id)
                            "
                            @click="selectTemplate(template)"
                          >
                            <span class="print-template-option-check" aria-hidden="true">
                              <svg viewBox="0 0 24 24">
                                <path d="m6 12 4 4 8-9"></path>
                              </svg>
                            </span>
                            <span class="print-template-option-copy">
                              <strong>{{ template.name }}</strong>
                              <span>{{ getPaperLabel(template) }}</span>
                            </span>
                            <span
                              v-if="template.isDefault"
                              class="print-template-default-tag"
                            >
                              默认
                            </span>
                          </button>

                          <div
                            v-if="!filteredTemplates.length"
                            class="print-template-no-results"
                          >
                            没有匹配的打印模板
                          </div>
                        </div>
                      </div>
                    </Transition>
                  </div>
                </div>
              </section>
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
const templateSelectRef = ref(null)
const templateSearchRef = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const templates = ref([])
const selectedTemplateId = ref(null)
const templateDropdownOpen = ref(false)
const templateSearch = ref('')
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

const filteredTemplates = computed(() => {
  const keyword = String(templateSearch.value || '').trim().toLocaleLowerCase()
  if (!keyword) return templates.value

  return templates.value.filter((template) => (
    [
      template.name,
      template.paperType,
      template.pageWidth,
      template.pageHeight,
      getPaperLabel(template)
    ]
      .filter(value => value !== undefined && value !== null)
      .join(' ')
      .toLocaleLowerCase()
      .includes(keyword)
  ))
})

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

const printTargetLabel = computed(() => (
  printConfig.value.mode === 'browser'
    ? '浏览器打印窗口'
    : printConfig.value.printerName || '未选择打印机'
))

const printServiceLabel = computed(() => (
  printConfig.value.mode === 'browser'
    ? '浏览器自动处理'
    : getPrintServiceBaseUrl(printConfig.value)
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
  templateDropdownOpen.value = false
  templateSearch.value = ''

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

const toggleTemplateDropdown = async () => {
  templateDropdownOpen.value = !templateDropdownOpen.value
  if (!templateDropdownOpen.value) {
    templateSearch.value = ''
    return
  }

  templateSearch.value = ''
  await nextTick()
  templateSearchRef.value?.focus()
}

const closeTemplateDropdown = () => {
  templateDropdownOpen.value = false
  templateSearch.value = ''
}

const selectTemplate = (template) => {
  selectedTemplateId.value = template.id
  closeTemplateDropdown()
}

const handleClose = () => {
  closeTemplateDropdown()
  settingsVisible.value = false
  emit('close')
}

const handleEscape = () => {
  if (templateDropdownOpen.value) {
    closeTemplateDropdown()
    return
  }
  handleClose()
}

const handleDocumentPointerDown = (event) => {
  if (
    templateDropdownOpen.value &&
    !templateSelectRef.value?.contains(event.target)
  ) {
    closeTemplateDropdown()
  }
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
    if (!visible) {
      closeTemplateDropdown()
      return
    }
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
  window.addEventListener('pointerdown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  window.removeEventListener('order-system-print-templates-updated', handleTemplatesUpdated)
  window.removeEventListener('pointerdown', handleDocumentPointerDown)
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
  width: min(880px, calc(100vw - 48px));
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
  min-height: 410px;
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 18px;
  background: #f8fafb;
}

.print-selector-layout {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  align-items: start;
}

.print-selector-column {
  min-width: 0;
}

.print-client-column {
  padding-right: 18px;
  border-right: 1px solid #e2e8f0;
}

.print-template-column {
  padding-left: 18px;
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

.print-selector-section-heading small {
  color: #8a96a8;
  font-size: 11px;
  font-weight: 500;
}

.print-selector-template-area {
  min-height: 72px;
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

.print-client-facts {
  margin: 16px 0 0;
  border-top: 1px solid #edf1f5;
}

.print-client-facts > div {
  display: grid;
  min-height: 38px;
  grid-template-columns: 72px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #edf1f5;
}

.print-client-facts dt,
.print-client-facts dd {
  margin: 0;
}

.print-client-facts dt {
  color: #8a96a8;
  font-size: 11px;
}

.print-client-facts dd {
  overflow: hidden;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.print-template-dialog-hint {
  margin: 0 0 13px;
  color: #647086;
  font-size: 12px;
}

.print-template-combobox {
  position: relative;
}

.print-template-trigger {
  display: grid;
  width: 100%;
  min-height: 70px;
  grid-template-columns: 36px minmax(0, 1fr) auto 18px;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  color: #283548;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.print-template-trigger:hover {
  border-color: #a9e5d2;
}

.print-template-trigger:focus-visible,
.print-template-combobox:focus-within .print-template-trigger {
  border-color: #0f9f78;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.12);
  outline: none;
}

.print-template-trigger-icon {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  color: #08745a;
  background: #e9f8f3;
  border-radius: 5px;
}

.print-template-trigger-icon svg,
.print-template-chevron,
.print-template-search svg,
.print-template-option-check svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.print-template-trigger-icon svg {
  width: 18px;
  height: 18px;
}

.print-template-trigger-copy,
.print-template-option-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
}

.print-template-trigger-copy strong,
.print-template-trigger-copy span,
.print-template-option-copy strong,
.print-template-option-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.print-template-trigger-copy strong,
.print-template-option-copy strong {
  font-size: 13px;
}

.print-template-trigger-copy span,
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

.print-template-chevron {
  width: 17px;
  height: 17px;
  color: #64748b;
  transition: transform 0.18s ease;
}

.print-template-chevron.open {
  transform: rotate(180deg);
}

.print-template-dropdown {
  position: absolute;
  z-index: 30;
  top: calc(100% + 7px);
  right: 0;
  left: 0;
  overflow: hidden;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.16);
}

.print-template-search {
  position: relative;
  display: block;
  padding: 10px;
  border-bottom: 1px solid #e2e8f0;
}

.print-template-search svg {
  position: absolute;
  top: 50%;
  left: 21px;
  width: 16px;
  height: 16px;
  color: #8a96a8;
  transform: translateY(-50%);
  pointer-events: none;
}

.print-template-search input {
  width: 100%;
  height: 36px;
  padding: 0 11px 0 34px;
  color: #273245;
  background: #f8fafc;
  border: 1px solid #d8e0e8;
  border-radius: 5px;
  font-size: 12px;
}

.print-template-search input:focus {
  background: #fff;
  border-color: #0f9f78;
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.1);
  outline: none;
}

.print-template-dropdown-list {
  max-height: 250px;
  overflow-y: auto;
  padding: 5px;
}

.print-template-dropdown-option {
  display: grid;
  width: 100%;
  min-height: 54px;
  grid-template-columns: 24px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  padding: 8px 9px;
  color: #283548;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  text-align: left;
}

.print-template-dropdown-option:hover,
.print-template-dropdown-option.selected {
  background: #edf9f5;
}

.print-template-dropdown-option:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: -2px;
}

.print-template-option-check {
  display: inline-flex;
  width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  color: transparent;
}

.print-template-option-check svg {
  width: 16px;
  height: 16px;
}

.print-template-dropdown-option.selected .print-template-option-check {
  color: #0f9f78;
}

.print-template-no-results {
  display: flex;
  min-height: 82px;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: #8a96a8;
  font-size: 12px;
}

.print-template-dropdown-enter-active,
.print-template-dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
  transform-origin: top;
}

.print-template-dropdown-enter-from,
.print-template-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
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

  .print-template-dialog-body {
    min-height: 0;
  }

  .print-selector-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .print-client-column {
    padding-right: 0;
    padding-bottom: 18px;
    border-right: 0;
    border-bottom: 1px solid #e2e8f0;
  }

  .print-template-column {
    padding-top: 18px;
    padding-left: 0;
  }

  .print-template-dropdown {
    position: static;
    margin-top: 7px;
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

@media (max-height: 650px) and (min-width: 781px) {
  .print-template-dialog-body {
    min-height: 0;
  }

  .print-template-dropdown {
    position: static;
    margin-top: 7px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .print-template-modal-enter-active,
  .print-template-modal-leave-active,
  .print-template-modal-enter-active .print-template-dialog,
  .print-template-modal-leave-active .print-template-dialog,
  .print-template-dropdown-enter-active,
  .print-template-dropdown-leave-active {
    transition: none;
  }
}
</style>
