<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="material-audit-overlay"
      role="presentation"
      @click.self="requestClose"
    >
      <section
        class="material-audit-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="materialAuditTitle"
        @click.stop
      >
        <form class="material-audit-form" @submit.prevent="submitChanges">
          <div class="top-info-bar">
            <div class="document-title">
              <span class="document-eyebrow">原材料出库</span>
              <h2 id="materialAuditTitle">修改</h2>
            </div>

            <div class="header-fields">
              <label class="info-group">
                <span>门店</span>
                <input :value="record?.storeName || '-'" type="text" readonly />
              </label>
              <label class="info-group">
                <span>出库仓库</span>
                <input :value="record?.warehouseName || '-'" type="text" readonly />
              </label>
              <label class="info-group material-source-field">
                <span>触屏原材料</span>
                <input :value="record?.primaryItem?.productName || '-'" type="text" readonly />
              </label>
              <label class="info-group quantity-source-field">
                <span>出库数量</span>
                <input
                  :value="`${formatNumber(record?.totalQuantity)} ${record?.primaryItem?.unit || ''}`"
                  type="text"
                  readonly
                />
              </label>
              <label class="info-group date-field">
                <span>单据日期</span>
                <input
                  v-model="form.documentDate"
                  :class="{ invalid: errors.documentDate }"
                  :disabled="!editing || saving"
                  type="date"
                  aria-label="单据日期"
                />
                <small v-if="errors.documentDate" class="top-error">{{ errors.documentDate }}</small>
              </label>
              <label class="info-group document-no-field">
                <span>单据编号</span>
                <input :value="record?.documentNo || '-'" type="text" readonly />
              </label>
            </div>

            <div class="toolbar-actions">
              <span class="audit-status">草稿</span>
              <button
                type="button"
                class="close-button"
                aria-label="关闭"
                title="关闭"
                :disabled="saving"
                @click="requestClose"
              >
                ×
              </button>
            </div>
          </div>

          <div class="contact-info-bar">
            <label class="info-group touch-remark-field">
              <span>触屏备注</span>
              <input :value="record?.remark || '-'" type="text" readonly />
            </label>
            <label class="info-group">
              <span>单据来源</span>
              <input :value="record?.source === 'touch' ? '触屏端辅助输入' : (record?.source || '-')" type="text" readonly />
            </label>
          </div>

          <div class="table-state" :class="{ error: optionsError }">
            <span v-if="optionsLoading">正在加载仓库和原材料资料...</span>
            <template v-else-if="optionsError">
              <span>{{ optionsError }}</span>
              <button type="button" class="inline-button" @click="loadOptions">重新加载</button>
            </template>
          </div>

          <div v-if="!optionsLoading && !optionsError" class="products-table-wrapper">
            <table class="products-table">
              <colgroup>
                <col style="width: 48px" />
                <col style="width: 240px" />
                <col style="width: 130px" />
                <col style="width: 70px" />
                <col style="width: 180px" />
                <col style="width: 115px" />
                <col style="width: 280px" />
              </colgroup>
              <thead>
                <tr>
                  <th>序号</th>
                  <th>原材料</th>
                  <th>规格型号</th>
                  <th>单位</th>
                  <th>出库仓库</th>
                  <th>出库数量</th>
                  <th>备注信息</th>
                </tr>
              </thead>
              <tbody>
                <tr class="data-row">
                  <td class="center">1</td>
                  <td>
                    <select
                      v-model="form.productId"
                      class="table-input"
                      :class="{ invalid: errors.productId }"
                      :disabled="!editing || saving || optionsLoading"
                      aria-label="原材料"
                      @change="syncProduct"
                    >
                      <option value="">请选择原材料</option>
                      <option
                        v-for="product in availableProducts"
                        :key="product.id"
                        :value="String(product.id)"
                      >
                        {{ product.code ? `${product.code} · ` : '' }}{{ product.name }}
                      </option>
                    </select>
                    <small class="cell-subtext">{{ form.productCode || '无编码' }}</small>
                    <small v-if="errors.productId" class="cell-error">{{ errors.productId }}</small>
                  </td>
                  <td>
                    <input
                      :value="form.specification || '-'"
                      type="text"
                      readonly
                      aria-label="规格型号"
                    />
                  </td>
                  <td>
                    <input
                      :value="form.unit || '-'"
                      type="text"
                      readonly
                      aria-label="原材料单位"
                    />
                  </td>
                  <td>
                    <select
                      v-model="form.warehouseId"
                      class="table-input"
                      :class="{ invalid: errors.warehouseId }"
                      :disabled="!editing || saving || optionsLoading"
                      aria-label="出库仓库"
                      @change="syncWarehouse"
                    >
                      <option value="">请选择仓库</option>
                      <option
                        v-for="warehouse in availableWarehouses"
                        :key="warehouse.id"
                        :value="String(warehouse.id)"
                      >
                        {{ warehouse.name }}
                      </option>
                    </select>
                    <small v-if="errors.warehouseId" class="cell-error">{{ errors.warehouseId }}</small>
                  </td>
                  <td class="right">
                    <input
                      v-model="form.quantity"
                      class="table-input number-input"
                      :class="{ invalid: errors.quantity }"
                      :readonly="!editing || saving"
                      type="number"
                      min="0"
                      step="0.0001"
                      placeholder="出库数量"
                      aria-label="出库数量"
                    />
                    <small v-if="errors.quantity" class="cell-error">{{ errors.quantity }}</small>
                  </td>
                  <td>
                    <input
                      v-model.trim="form.remark"
                      class="table-input"
                      :readonly="!editing || saving"
                      type="text"
                      maxlength="200"
                      placeholder="默认继承触屏备注"
                      aria-label="备注信息"
                    />
                  </td>
                </tr>
                <tr v-for="index in 7" :key="`blank-row-${index}`" class="blank-row">
                  <td class="center">{{ index + 1 }}</td>
                  <td colspan="6"></td>
                </tr>
                <tr class="total-row">
                  <td colspan="5" class="center">合计</td>
                  <td class="right">{{ formatNumber(form.quantity || 0) }}</td>
                  <td></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="formError" class="form-error" role="alert">{{ formError }}</div>

          <div class="bottom-info-bar">
            <div class="finance-row-full">
              <label class="info-group">
                <span>制单人</span>
                <input :value="record?.createdBy || '-'" type="text" readonly />
              </label>
              <label class="info-group">
                <span>制单时间</span>
                <input :value="record?.createdAt || '-'" type="text" readonly />
              </label>
              <label class="info-group wide remark-field">
                <span>备注信息</span>
                <input :value="form.remark || '-'" type="text" readonly />
              </label>
              <label class="info-group">
                <span>修改人</span>
                <input value="当前操作员" type="text" readonly />
              </label>
              <label class="info-group">
                <span>单据状态</span>
                <input value="草稿，待审核" type="text" readonly />
              </label>
            </div>
            <div class="finance-row">
              <span>原材料出库 <strong>{{ formatNumber(form.quantity || 0) }} {{ form.unit || '' }}</strong></span>
              <span>单据状态 <strong>草稿</strong></span>
              <span>修改结果 <strong>{{ editing ? '保存后仍为草稿，待详情弹窗审核' : '点击修改后编辑表单' }}</strong></span>
              <button
                v-if="editing"
                type="button"
                class="edit-button secondary"
                :disabled="saving"
                @click="cancelEditing"
              >
                取消修改
              </button>
              <button
                type="submit"
                class="edit-button primary bottom-edit-button"
                :disabled="saving || optionsLoading || Boolean(optionsError)"
              >
                {{ saving ? '保存中...' : (editing ? '保存修改' : '修改') }}
              </button>
            </div>
          </div>
        </form>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import request from '@/api/request'

