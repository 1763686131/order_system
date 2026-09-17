<template>
  <Teleport to="body">
    <Transition name="print-client-settings">
      <div
        v-if="visible"
        class="print-client-settings-overlay"
        @click.self="handleClose"
        @keydown.esc.prevent="handleClose"
      >
        <section
          ref="dialogRef"
          class="print-client-settings-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="print-client-settings-title"
          tabindex="-1"
        >
          <header class="settings-header">
            <div>
              <h3 id="print-client-settings-title">打印方式设置</h3>
              <span>配置仅保存在当前浏览器</span>
            </div>
            <button type="button" title="关闭" @click="handleClose">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12M18 6 6 18"></path>
              </svg>
            </button>
          </header>

          <div class="settings-body">
            <div class="mode-switch" role="radiogroup" aria-label="打印方式">
              <button
                type="button"
                :class="{ active: form.mode === 'browser' }"
                role="radio"
                :aria-checked="form.mode === 'browser'"
                @click="form.mode = 'browser'"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <rect x="3" y="4" width="18" height="13" rx="1"></rect>
                  <path d="M8 21h8M12 17v4"></path>
                </svg>
                浏览器打印
              </button>
              <button
                type="button"
                :class="{ active: form.mode === 'clodop' }"
                role="radio"
                :aria-checked="form.mode === 'clodop'"
                @click="form.mode = 'clodop'"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 9V2h12v7"></path>
                  <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                  <path d="M6 14h12v8H6z"></path>
                </svg>
                C-Lodop
              </button>
            </div>

            <div v-if="form.mode === 'browser'" class="browser-mode-summary">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="m8 12 2.7 2.7L16.5 9"></path>
              </svg>
              <div>
                <strong>浏览器打印窗口</strong>
                <span>预览和打印将使用浏览器当前可用的打印设备。</span>
              </div>
            </div>

            <div v-else class="clodop-settings">
              <div class="service-fields">
                <label>
                  <span>协议</span>
                  <select v-model="form.protocol">
                    <option value="http">HTTP</option>
                    <option value="https">HTTPS</option>
                  </select>
                </label>
                <label class="host-field">
                  <span>服务地址</span>
                  <input v-model.trim="form.host" type="text" placeholder="localhost" />
                </label>
                <label>
                  <span>端口</span>
                  <input
                    v-model.number="form.port"
                    type="number"
                    min="1"
                    max="65535"
                    :placeholder="form.protocol === 'https' ? '8443' : '8000'"
                  />
                </label>
              </div>

              <div class="service-endpoint">
                <span>{{ serviceEndpoint }}</span>
                <button
                  type="button"
                  :disabled="detecting"
                  @click="handleDetect"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M20 11a8 8 0 1 0 2 5"></path>
                    <path d="M20 4v7h-7"></path>
                  </svg>
                  {{ detecting ? '检测中...' : '自动检测' }}
                </button>
              </div>

              <label class="printer-field">
                <span>本地打印机</span>
                <select v-model="form.printerName">
                  <option value="" disabled>请选择 C-Lodop 打印机</option>
                  <option
                    v-if="storedPrinterOption"
                    :value="storedPrinterOption"
                  >
                    {{ storedPrinterOption }}
                  </option>
                  <option
                    v-for="printer in printers"
                    :key="`${printer.index}-${printer.name}`"
                    :value="printer.name"
                  >
                    {{ printer.name }}{{ printer.isDefault ? '（默认）' : '' }}
                  </option>
                </select>
              </label>

              <div
                v-if="detectionMessage"
                :class="['detection-status', { error: detectionError }]"
                :role="detectionError ? 'alert' : 'status'"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="9"></circle>
                  <path v-if="!detectionError" d="m8 12 2.7 2.7L16.5 9"></path>
                  <path v-else d="M12 8v5M12 17h.01"></path>
                </svg>
                <span>{{ detectionMessage }}</span>
              </div>
            </div>
          </div>

          <footer class="settings-footer">
            <button type="button" class="settings-cancel" @click="handleClose">
              取消
            </button>
            <button
              type="button"
              class="settings-save"
              :disabled="!canSave"
              @click="handleSave"
            >
              保存设置
            </button>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { detectLodopService } from '@/utils/lodopPrint'
import {
  getPrintClientConfig,
  getPrintServiceBaseUrl,
  normalizePrintClientConfig,
  savePrintClientConfig
} from '@/utils/printClientConfig'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'saved'])
const dialogRef = ref(null)
const form = ref(getPrintClientConfig())
const printers = ref([])
const detecting = ref(false)
const detectionMessage = ref('')
const detectionError = ref(false)

const serviceEndpoint = computed(() => getPrintServiceBaseUrl(form.value))

const storedPrinterOption = computed(() => {
  const name = String(form.value.printerName || '').trim()
  if (!name || printers.value.some(printer => printer.name === name)) return ''
  return name
})

const canSave = computed(() => {
  if (form.value.mode === 'browser') return true
  const port = Number(form.value.port)
  return Boolean(
    String(form.value.host || '').trim() &&
    Number.isInteger(port) &&
    port > 0 &&
    port <= 65535 &&
    String(form.value.printerName || '').trim()
  )
})

const resetDialog = async () => {
  form.value = getPrintClientConfig()
  printers.value = []
  detecting.value = false
  detectionMessage.value = ''
  detectionError.value = false
  await nextTick()
  dialogRef.value?.focus()
}

