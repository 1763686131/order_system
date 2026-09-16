<template>
  <teleport to="body">
    <div v-if="visible" id="uploadMaterialModal" class="material-modal-mask">
      <section class="material-modal" role="dialog" aria-modal="true" aria-labelledby="materialModalTitle">
        <header class="material-modal-header">
          <div>
            <span>原材料出库</span>
            <h2 id="materialModalTitle">录入生产领料数据</h2>
            <p>提交后生成待审核草稿，管理员审核后才扣减库存</p>
          </div>
          <button type="button" aria-label="关闭" @click="handleClose">×</button>
        </header>

        <div v-if="configLoading" class="modal-state">正在加载出库配置...</div>
        <div v-else-if="configError" class="modal-state error-state">
          <strong>暂时无法录入</strong>
          <span>{{ configError }}</span>
          <button type="button" @click="fetchConfig">重新加载</button>
        </div>

        <div v-else class="material-modal-body">
          <div class="upload-inputs-area">
            <section class="material-summary">
              <div class="summary-heading">
                <span>本次领用原材料</span>
                <strong>{{ currentProduct?.name || '尚未配置' }}</strong>
              </div>
              <div class="summary-grid">
                <div>
                  <span>规格</span>
                  <strong>{{ currentProduct?.specification || '-' }}</strong>
                </div>
                <div>
                  <span>计量单位</span>
                  <strong>{{ currentProduct?.unit || '-' }}</strong>
                </div>
                <div>
                  <span>门店</span>
                  <strong>{{ currentStore?.name || '-' }}</strong>
                </div>
                <div>
                  <span>出库仓库</span>
                  <strong>{{ currentWarehouse?.name || '-' }}</strong>
                </div>
              </div>
              <div v-if="settings.showCurrentStock" class="stock-line">
                当前可用库存
                <strong>{{ formatNumber(currentProduct?.currentStock) }} {{ currentProduct?.unit }}</strong>
              </div>
            </section>

            <div class="number-fields">
              <label class="touch-field">
                <span>原材料出库数量（{{ currentProduct?.unit || '单位' }}）</span>
                <input
                  id="materialInputUse"
                  v-model="usedValue"
                  readonly
                  inputmode="none"
                  placeholder="点击右侧数字键盘输入"
                  :class="{ active: activeTarget === 'used' }"
                  @click="setActiveTarget('used')"
                />
              </label>

              <label class="touch-field produced-field">
                <span>成品数量（kg）</span>
                <input
                  id="materialInputProduct"
                  v-model="producedValue"
                  readonly
                  inputmode="none"
                  placeholder="点击右侧数字键盘输入"
                  :class="{ active: activeTarget === 'produced' }"
                  @click="setActiveTarget('produced')"
                />
              </label>
            </div>

            <div class="remark-area">
              <label for="materialInputRemark">备注名称</label>
              <input
                id="materialInputRemark"
                v-model="remarkValue"
                placeholder="可以点击下方标签，也可以手动输入"
              />
              <div class="remark-tags">
                <button
                  v-for="tag in remarkTags"
                  :key="tag"
                  type="button"
                  :class="{ selected: remarkValue === tag }"
                  @click="remarkValue = tag"
                >
                  {{ tag }}
                </button>
                <span v-if="remarkTags.length === 0">暂无常用标签</span>
              </div>
            </div>
          </div>

          <div class="upload-keyboard-area">
            <div class="active-hint">
              正在输入：
              <strong>{{ activeTarget === 'used' ? '原材料出库数量' : '成品数量' }}</strong>
            </div>
            <div class="touch-keyboard-panel">
              <button v-for="n in 9" :key="n" type="button" @click="pressKey(String(n))">{{ n }}</button>
              <button type="button" @click="pressKey('.')">.</button>
              <button type="button" @click="pressKey('0')">0</button>
              <button type="button" class="key-backspace" @click="pressKey('backspace')">⌫</button>
              <button type="button" class="key-clear" @click="pressKey('clear')">清空重输</button>
            </div>

            <div v-if="submitError" class="submit-error">{{ submitError }}</div>

            <footer class="material-modal-footer">
              <button type="button" class="button-secondary" @click="handleClose">取消</button>
              <button
                type="button"
                class="button-primary"
                :disabled="loading || !settings.configured"
                @click="handleSubmit"
              >
                {{ loading ? '正在提交...' : '提交待审核草稿' }}
              </button>
            </footer>
          </div>
        </div>
      </section>
    </div>

    <div v-if="showSuccess" class="material-modal-mask success-layer">
      <section class="success-modal" role="dialog" aria-modal="true">
        <div class="success-icon">✓</div>
        <h3>原材料出库草稿已提交</h3>
        <p>{{ successMessage }}</p>
        <button type="button" @click="showSuccess = false">我知道了</button>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import request from '@/api/request'