const props = defineProps({
  visible: { type: Boolean, default: false },
  record: { type: Object, default: null }
})

const emit = defineEmits(['close', 'updated'])

const warehouses = ref([])
const products = ref([])
const units = ref([])
const allowedProductIds = ref([])
const optionsLoading = ref(false)
const optionsError = ref('')
const optionsLoaded = ref(false)
const saving = ref(false)
const editing = ref(false)
const formError = ref('')
const initializedRecordId = ref(null)
const form = reactive({
  documentDate: '',
  productId: '',
  productName: '',
  productCode: '',
  specification: '',
  unit: '',
  warehouseId: '',
  warehouseName: '',
  quantity: '',
  remark: ''
})
const errors = reactive({
  documentDate: '',
  productId: '',
  warehouseId: '',
  quantity: ''
})

const formatNumber = value => Number(value || 0).toLocaleString('zh-CN', {
  maximumFractionDigits: 3
})

const parseIds = value => {
  if (Array.isArray(value)) return value
  if (!value) return []
  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return String(value).split(',').map(item => item.trim()).filter(Boolean)
  }
}

const activeWarehouses = computed(() => warehouses.value.filter(item => item.status !== 'inactive'))

const availableWarehouses = computed(() => {
  const scoped = activeWarehouses.value.filter(item => (
    !props.record?.storeId
    || !item.storeId
    || String(item.storeId) === String(props.record.storeId)
  ))
  return scoped.length ? scoped : activeWarehouses.value
})