const handleDetect = async () => {
  if (detecting.value) return

  detecting.value = true
  detectionMessage.value = ''
  detectionError.value = false

  try {
    const result = await detectLodopService(form.value)
    printers.value = result.printers
    const selectedPrinter = (
      printers.value.find(printer => printer.name === form.value.printerName) ||
      printers.value.find(printer => printer.isDefault) ||
      printers.value[0] ||
      null
    )

    form.value = normalizePrintClientConfig({
      ...form.value,
      ...result.config,
      mode: 'clodop',
      printerName: selectedPrinter?.name || form.value.printerName
    })

    const saved = savePrintClientConfig(form.value)
    detectionMessage.value = printers.value.length
      ? `检测成功，发现 ${printers.value.length} 台打印机，配置已保存。`
      : 'C-Lodop 连接成功，但没有检测到本地打印机。'
    emit('saved', saved)
  } catch (error) {
    printers.value = []
    detectionError.value = true
    detectionMessage.value = error?.message || 'C-Lodop 服务检测失败'
  } finally {
    detecting.value = false
  }
}

const handleSave = () => {
  if (!canSave.value) return
  const saved = savePrintClientConfig(form.value)
  emit('saved', saved)
  emit('close')
}

const handleClose = () => emit('close')

watch(
  () => props.visible,
  (visible) => {
    if (visible) resetDialog()
  },
  { immediate: true }
)

watch(
  () => form.value.protocol,
  (protocol, previousProtocol) => {
    if (protocol === previousProtocol) return
    if (protocol === 'https' && Number(form.value.port) === 8000) {
      form.value.port = 8443
    } else if (protocol === 'http' && Number(form.value.port) === 8443) {
      form.value.port = 8000
    }
  }
)
</script>

<style scoped>
.print-client-settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147482800;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(1px);
}

.print-client-settings-dialog {
  width: min(620px, calc(100vw - 48px));
  max-height: min(760px, calc(100vh - 48px));
  overflow: hidden;
  color: #172033;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
  outline: none;
}

.settings-header {
  display: flex;
  min-height: 72px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-bottom: 1px solid #e2e8f0;
}

.settings-header h3 {
  margin: 0 0 4px;
  font-size: 17px;
}

.settings-header span {
  color: #8a96a8;
  font-size: 12px;
}

.settings-header button {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
}

.settings-header button:hover {
  color: #172033;
  background: #f1f5f9;
}

.settings-header svg,
.mode-switch svg,
.service-endpoint svg,
.detection-status svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.settings-body {
  padding: 18px;
  overflow-y: auto;
  background: #f8fafb;
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  padding: 4px;
  background: #eef2f6;
  border-radius: 8px;
}

.mode-switch button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #596579;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.mode-switch button.active {
  color: #fff;
  background: #0f9f78;
  border-color: #0f9f78;
  box-shadow: 0 2px 6px rgba(15, 159, 120, 0.2);
}

.browser-mode-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 88px;
  margin-top: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.browser-mode-summary > svg {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  fill: none;
  stroke: #0f9f78;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.browser-mode-summary div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
}

.browser-mode-summary strong {
  font-size: 14px;
}

.browser-mode-summary span {
  color: #7b8798;
  font-size: 12px;
}

.clodop-settings {
  margin-top: 16px;
}

.service-fields {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr) 120px;
  gap: 10px;
}

.service-fields label,
.printer-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
}

.service-fields input,
.service-fields select,
.printer-field select {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  color: #172033;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  font-size: 13px;
}

.service-fields input:focus,
.service-fields select:focus,
.printer-field select:focus {
  border-color: #0f9f78;
  outline: 2px solid rgba(15, 159, 120, 0.14);
}

.service-endpoint {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 5px;
}

.service-endpoint > span {
  overflow: hidden;
  color: #64748b;
  font-family: Consolas, monospace;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.service-endpoint button {
  display: inline-flex;
  height: 32px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 11px;
  color: #08745a;
  background: #e9f8f3;
  border: 1px solid #a9e5d2;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.service-endpoint button:disabled {
  cursor: wait;
  opacity: 0.55;
}

.printer-field {
  margin-top: 14px;
}

.detection-status {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  color: #13734f;
  font-size: 12px;
  line-height: 1.5;
}

.detection-status svg {
  flex: 0 0 18px;
}

.detection-status.error {
  color: #b4232f;
  white-space: pre-line;
}

.settings-footer {
  display: flex;
  min-height: 68px;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 13px 18px;
  border-top: 1px solid #e2e8f0;
}

.settings-cancel,
.settings-save {
  height: 38px;
  min-width: 106px;
  padding: 0 18px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.settings-cancel {
  color: #596579;
  background: #fff;
  border: 1px solid #cbd5e1;
}

.settings-cancel:hover {
  color: #08745a;
  background: #e9f8f3;
  border-color: #a9e5d2;
}

.settings-save {
  color: #fff;
  background: #0f9f78;
  border: 1px solid #0f9f78;
}

.settings-save:hover:not(:disabled) {
  background: #08745a;
  border-color: #08745a;
}

.settings-save:disabled {
  color: #94a3b8;
  background: #f1f5f9;
  border-color: #d8e0e8;
  cursor: not-allowed;
}

.print-client-settings-enter-active,
.print-client-settings-leave-active {
  transition: opacity 0.18s ease;
}

.print-client-settings-enter-from,
.print-client-settings-leave-to {
  opacity: 0;
}

@media (max-width: 780px) {
  .print-client-settings-overlay {
    padding: 0;
  }

  .print-client-settings-dialog {
    width: 100vw;
    max-height: 100vh;
    border-radius: 0;
  }

  .service-fields {
    grid-template-columns: 1fr;
  }
}
</style>