const visible = ref(false)
const loading = ref(false)
const configLoading = ref(false)
const configError = ref('')
const submitError = ref('')
const showSuccess = ref(false)
const successMessage = ref('')

const usedValue = ref('')
const producedValue = ref('')
const remarkValue = ref('')
const activeTarget = ref('used')
const settings = ref({
  configured: false,
  defaultStoreId: null,
  defaultWarehouseId: null,
  defaultProductId: null,
  showCurrentStock: true,
  stores: [],
  warehouses: [],
  products: [],
  allowedProducts: [],
  remarkTags: []
})

const currentProduct = computed(() => (
  settings.value.defaultProduct
  || settings.value.products.find(item => String(item.id) === String(settings.value.defaultProductId))
  || null
))
const currentStore = computed(() => (
  settings.value.stores.find(item => String(item.id) === String(settings.value.defaultStoreId)) || null
))
const currentWarehouse = computed(() => (
  settings.value.warehouses.find(item => String(item.id) === String(settings.value.defaultWarehouseId)) || null
))
const remarkTags = computed(() => settings.value.remarkTags || [])

const formatNumber = value => Number(value || 0).toLocaleString('zh-CN', {
  maximumFractionDigits: 3
})

const setActiveTarget = target => {
  activeTarget.value = target
}

const pressKey = key => {
  const targetRef = activeTarget.value === 'used' ? usedValue : producedValue
  const currentValue = targetRef.value

  if (key === 'clear') {
    targetRef.value = ''
  } else if (key === 'backspace') {
    targetRef.value = currentValue.slice(0, -1)
  } else if (key === '.') {
    if (!currentValue.includes('.')) targetRef.value = `${currentValue || '0'}.`
  } else if (currentValue !== '0' || key !== '0') {
    targetRef.value = `${currentValue}${key}`
  }
}

const fetchConfig = async () => {
  configLoading.value = true
  configError.value = ''
  try {
    const response = await request({
      url: '/material-outbound-settings',
      method: 'GET'
    })
    settings.value = response || settings.value
    if (!settings.value.configured) {
      configError.value = '管理员尚未配置默认门店、仓库和原材料，请先在后台“原材料出库”页面完成设置。'
    }
  } catch (error) {
    configError.value = error?.response?.data?.message || '原材料出库配置加载失败，请检查网络连接。'
  } finally {
    configLoading.value = false
  }
}

const open = () => {
  usedValue.value = ''
  producedValue.value = ''
  remarkValue.value = ''
  activeTarget.value = 'used'
  submitError.value = ''
  visible.value = true
  fetchConfig()
}

const handleClose = () => {
  if (loading.value) return
  visible.value = false
}