const availableProducts = computed(() => {
  return products.value.filter(product => {
    if (product.enabled === false) return false
    if (
      allowedProductIds.value.length
      && !allowedProductIds.value.some(id => String(id) === String(product.id))
      && String(product.id) !== String(form.productId)
    ) {
      return false
    }
    const storeIds = parseIds(product.storeIds ?? product.store_ids)
    if (storeIds.length && props.record?.storeId) {
      if (!storeIds.some(id => String(id) === String(props.record.storeId))) return false
    }
    return true
  })
})

const selectedProduct = computed(() => (
  availableProducts.value.find(product => String(product.id) === String(form.productId))
  || products.value.find(product => String(product.id) === String(form.productId))
  || null
))

const productUnit = product => {
  if (!product) return ''
  return product.unit
    || product.unitName
    || units.value.find(unit => String(unit.id) === String(product.unitId ?? product.unit_id))?.name
    || ''
}

const clearErrors = () => {
  errors.documentDate = ''
  errors.productId = ''
  errors.warehouseId = ''
  errors.quantity = ''
  formError.value = ''
}

const resetForm = () => {
  clearErrors()
  editing.value = false
  form.documentDate = props.record?.documentDate || ''
  form.productId = props.record?.primaryItem?.productId
    ? String(props.record.primaryItem.productId)
    : ''
  form.productName = props.record?.primaryItem?.productName || ''
  form.productCode = props.record?.primaryItem?.productCode || ''
  form.specification = props.record?.primaryItem?.specification || ''
  form.unit = props.record?.primaryItem?.unit || ''
  form.warehouseId = props.record?.warehouseId ? String(props.record.warehouseId) : ''
  form.warehouseName = props.record?.warehouseName || ''
  form.quantity = props.record?.totalQuantity != null
    ? String(props.record.totalQuantity)
    : ''
  form.remark = props.record?.remark || ''
}

