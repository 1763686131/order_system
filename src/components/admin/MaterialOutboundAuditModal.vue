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
        <form class="material-audit-form" @submit.prevent="submitAudit">
          <div class="top-info-bar">
            <div class="document-title">
              <span class="document-eyebrow">原材料出库</span>
              <h2 id="materialAuditTitle">审核</h2>
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
                <input :value="record?.documentDate || '-'" type="text" readonly />
              </label>
              <label class="info-group document-no-field">
                <span>单据编号</span>
                <input :value="record?.documentNo || '-'" type="text" readonly />
              </label>
            </div>

            <div class="toolbar-actions">
              <span class="audit-status">待审核</span>
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
            <span v-if="optionsLoading">正在加载仓库和成品资料...</span>
            <template v-else-if="optionsError">
              <span>{{ optionsError }}</span>
              <button type="button" class="inline-button" @click="loadOptions">重新加载</button>
            </template>
          </div>

          <div v-if="!optionsLoading && !optionsError" class="products-table-wrapper">
            <table class="products-table">
              <colgroup>
                <col style="width: 48px" />
                <col style="width: 190px" />
                <col style="width: 130px" />
                <col style="width: 70px" />
                <col style="width: 140px" />
                <col style="width: 105px" />
                <col style="width: 170px" />
                <col style="width: 220px" />
                <col style="width: 110px" />
                <col style="width: 75px" />
                <col style="width: 220px" />
              </colgroup>
              <thead>
                <tr>
                  <th>序号</th>
                  <th>原材料</th>
                  <th>规格型号</th>
                  <th>单位</th>
                  <th>出库仓库</th>
                  <th>出库数量</th>
                  <th>成品入库仓库</th>
                  <th>成品商品</th>
                  <th>入库数量</th>
                  <th>单位</th>
                  <th>备注信息</th>
                </tr>
              </thead>
              <tbody>
                <tr class="data-row">
                  <td class="center">1</td>
                  <td>
                    <input
                      :value="record?.primaryItem?.productName || '-'"
                      type="text"
                      readonly
                      aria-label="原材料"
                    />
                    <small class="cell-subtext">{{ record?.primaryItem?.productCode || '无编码' }}</small>
                  </td>
                  <td>
                    <input
                      :value="record?.primaryItem?.specification || '-'"
                      type="text"
                      readonly
                      aria-label="规格型号"
                    />
                  </td>
                  <td>
                    <input
                      :value="record?.primaryItem?.unit || '-'"
                      type="text"
                      readonly
                      aria-label="原材料单位"
                    />
                  </td>
                  <td>
                    <input
                      :value="record?.warehouseName || '-'"
                      type="text"
                      readonly
                      aria-label="出库仓库"
                    />
                  </td>
                  <td class="right">
                    <input
                      :value="formatNumber(record?.totalQuantity)"
                      type="text"
                      readonly
                      aria-label="出库数量"
                    />
                  </td>
                  <td>
                    <select
                      v-model="form.finishedWarehouseId"
                      class="table-input"
                      :class="{ invalid: errors.finishedWarehouseId }"
                      :disabled="saving || optionsLoading"
                      aria-label="成品入库仓库"
                      @change="handleWarehouseChange"
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
                    <small v-if="errors.finishedWarehouseId" class="cell-error">
                      {{ errors.finishedWarehouseId }}
                    </small>
                  </td>
                  <td>
                    <select
                      v-model="form.finishedProductId"
                      class="table-input"
                      :class="{ invalid: errors.finishedProductId }"
                      :disabled="saving || !form.finishedWarehouseId"
                      aria-label="成品商品"
                    >
                      <option value="">
                        {{ form.finishedWarehouseId ? '请选择成品商品' : '请先选择仓库' }}
                      </option>
                      <option
                        v-for="product in availableProducts"
                        :key="product.id"
                        :value="String(product.id)"
                      >
                        {{ product.code ? `${product.code} · ` : '' }}{{ product.name }}
                      </option>
                    </select>
                    <small v-if="selectedProduct" class="cell-subtext">
                      {{ selectedProduct.specification || '无规格' }}
                    </small>
                    <small v-if="errors.finishedProductId" class="cell-error">
                      {{ errors.finishedProductId }}
                    </small>
                  </td>
                  <td>
                    <input
                      v-model="form.finishedQuantity"
                      class="table-input number-input"
                      :class="{ invalid: errors.finishedQuantity }"
                      :disabled="saving"
                      type="number"
                      min="0"
                      step="0.0001"
                      placeholder="入库数量"
                      aria-label="入库数量"
                    />
                    <small v-if="errors.finishedQuantity" class="cell-error">
                      {{ errors.finishedQuantity }}
                    </small>
                  </td>
                  <td class="center readonly-unit">
                    {{ productUnit(selectedProduct) || '待定' }}
                  </td>
                  <td>
                    <input
                      v-model.trim="form.finishedRemark"
                      class="table-input"
                      :disabled="saving"
                      type="text"
                      maxlength="200"
                      placeholder="默认继承触屏备注"
                      aria-label="成品入库备注"
                    />
                  </td>
                </tr>
                <tr v-for="index in 7" :key="`blank-row-${index}`" class="blank-row">
                  <td class="center">{{ index + 1 }}</td>
                  <td colspan="10"></td>
                </tr>
                <tr class="total-row">
                  <td colspan="5" class="center">合计</td>
                  <td class="right">{{ formatNumber(record?.totalQuantity) }}</td>
                  <td colspan="2"></td>
                  <td class="right">{{ formatNumber(form.finishedQuantity || 0) }}</td>
                  <td class="center">{{ productUnit(selectedProduct) || '-' }}</td>
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
                <input :value="record?.remark || '-'" type="text" readonly />
              </label>
              <label class="info-group">
                <span>审核人</span>
                <input value="当前审核员" type="text" readonly />
              </label>
              <label class="info-group">
                <span>审核状态</span>
                <input value="待审核" type="text" readonly />
              </label>
            </div>
            <div class="finance-row">
              <span>原材料出库 <strong>{{ formatNumber(record?.totalQuantity) }} {{ record?.primaryItem?.unit || '' }}</strong></span>
              <span>成品入库 <strong>{{ formatNumber(form.finishedQuantity || 0) }} {{ productUnit(selectedProduct) || '-' }}</strong></span>
              <span>审核结果 <strong>审核后同步完成出库和入库</strong></span>
              <button
                type="submit"
                class="audit-button primary bottom-audit-button"
                :disabled="saving || optionsLoading || Boolean(optionsError)"
              >
                {{ saving ? '审核中...' : '审核并入库' }}
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