const handleSubmit = async () => {
  const used = Number(usedValue.value)
  const produced = Number(producedValue.value)
  submitError.value = ''

  if (!settings.value.configured) {
    submitError.value = '管理员尚未完成触屏端出库配置。'
    return
  }
  if (!Number.isFinite(used) || used <= 0) {
    submitError.value = '请输入大于 0 的原材料出库数量。'
    setActiveTarget('used')
    return
  }
  if (producedValue.value === '' || !Number.isFinite(produced) || produced < 0) {
    submitError.value = '请输入有效的成品数量。'
    setActiveTarget('produced')
    return
  }

  loading.value = true
  try {
    const response = await request({
      url: '/material-outbounds',
      method: 'POST',
      data: {
        productId: settings.value.defaultProductId,
        quantity: used,
        producedQuantity: produced,
        remark: remarkValue.value.trim()
      }
    })
    const documentNo = response?.materialOutbound?.documentNo || ''
    successMessage.value = [
      documentNo ? `单号：${documentNo}` : '',
      `原材料：${currentProduct.value?.name || '-'}`,
      `出库数量：${formatNumber(used)} ${currentProduct.value?.unit || ''}`,
      `成品数量：${formatNumber(produced)} kg`,
      '当前状态：待审核（尚未扣减库存）'
    ].filter(Boolean).join('\n')
    showSuccess.value = true
    visible.value = false
    window.dispatchEvent(new CustomEvent('refresh-material-outbounds'))
    window.dispatchEvent(new CustomEvent('refresh-materials'))
  } catch (error) {
    submitError.value = error?.response?.data?.message || '网络通信异常，草稿提交失败。'
  } finally {
    loading.value = false
  }
}

const handleOpenEvent = () => open()

onMounted(() => {
  window.addEventListener('open-upload-material-modal', handleOpenEvent)
})

onBeforeUnmount(() => {
  window.removeEventListener('open-upload-material-modal', handleOpenEvent)
})

defineExpose({ open })
</script>

<style scoped>
.material-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 2147483000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.46);
}

.material-modal {
  width: min(980px, calc(100vw - 48px));
  overflow: hidden;
  color: #172033;
  background: #f4f7f8;
  border: 1px solid #dbe3ea;
  border-radius: 10px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
}

.material-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 82px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #dfe5ec;
}

.material-modal-header span {
  color: #0f9f78;
  font-size: 12px;
  font-weight: 700;
}

.material-modal-header h2 {
  margin: 3px 0 2px;
  font-size: 20px;
}

.material-modal-header p {
  margin: 0;
  color: #7b8799;
  font-size: 13px;
}

.material-modal-header > button {
  width: 38px;
  height: 38px;
  padding: 0;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 27px;
  line-height: 1;
}

.material-modal-body {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(330px, 0.8fr);
  gap: 18px;
  padding: 18px;
}

.upload-inputs-area,
.upload-keyboard-area {
  min-width: 0;
  padding: 18px;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 8px;
}

.material-summary {
  overflow: hidden;
  border: 1px solid #dce7e3;
  border-radius: 7px;
}

.summary-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 15px;
  background: #f0faf6;
  border-bottom: 1px solid #dce7e3;
}

.summary-heading span,
.summary-grid span {
  color: #7a8698;
  font-size: 12px;
}

.summary-heading strong {
  color: #08745a;
  font-size: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-grid > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
  padding: 12px 15px;
  border-right: 1px solid #edf1f3;
  border-bottom: 1px solid #edf1f3;
}

.summary-grid > div:nth-child(2n) {
  border-right: 0;
}

.summary-grid strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.stock-line {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 15px;
  color: #64748b;
  font-size: 13px;
}

.stock-line strong {
  color: #0f766e;
}

.number-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px;
  margin-top: 16px;
}

.touch-field,
.remark-area {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 8px;
}

.touch-field > span,
.remark-area > label {
  color: #475569;
  font-size: 13px;
  font-weight: 700;
}

.touch-field input,
.remark-area > input {
  width: 100%;
  height: 48px;
  padding: 0 13px;
  color: #172033;
  background: #f8fafc;
  border: 2px solid #d7e0e8;
  border-radius: 7px;
  box-sizing: border-box;
  outline: none;
  font-size: 20px;
  font-weight: 750;
}