const loadOptions = async () => {
  optionsLoading.value = true
  optionsError.value = ''
  optionsLoaded.value = false
  try {
    const results = await Promise.all([
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: '/material-outbound-settings', method: 'GET' }),
      request({ url: '/products/units/measurements', method: 'GET' })
    ])
    warehouses.value = Array.isArray(results[0]) ? results[0] : []
    const settings = results[1] || {}
    allowedProductIds.value = parseIds(settings.allowedProductIds)
    products.value = Array.isArray(settings.products)
      ? settings.products
      : (Array.isArray(settings.allowedProducts) ? settings.allowedProducts : [])
    units.value = Array.isArray(results[2]) ? results[2] : []
    const currentProduct = props.record?.primaryItem
    if (
      currentProduct?.productId
      && !products.value.some(item => String(item.id) === String(currentProduct.productId))
    ) {
      products.value.push({
        id: currentProduct.productId,
        code: currentProduct.productCode || '',
        name: currentProduct.productName || '',
        specification: currentProduct.specification || '',
        unit: currentProduct.unit || '',
        enabled: true
      })
    }
    optionsLoaded.value = true
  } catch (error) {
    optionsError.value = error?.response?.data?.message || '仓库和原材料资料加载失败。'
  } finally {
    optionsLoading.value = false
  }
}

const initialize = async () => {
  if (!props.record) return
  if (initializedRecordId.value !== props.record.id) {
    initializedRecordId.value = props.record.id
    resetForm()
  }
  if (!optionsLoaded.value) await loadOptions()
}

const syncProduct = () => {
  const product = selectedProduct.value
  errors.productId = ''
  if (!product) return
  form.productName = product.name || ''
  form.productCode = product.code || ''
  form.specification = product.specification || ''
  form.unit = productUnit(product)
}

const syncWarehouse = () => {
  errors.warehouseId = ''
  const warehouse = availableWarehouses.value.find(
    item => String(item.id) === String(form.warehouseId)
  )
  form.warehouseName = warehouse?.name || ''
}

const cancelEditing = () => {
  if (saving.value) return
  resetForm()
}

const startEditing = () => {
  clearErrors()
  editing.value = true
}

const validate = () => {
  clearErrors()
  let valid = true
  if (!form.documentDate) {
    errors.documentDate = '请选择单据日期。'
    valid = false
  } else if (!/^\d{4}-\d{2}-\d{2}$/.test(form.documentDate)) {
    errors.documentDate = '单据日期格式无效。'
    valid = false
  }
  if (!form.productId) {
    errors.productId = '请选择原材料。'
    valid = false
  }
  if (!form.warehouseId) {
    errors.warehouseId = '请选择出库仓库。'
    valid = false
  }
  const quantity = Number(form.quantity)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    errors.quantity = '出库数量必须大于 0。'
    valid = false
  }
  return valid
}

const requestClose = () => {
  if (!saving.value) emit('close')
}

const submitChanges = async () => {
  if (saving.value || !props.record) return
  if (!editing.value) {
    startEditing()
    return
  }
  if (!validate()) return
  saving.value = true
  try {
    const response = await request({
      url: `/material-outbounds/${props.record.id}`,
      method: 'PUT',
      data: {
        documentDate: form.documentDate,
        storeId: props.record.storeId,
        warehouseId: Number(form.warehouseId),
        productId: Number(form.productId),
        quantity: Number(form.quantity),
        remark: form.remark
      }
    })
    emit('updated', response)
  } catch (error) {
    formError.value = error?.response?.data?.message || '保存修改失败，请检查表单后重试。'
  } finally {
    saving.value = false
  }
}

watch(
  () => props.visible,
  visible => {
    if (visible) initialize()
    else {
      initializedRecordId.value = null
      editing.value = false
    }
  }
)

watch(
  () => props.record?.id,
  () => {
    if (props.visible) initialize()
  }
)
</script>

<style scoped>
.material-audit-overlay {
  --accent: #159a7c;
  --accent-dark: #08755e;
  --border: #e3e8ec;
  --border-strong: #d4dde3;
  --muted: #6c7a85;
  --text: #17212b;
  position: fixed;
  inset: 0;
  z-index: 2147483100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  color: var(--text);
  background: rgba(15, 23, 42, 0.52);
  font-size: 13px;
}

.material-audit-modal,
.material-audit-modal * {
  box-sizing: border-box;
  letter-spacing: 0;
}