const emit = defineEmits(['close', 'audited'])

const warehouses = ref([])
const products = ref([])
const units = ref([])
const optionsLoading = ref(false)
const optionsError = ref('')
const saving = ref(false)
const formError = ref('')
const initializedRecordId = ref(null)
const form = reactive({
  finishedWarehouseId: '',
  finishedProductId: '',
  finishedQuantity: '',
  finishedRemark: ''
})
const errors = reactive({
  finishedWarehouseId: '',
  finishedProductId: '',
  finishedQuantity: ''
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
  if (!form.finishedWarehouseId) return []
  return products.value.filter(product => {
    if (product.enabled === false) return false
    const storeIds = parseIds(product.storeIds ?? product.store_ids)
    if (storeIds.length && props.record?.storeId) {
      if (!storeIds.some(id => String(id) === String(props.record.storeId))) return false
    }
    const productWarehouseId = product.warehouseId ?? product.warehouse_id
    return !productWarehouseId || String(productWarehouseId) === String(form.finishedWarehouseId)
  })
})

const selectedProduct = computed(() => availableProducts.value.find(
  product => String(product.id) === String(form.finishedProductId)
) || products.value.find(product => String(product.id) === String(form.finishedProductId)) || null)

const productUnit = product => {
  if (!product) return ''
  return product.unit
    || product.unitName
    || units.value.find(unit => String(unit.id) === String(product.unitId ?? product.unit_id))?.name
    || ''
}

const clearErrors = () => {
  errors.finishedWarehouseId = ''
  errors.finishedProductId = ''
  errors.finishedQuantity = ''
  formError.value = ''
}