.touch-field input.active {
  border-color: #0f9f78;
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.12);
}

.produced-field input.active {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.remark-area {
  margin-top: 16px;
  padding-top: 15px;
  border-top: 1px dashed #dfe5ec;
}

.remark-area > input {
  height: 40px;
  background: #fff;
  border-width: 1px;
  font-size: 14px;
  font-weight: 500;
}

.remark-tags {
  display: flex;
  min-height: 28px;
  flex-wrap: wrap;
  gap: 8px;
}

.remark-tags button {
  min-height: 32px;
  padding: 0 12px;
  color: #08745a;
  background: #e9f8f3;
  border: 1px solid #bce8d9;
  border-radius: 999px;
  cursor: pointer;
  font-size: 13px;
}

.remark-tags button.selected {
  color: #fff;
  background: #0f9f78;
  border-color: #0f9f78;
}

.remark-tags > span {
  color: #94a3b8;
  font-size: 12px;
}

.upload-keyboard-area {
  display: flex;
  flex-direction: column;
}

.active-hint {
  margin-bottom: 12px;
  color: #64748b;
  font-size: 13px;
}

.active-hint strong {
  color: #172033;
}

.touch-keyboard-panel {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.touch-keyboard-panel button {
  height: 54px;
  color: #263348;
  background: #f8fafc;
  border: 1px solid #d7e0e8;
  border-radius: 7px;
  cursor: pointer;
  font-size: 21px;
  font-weight: 700;
}

.touch-keyboard-panel button:active {
  color: #08745a;
  background: #e9f8f3;
  border-color: #0f9f78;
  transform: scale(0.97);
}

.touch-keyboard-panel .key-backspace {
  color: #dc2626;
}

.touch-keyboard-panel .key-clear {
  grid-column: 1 / -1;
  height: 44px;
  color: #64748b;
  font-size: 14px;
}

.material-modal-footer {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 10px;
  margin-top: auto;
  padding-top: 18px;
}

.material-modal-footer button,
.success-modal button,
.modal-state button {
  height: 44px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

.button-secondary {
  color: #475569;
  background: #fff;
  border: 1px solid #cbd5e1;
}

.button-primary,
.success-modal button {
  color: #fff;
  background: #0f9f78;
  border: 1px solid #0f9f78;
}

.button-primary:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.submit-error {
  margin-top: 12px;
  padding: 9px 11px;
  color: #b42318;
  background: #fff1f0;
  border: 1px solid #fecaca;
  border-radius: 6px;
  font-size: 12px;
}

.modal-state {
  display: flex;
  min-height: 320px;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.error-state {
  flex-direction: column;
  gap: 10px;
  text-align: center;
}

.error-state strong {
  color: #b42318;
  font-size: 18px;
}

.error-state button {
  margin-top: 6px;
  padding: 0 18px;
  color: #fff;
  background: #0f9f78;
  border: 0;
}

.success-layer {
  z-index: 2147483100;
}

.success-modal {
  width: min(380px, calc(100vw - 40px));
  padding: 30px;
  text-align: center;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.25);
}

.success-icon {
  display: inline-flex;
  width: 52px;
  height: 52px;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #0f9f78;
  border-radius: 50%;
  font-size: 28px;
  font-weight: 800;
}

.success-modal h3 {
  margin: 16px 0 8px;
  color: #172033;
}

.success-modal p {
  margin: 0;
  color: #64748b;
  line-height: 1.8;
  white-space: pre-line;
}

.success-modal button {
  width: 100%;
  margin-top: 20px;
}

@media (max-width: 780px) {
  .material-modal-mask {
    padding: 10px;
  }

  .material-modal {
    width: calc(100vw - 20px);
    max-height: calc(100vh - 20px);
    overflow-y: auto;
  }

  .material-modal-body {
    grid-template-columns: 1fr;
  }
}
</style>