.material-audit-modal {
  display: flex;
  width: min(1660px, calc(100vw - 24px));
  max-height: calc(100vh - 24px);
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  box-shadow: 0 18px 54px rgba(23, 33, 43, 0.24);
}

.material-audit-form {
  display: flex;
  min-height: 0;
  flex-direction: column;
  overflow: auto;
  background: #fff;
}

.top-info-bar,
.contact-info-bar,
.finance-row-full,
.finance-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
}

.top-info-bar {
  min-height: 62px;
}

.document-title {
  display: flex;
  flex: 0 0 auto;
  align-items: baseline;
  gap: 8px;
  min-width: 126px;
}

.document-eyebrow {
  color: var(--text);
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
}

.document-title h2 {
  margin: 0;
  color: var(--accent-dark);
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.header-fields {
  display: flex;
  flex: 1 1 780px;
  flex-wrap: wrap;
  align-items: center;
  gap: 9px 12px;
  min-width: 0;
}

.info-group {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
}

.info-group > span {
  flex: none;
  color: #46535f;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

input,
select,
button {
  font: inherit;
}

.info-group input,
.info-group select {
  width: 148px;
  min-width: 0;
  height: 36px;
  padding: 0 9px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  outline: none;
}

.info-group input:focus,
.info-group select:focus,
.table-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(21, 154, 124, 0.12);
}

.info-group input[readonly] {
  color: #64717c;
  background: #f8fafb;
}

.material-source-field input {
  width: 166px;
}

.quantity-source-field input {
  width: 104px;
  text-align: right;
}

.date-field input {
  width: 132px;
}

.document-no-field input {
  width: 154px;
}

.contact-info-bar {
  min-height: 58px;
  background: #fbfcfc;
}

.contact-info-bar .info-group input,
.contact-info-bar .info-group select {
  width: 160px;
}

.touch-remark-field {
  flex: 1 1 280px;
}

.touch-remark-field input {
  width: 100%;
}

.document-time-field input {
  width: 190px;
}

.toolbar-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 9px;
  margin-left: auto;
}

.close-button {
  width: 38px;
  height: 38px;
  padding: 0;
  color: #687580;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.close-button:hover {
  background: #f3f8f6;
}

