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
        <header class="audit-header">
          <div class="audit-title">
            <span class="audit-eyebrow">原材料出库审核</span>
            <h2 id="materialAuditTitle">{{ record?.documentNo || '审核出库单' }}</h2>
            <p>补齐成品入库信息后，系统会在同一事务中完成出库和入库。</p>
          </div>
          <button
            type="button"
            class="audit-close"
            aria-label="关闭"
            :disabled="saving"
            @click="requestClose"
          >
            ×
          </button>
        </header>

        <div class="audit-body">
          <section class="audit-section source-section">
            <div class="section-heading">
              <span class="section-index">1</span>
              <div>
                <h3>触屏端辅助输入</h3>
                <p>以下数据来自员工触屏端，审核时作为原材料出库依据。</p>
              </div>
            </div>
            <dl class="source-grid">
              <div>
                <dt>门店</dt>
                <dd>{{ record?.storeName || '-' }}</dd>
              </div>
              <div>
                <dt>出库仓库</dt>
                <dd>{{ record?.warehouseName || '-' }}</dd>
              </div>
              <div>
                <dt>原材料</dt>
                <dd>{{ record?.primaryItem?.productName || '-' }}</dd>
              </div>
              <div>
                <dt>出库数量</dt>
                <dd>{{ formatNumber(record?.totalQuantity) }} {{ record?.primaryItem?.unit || '' }}</dd>
              </div>
              <div>
                <dt>录入人</dt>
                <dd>{{ record?.createdBy || '-' }}</dd>
              </div>
              <div>
                <dt>触屏备注</dt>
                <dd>{{ record?.remark || '-' }}</dd>
              </div>
            </dl>
          </section>

          <section class="audit-section">
            <div class="section-heading">
              <span class="section-index">2</span>
              <div>
                <h3>补充成品入库</h3>
                <p>审核员需要确认成品仓库、成品商品和实际入库数量。</p>
              </div>
            </div>

            <div v-if="optionsLoading" class="options-state">正在加载成品和仓库资料...</div>
            <div v-else-if="optionsError" class="options-state error">
              <span>{{ optionsError }}</span>
              <button type="button" class="inline-button" @click="loadOptions">重新加载</button>
            </div>
            <div v-else class="audit-form-grid">
              <label class="audit-field">
                <span>成品入库仓库 <em>*</em></span>
                <select v-model="form.finishedWarehouseId" @change="handleWarehouseChange">
                  <option value="">请选择成品仓库</option>
                  <option
                    v-for="warehouse in availableWarehouses"
                    :key="warehouse.id"
                    :value="String(warehouse.id)"
                  >
                    {{ warehouse.name }}
                  </option>
                </select>
                <small v-if="errors.finishedWarehouseId">{{ errors.finishedWarehouseId }}</small>
              </label>

              <label class="audit-field">
                <span>成品商品 <em>*</em></span>
                <select
                  v-model="form.finishedProductId"
                  :disabled="!form.finishedWarehouseId"
                >
                  <option value="">
                    {{ form.finishedWarehouseId ? '请选择成品商品' : '请先选择成品仓库' }}
                  </option>
                  <option
                    v-for="product in availableProducts"
                    :key="product.id"
                    :value="String(product.id)"
                  >
                    {{ product.code ? `${product.code} · ` : '' }}{{ product.name }}
                  </option>
                </select>
                <small v-if="errors.finishedProductId">{{ errors.finishedProductId }}</small>
              </label>

              <label class="audit-field">
                <span>入库数量 <em>*</em></span>
                <input
                  v-model="form.finishedQuantity"
                  type="number"
                  min="0"
                  step="0.0001"
                  placeholder="请输入实际成品数量"
                />
                <small v-if="errors.finishedQuantity">{{ errors.finishedQuantity }}</small>
              </label>

              <label class="audit-field wide-field">
                <span>入库备注</span>
                <input
                  v-model.trim="form.finishedRemark"
                  type="text"
                  maxlength="200"
                  placeholder="默认使用触屏端备注"
                />
              </label>
            </div>

            <div v-if="selectedProduct" class="selected-product">
              <span>入库商品</span>
              <strong>{{ selectedProduct.name }}</strong>
              <small>
                {{ selectedProduct.specification || '无规格' }}
                · {{ productUnit(selectedProduct) || '未设置单位' }}
              </small>
            </div>

            <div v-if="formError" class="form-error">{{ formError }}</div>
          </section>
        </div>

        <footer class="audit-footer">
          <div class="audit-summary">
            <span>原材料出库 <strong>{{ formatNumber(record?.totalQuantity) }} {{ record?.primaryItem?.unit || '' }}</strong></span>
            <span>成品入库 <strong>{{ formatNumber(form.finishedQuantity || 0) }} {{ productUnit(selectedProduct) || 'kg' }}</strong></span>
          </div>
          <div class="audit-actions">
            <button type="button" class="audit-button secondary" :disabled="saving" @click="requestClose">
              取消
            </button>
            <button
              type="button"
              class="audit-button primary"
              :disabled="saving || optionsLoading || Boolean(optionsError)"
              @click="submitAudit"
            >
              {{ saving ? '正在审核...' : '审核并完成成品入库' }}
            </button>
          </div>
        </footer>
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
  --accent: #0f9f78;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  position: fixed;
  inset: 0;
  z-index: 2147483100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 22px;
  color: #172033;
  background: rgba(15, 23, 42, 0.52);
}