const preferredWarehouseId = () => {
  const existing = props.record?.finishedWarehouseId
  if (existing && availableWarehouses.value.some(item => String(item.id) === String(existing))) {
    return String(existing)
  }
  const named = availableWarehouses.value.find(item => /成品|完工|商品|finished/i.test(item.name || ''))
  if (named) return String(named.id)
  return availableWarehouses.value.length === 1 ? String(availableWarehouses.value[0].id) : ''
}

const resetForm = () => {
  clearErrors()
  form.finishedWarehouseId = ''
  form.finishedProductId = props.record?.finishedProductId
    ? String(props.record.finishedProductId)
    : ''
  form.finishedQuantity = Number(props.record?.producedQuantity || 0) > 0
    ? String(props.record.producedQuantity)
    : ''
  form.finishedRemark = props.record?.finishedRemark || props.record?.remark || ''
}

const loadOptions = async () => {
  optionsLoading.value = true
  optionsError.value = ''
  try {
    const results = await Promise.all([
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: '/products', method: 'GET' }),
      request({ url: '/products/units/measurements', method: 'GET' })
    ])
    warehouses.value = Array.isArray(results[0]) ? results[0] : []
    products.value = Array.isArray(results[1]) ? results[1] : []
    units.value = Array.isArray(results[2]) ? results[2] : []
    if (!form.finishedWarehouseId) form.finishedWarehouseId = preferredWarehouseId()
    if (
      form.finishedProductId
      && !availableProducts.value.some(item => String(item.id) === String(form.finishedProductId))
    ) {
      form.finishedProductId = ''
    }
  } catch (error) {
    optionsError.value = error?.response?.data?.message || '成品资料加载失败。'
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
  if (!warehouses.value.length || !products.value.length) await loadOptions()
}

const handleWarehouseChange = () => {
  errors.finishedWarehouseId = ''
  if (
    form.finishedProductId
    && !availableProducts.value.some(item => String(item.id) === String(form.finishedProductId))
  ) {
    form.finishedProductId = ''
  }
}

const validate = () => {
  clearErrors()
  let valid = true
  if (!form.finishedWarehouseId) {
    errors.finishedWarehouseId = '请选择成品入库仓库。'
    valid = false
  }
  if (!form.finishedProductId) {
    errors.finishedProductId = '请选择成品商品。'
    valid = false
  }
  const quantity = Number(form.finishedQuantity)
  if (!Number.isFinite(quantity) || quantity <= 0) {
    errors.finishedQuantity = '入库数量必须大于 0。'
    valid = false
  }
  return valid
}

const requestClose = () => {
  if (!saving.value) emit('close')
}

const submitAudit = async () => {
  if (saving.value || !props.record || !validate()) return
  saving.value = true
  try {
    const response = await request({
      url: `/material-outbounds/${props.record.id}/audit`,
      method: 'POST',
      data: {
        finishedWarehouseId: Number(form.finishedWarehouseId),
        finishedProductId: Number(form.finishedProductId),
        finishedQuantity: Number(form.finishedQuantity),
        finishedRemark: form.finishedRemark
      }
    })
    emit('audited', response)
  } catch (error) {
    formError.value = error?.response?.data?.message || '审核失败，请检查表单和库存后重试。'
  } finally {
    saving.value = false
  }
}

watch(
  () => props.visible,
  visible => {
    if (visible) initialize()
    else initializedRecordId.value = null
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

.audit-button {
  min-height: 38px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.audit-button:disabled,
.close-button:disabled,
button:disabled {
  cursor: default;
  opacity: 0.55;
}

.audit-button.primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.audit-button.primary:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.audit-button.secondary {
  color: #52616c;
  background: #fff;
  border-color: var(--border-strong);
}

.audit-button.secondary:hover:not(:disabled) {
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
  min-width: 1260px;
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
.info-group select.invalid {
  border-color: #d64550;
  background: #fff6f6;
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

.finance-row .audit-button {
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

  .header-audit-button {
    flex: 1;
  }

  .finance-row {
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
  }

  .finance-row > span {
    white-space: normal;
  }

  .finance-row .audit-button {
    width: 100%;
    margin-left: 0;
  }
}
</style>