.audit-status {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  padding: 0 9px;
  color: #a15c00;
  background: #fff7e7;
  border: 1px solid #f1d9a7;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.edit-button {
  min-height: 38px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.edit-button:disabled,
.close-button:disabled,
button:disabled {
  cursor: default;
  opacity: 0.55;
}

.edit-button.primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.edit-button.primary:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.edit-button.secondary {
  color: #52616c;
  background: #fff;
  border-color: var(--border-strong);
}

.edit-button.secondary:hover:not(:disabled) {
  background: #f3f8f6;
}

.table-state {
  display: flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}

.table-state:empty {
  display: none;
}

.table-state.error,
.form-error {
  color: #b5363e;
  background: #fff6f6;
}

.table-state.error {
  justify-content: flex-start;
  padding: 8px 14px;
}

.inline-button {
  min-height: 28px;
  padding: 0 9px;
  color: var(--accent-dark);
  background: #fff;
  border: 1px solid #b5e5d8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.products-table-wrapper {
  overflow-x: auto;
}

.products-table {
  width: 100%;
  min-width: 1080px;
  table-layout: fixed;
  border-collapse: collapse;
}

.products-table th,
.products-table td {
  height: 44px;
  padding: 4px 7px;
  overflow: hidden;
  border-right: 1px solid #eef1f3;
  border-bottom: 1px solid #e9eef1;
}

.products-table th {
  color: var(--muted);
  background: #f8fafb;
  font-size: 12px;
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
}

.products-table td {
  color: var(--text);
  background: #fff;
  font-size: 13px;
}

.products-table td:last-child,
.products-table th:last-child {
  border-right: 0;
}

.products-table td input,
.products-table td select {
  width: 100%;
  height: 32px;
  min-width: 0;
  padding: 0 5px;
  color: inherit;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 3px;
  outline: none;
}

.products-table td input[readonly] {
  color: #46535f;
  background: #f8fafb;
}

.products-table .table-input {
  background: #fff;
  border-color: var(--border-strong);
}

.products-table .table-input:disabled {
  color: #87939b;
  background: #f8fafb;
}

.products-table .table-input.invalid,
.info-group select.invalid,
.info-group input.invalid {
  border-color: #d64550;
  background: #fff6f6;
}

.info-group input:disabled {
  color: #64717c;
  background: #f8fafb;
  cursor: default;
}

.products-table td.right,
.products-table td.right input,
.number-input {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.center {
  text-align: center !important;
}

.cell-subtext,
.cell-error {
  display: block;
  overflow: hidden;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-subtext {
  padding: 0 5px;
  color: #7b8892;
  font-size: 11px;
}

.cell-error {
  padding: 0 5px;
  color: #b5363e;
  font-size: 11px;
  white-space: normal;
}

.top-error {
  color: #b5363e;
  font-size: 11px;
  white-space: nowrap;
}

.readonly-unit {
  color: #64717c !important;
  background: #f8fafb !important;
}

.blank-row td {
  height: 43px;
  background: #fff;
}

.total-row td {
  height: 43px;
  color: #17212b;
  background: #f8fafb;
  font-weight: 600;
}

.total-row td.right {
  color: var(--accent-dark);
}

.form-error {
  margin: 0;
  padding: 9px 14px;
  border-bottom: 1px solid #f1cbd0;
  font-size: 12px;
}

.bottom-info-bar {
  border-top: 0;
  background: #fff;
}

.finance-row-full {
  border-bottom: 0;
}

.finance-row-full .info-group input {
  width: 142px;
}

.finance-row-full .info-group.wide {
  flex: 1 1 260px;
}

.finance-row-full .info-group.wide input {
  width: 100%;
}

.finance-row {
  gap: 22px;
  background: #fbfcfc;
}

.finance-row > span {
  color: #46535f;
  white-space: nowrap;
}

.finance-row strong {
  margin-left: 7px;
  color: var(--accent-dark);
  font-variant-numeric: tabular-nums;
}

.finance-row > span:nth-child(3) strong {
  font-weight: 500;
}

.finance-row .edit-button {
  margin-left: auto;
}

@media (max-width: 1180px) {
  .top-info-bar {
    align-items: flex-start;
  }

  .toolbar-actions {
    margin-left: 0;
  }

  .header-fields {
    flex-basis: 100%;
    order: 3;
  }

  .document-title {
    margin-top: 7px;
  }
}

@media (max-width: 720px) {
  .material-audit-overlay {
    padding: 5px;
  }

  .material-audit-modal {
    width: calc(100vw - 10px);
    max-height: calc(100vh - 10px);
  }

  .top-info-bar,
  .contact-info-bar,
  .finance-row-full,
  .finance-row {
    gap: 9px;
    padding: 9px;
  }

  .document-title {
    width: 100%;
    margin-top: 0;
  }

  .header-fields {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .header-fields .info-group,
  .contact-info-bar .info-group,
  .finance-row-full .info-group {
    width: 100%;
  }

  .info-group input,
  .info-group select,
  .material-source-field input,
  .quantity-source-field input,
  .date-field input,
  .document-no-field input,
  .contact-info-bar .info-group input,
  .contact-info-bar .info-group select,
  .finance-row-full .info-group input {
    flex: 1;
    width: 0;
  }

  .toolbar-actions {
    width: 100%;
    margin-left: 0;
  }

  .finance-row {
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
  }

  .finance-row > span {
    white-space: normal;
  }

  .finance-row .edit-button {
    width: 100%;
    margin-left: 0;
  }
}
</style>