.material-audit-modal {
  display: flex;
  width: min(980px, calc(100vw - 44px));
  max-height: calc(100vh - 44px);
  flex-direction: column;
  overflow: hidden;
  background: #f4f7f8;
  border: 1px solid #dbe3ea;
  border-radius: 8px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.28);
}

.audit-header,
.audit-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 17px 21px;
  background: #fff;
}

.audit-header {
  border-bottom: 1px solid #dfe5ec;
}

.audit-title {
  min-width: 0;
}

.audit-eyebrow {
  color: var(--accent-dark);
  font-size: 11px;
  font-weight: 750;
}

.audit-title h2 {
  margin: 4px 0 3px;
  overflow: hidden;
  font-size: 19px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audit-title p,
.section-heading p {
  margin: 0;
  color: #7a8698;
  font-size: 12px;
}

.audit-close {
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  color: #68758a;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  font-size: 25px;
  line-height: 1;
}

.audit-close:hover {
  background: #f0f3f6;
}

.audit-body {
  min-height: 0;
  overflow-y: auto;
  padding: 16px;
}

.audit-section {
  padding: 15px;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.audit-section + .audit-section {
  margin-top: 13px;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin-bottom: 14px;
}

.section-heading h3 {
  margin: 0 0 4px;
  font-size: 14px;
}

.section-index {
  display: inline-flex;
  width: 23px;
  height: 23px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: var(--accent);
  border-radius: 50%;
  font-size: 11px;
  font-weight: 750;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
  overflow: hidden;
  border: 1px solid #edf1f5;
  border-radius: 5px;
}

.source-grid > div {
  min-width: 0;
  padding: 11px 12px;
  border-right: 1px solid #edf1f5;
  border-bottom: 1px solid #edf1f5;
}

.source-grid > div:nth-child(3n) {
  border-right: 0;
}

.source-grid > div:nth-last-child(-n + 3) {
  border-bottom: 0;
}

.source-grid dt {
  margin-bottom: 5px;
  color: #8a96a8;
  font-size: 11px;
}

.source-grid dd {
  margin: 0;
  overflow: hidden;
  color: #283548;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audit-form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 13px;
}

.audit-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.audit-field span {
  color: #596579;
  font-size: 12px;
  font-weight: 650;
}

.audit-field em {
  color: #dc2626;
  font-style: normal;
}

.audit-field input,
.audit-field select {
  width: 100%;
  height: 38px;
  min-width: 0;
  padding: 0 10px;
  color: #344054;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  outline: none;
  font: inherit;
}

.audit-field input:focus,
.audit-field select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.12);
}

.audit-field input:disabled,
.audit-field select:disabled {
  color: #8a96a8;
  background: #f8fafc;
}

.audit-field small {
  min-height: 15px;
  color: #dc2626;
  font-size: 11px;
}

.wide-field {
  grid-column: 1 / -1;
}

.selected-product {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  color: #596579;
  background: #f8fafc;
  border: 1px solid #edf1f5;
  border-radius: 5px;
  font-size: 12px;
}

.selected-product strong {
  color: #283548;
  font-size: 13px;
}

.selected-product small {
  color: #8a96a8;
}

.options-state {
  display: flex;
  min-height: 78px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #7a8698;
  font-size: 12px;
}

.options-state.error,
.form-error {
  color: #b42318;
  background: #fff1f0;
  border: 1px solid #fecaca;
  border-radius: 5px;
}

.options-state.error {
  padding: 12px;
}

.inline-button {
  padding: 4px 8px;
  color: var(--accent-dark);
  background: #fff;
  border: 1px solid #a9e5d2;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.form-error {
  margin-top: 12px;
  padding: 10px 12px;
  font-size: 12px;
}

.audit-footer {
  flex-wrap: wrap;
  border-top: 1px solid #dfe5ec;
}

.audit-summary,
.audit-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.audit-summary {
  color: #7a8698;
  font-size: 12px;
}

.audit-summary strong {
  margin-left: 4px;
  color: var(--accent-dark);
  font-size: 14px;
}

.audit-actions {
  margin-left: auto;
}

.audit-button {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 650;
}

.audit-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.audit-button.secondary {
  color: #475569;
  background: #fff;
  border-color: #cbd5e1;
}

.audit-button.primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.audit-button.primary:hover:not(:disabled) {
  background: var(--accent-dark);
}

@media (max-width: 720px) {
  .material-audit-overlay {
    padding: 10px;
  }

  .material-audit-modal {
    width: calc(100vw - 20px);
    max-height: calc(100vh - 20px);
  }

  .source-grid,
  .audit-form-grid {
    grid-template-columns: 1fr;
  }

  .source-grid > div,
  .source-grid > div:nth-child(3n),
  .source-grid > div:nth-last-child(-n + 3) {
    border-right: 0;
    border-bottom: 1px solid #edf1f5;
  }

  .source-grid > div:last-child {
    border-bottom: 0;
  }

  .audit-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .audit-summary,
  .audit-actions {
    width: 100%;
  }

  .audit-actions {
    margin-left: 0;
  }

  .audit-button {
    flex: 1;
  }
}
</style>
