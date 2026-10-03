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
            <span class="audit-eyebrow">ERP · 原材料出库</span>
            <h2 id="materialAuditTitle">{{ record?.documentNo || '审核出库单' }}</h2>
            <p>补齐成品入库明细后，审核将同时完成原材料出库和成品入库。</p>
          </div>
          <div class="audit-header-actions">
            <button
              type="button"
              class="audit-close"
              aria-label="关闭"
              :disabled="saving"
              @click="requestClose"
            >
              ×
            </button>
            <span class="audit-status">待审核</span>
            <button
              type="button"
              class="audit-button primary header-audit-button"
              :disabled="saving || optionsLoading || Boolean(optionsError)"
              @click="submitAudit"
            >
              {{ saving ? '正在审核...' : '审核并入库' }}
            </button>
          </div>
        </header>

        <div class="audit-body">
          <section class="audit-section source-section">
            <div class="section-heading">
              <span class="section-index">1</span>
              <div>
                <h3>触屏端辅助输入</h3>
                <p>以下字段由员工在触屏端录入，审核员无需重复填写。</p>
              </div>
            </div>
            <div class="source-strip">
              <div class="source-item">
                <span>门店</span>
                <strong>{{ record?.storeName || '-' }}</strong>
              </div>
              <div class="source-item">
                <span>出库仓库</span>
                <strong>{{ record?.warehouseName || '-' }}</strong>
              </div>
              <div class="source-item">
                <span>原材料</span>
                <strong>{{ record?.primaryItem?.productName || '-' }}</strong>
              </div>
              <div class="source-item number-source">
                <span>出库数量</span>
                <strong>
                  {{ formatNumber(record?.totalQuantity) }}
                  {{ record?.primaryItem?.unit || '' }}
                </strong>
              </div>
              <div class="source-item source-remark">
                <span>触屏备注</span>
                <strong>{{ record?.remark || '-' }}</strong>
              </div>
            </div>
          </section>

          <section class="audit-section detail-section">
            <div class="section-heading">
              <span class="section-index">2</span>
              <div>
                <h3>原材料出库及成品入库明细</h3>
                <p>灰色字段为触屏端数据，白色字段需要审核员补充。</p>
              </div>
            </div>

            <div v-if="optionsLoading" class="options-state">正在加载仓库和成品资料...</div>
            <div v-else-if="optionsError" class="options-state error">
              <span>{{ optionsError }}</span>
              <button type="button" class="inline-button" @click="loadOptions">重新加载</button>
            </div>
            <div v-else class="detail-table-wrap">
              <table class="audit-detail-table">
                <thead>
                  <tr>
                    <th class="index-col">行号</th>
                    <th class="material-col">原材料</th>
                    <th>规格型号</th>
                    <th class="unit-col">单位</th>
                    <th>出库仓库</th>
                    <th class="number-col">出库数量</th>
                    <th class="required-head">成品入库仓库</th>
                    <th class="product-col required-head">成品商品</th>
                    <th class="number-col required-head">入库数量</th>
                    <th class="remark-col">备注</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="index-col">1</td>
                    <td class="material-cell readonly-cell">
                      <strong>{{ record?.primaryItem?.productName || '-' }}</strong>
                      <small>{{ record?.primaryItem?.productCode || '无编码' }}</small>
                    </td>
                    <td class="readonly-cell">
                      {{ record?.primaryItem?.specification || '-' }}
                    </td>
                    <td class="readonly-cell unit-cell">
                      {{ record?.primaryItem?.unit || '-' }}
                    </td>
                    <td class="readonly-cell">
                      {{ record?.warehouseName || '-' }}
                    </td>
                    <td class="readonly-cell number-cell">
                      {{ formatNumber(record?.totalQuantity) }}
                    </td>
                    <td>
                      <select
                        v-model="form.finishedWarehouseId"
                        class="table-control"
                        :class="{ invalid: errors.finishedWarehouseId }"
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
                        class="table-control"
                        :class="{ invalid: errors.finishedProductId }"
                        :disabled="!form.finishedWarehouseId"
                      >
                        <option value="">
                          {{ form.finishedWarehouseId ? '请选择成品' : '请先选仓库' }}
                        </option>
                        <option
                          v-for="product in availableProducts"
                          :key="product.id"
                          :value="String(product.id)"
                        >
                          {{ product.code ? `${product.code} · ` : '' }}{{ product.name }}
                        </option>
                      </select>
                      <small v-if="selectedProduct" class="cell-hint">
                        {{ selectedProduct.specification || '无规格' }}
                        · {{ productUnit(selectedProduct) || '未设置单位' }}
                      </small>
                      <small v-if="errors.finishedProductId" class="cell-error">
                        {{ errors.finishedProductId }}
                      </small>
                    </td>
                    <td>
                      <input
                        v-model="form.finishedQuantity"
                        class="table-control number-input"
                        :class="{ invalid: errors.finishedQuantity }"
                        type="number"
                        min="0"
                        step="0.0001"
                        placeholder="实际数量"
                      />
                      <small v-if="errors.finishedQuantity" class="cell-error">
                        {{ errors.finishedQuantity }}
                      </small>
                    </td>
                    <td>
                      <input
                        v-model.trim="form.finishedRemark"
                        class="table-control"
                        type="text"
                        maxlength="200"
                        placeholder="默认继承触屏备注"
                      />
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="5" class="summary-label">合计</td>
                    <td class="number-cell">
                      {{ formatNumber(record?.totalQuantity) }}
                      {{ record?.primaryItem?.unit || '' }}
                    </td>
                    <td colspan="2" class="summary-label finished-summary-label">成品入库合计</td>
                    <td class="number-cell finished-total">
                      {{ formatNumber(form.finishedQuantity || 0) }}
                      {{ productUnit(selectedProduct) || 'kg' }}
                    </td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div v-if="formError" class="form-error">{{ formError }}</div>
          </section>

          <section class="audit-section document-meta-section">
            <div class="section-heading">
              <span class="section-index">3</span>
              <div>
                <h3>制单与审核信息</h3>
                <p>单据来源和审核记录由系统自动保留。</p>
              </div>
            </div>
            <dl class="document-meta-grid">
              <div>
                <dt>制单人</dt>
                <dd>{{ record?.createdBy || '-' }}</dd>
              </div>
              <div>
                <dt>制单时间</dt>
                <dd>{{ record?.createdAt || '-' }}</dd>
              </div>
              <div>
                <dt>单据来源</dt>
                <dd>{{ record?.source === 'touch' ? '触屏端辅助输入' : (record?.source || '-') }}</dd>
              </div>
              <div>
                <dt>审核人</dt>
                <dd>{{ record?.auditedBy || '待审核' }}</dd>
              </div>
              <div>
                <dt>审核时间</dt>
                <dd>{{ record?.auditedAt || '待审核' }}</dd>
              </div>
              <div>
                <dt>审核结果</dt>
                <dd><span class="meta-status">审核后扣减原材料并完成成品入库</span></dd>
              </div>
            </dl>
          </section>
        </div>

        <footer class="audit-footer">
          <div class="audit-footer-summary">
            <span>原材料出库 <strong>{{ formatNumber(record?.totalQuantity) }} {{ record?.primaryItem?.unit || '' }}</strong></span>
            <span>成品入库 <strong>{{ formatNumber(form.finishedQuantity || 0) }} {{ productUnit(selectedProduct) || 'kg' }}</strong></span>
          </div>
          <button type="button" class="audit-button secondary" :disabled="saving" @click="requestClose">
            关闭
          </button>
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
  width: min(1280px, calc(100vw - 44px));
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

.audit-header-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 9px;
}

.audit-status {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 0 10px;
  color: #a15c00;
  background: #fff5df;
  border: 1px solid #f4d99a;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
}

.header-audit-button {
  min-height: 38px;
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

.source-strip {
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr 1fr 1.7fr;
  overflow: hidden;
  border: 1px solid #edf1f5;
  border-radius: 5px;
}

.source-item {
  min-width: 0;
  padding: 11px 12px;
  border-right: 1px solid #edf1f5;
}

.source-item:last-child {
  border-right: 0;
}

.source-item span,
.source-item strong {
  display: block;
}

.source-item span {
  margin-bottom: 5px;
  color: #8a96a8;
  font-size: 11px;
}

.source-item strong {
  overflow: hidden;
  color: #283548;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.number-source strong {
  color: var(--accent-dark);
}

.detail-table-wrap {
  overflow-x: auto;
  border: 1px solid #dfe5ec;
  border-radius: 5px;
}

.audit-detail-table {
  width: 100%;
  min-width: 1160px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 12px;
}

.audit-detail-table th,
.audit-detail-table td {
  padding: 10px 9px;
  border-right: 1px solid #edf1f5;
  border-bottom: 1px solid #edf1f5;
  text-align: left;
  vertical-align: top;
}

.audit-detail-table th {
  color: #596579;
  background: #f8fafc;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.audit-detail-table th:last-child,
.audit-detail-table td:last-child {
  border-right: 0;
}

.audit-detail-table tfoot td {
  border-bottom: 0;
  color: #596579;
  background: #fbfcfd;
  font-weight: 650;
}

.index-col {
  width: 48px;
  text-align: center !important;
}

.material-col {
  width: 150px;
}

.product-col {
  width: 190px;
}

.unit-col {
  width: 68px;
}

.number-col {
  width: 100px;
  text-align: right !important;
}

.remark-col {
  width: 190px;
}

.readonly-cell {
  color: #526076;
  background: #f8fafc;
}

.material-cell strong,
.material-cell small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.material-cell strong {
  color: #283548;
  font-size: 13px;
}

.material-cell small,
.cell-hint {
  margin-top: 4px;
  color: #8a96a8;
  font-size: 11px;
}

.unit-cell,
.number-cell {
  font-variant-numeric: tabular-nums;
}

.number-cell {
  text-align: right !important;
}

.table-control {
  width: 100%;
  min-width: 0;
  height: 35px;
  padding: 0 8px;
  color: #344054;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  outline: none;
  font: inherit;
}

.table-control:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(15, 159, 120, 0.12);
}

.table-control:disabled {
  color: #8a96a8;
  background: #f8fafc;
}

.table-control.invalid {
  border-color: #dc2626;
  background: #fffafa;
}

.number-input {
  text-align: right;
}

.cell-error,
.cell-hint {
  display: block;
  line-height: 1.35;
}

.cell-error {
  margin-top: 4px;
  color: #b42318;
  font-size: 11px;
}

.required-head::after {
  margin-left: 3px;
  color: #dc2626;
  content: '*';
}

.summary-label {
  text-align: right !important;
}

.finished-summary-label {
  color: var(--accent-dark) !important;
}

.finished-total {
  color: var(--accent-dark) !important;
}

.options-state {
  display: flex;
  min-height: 96px;
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

.document-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
  overflow: hidden;
  border: 1px solid #edf1f5;
  border-radius: 5px;
}

.document-meta-grid > div {
  min-width: 0;
  padding: 10px 12px;
  border-right: 1px solid #edf1f5;
  border-bottom: 1px solid #edf1f5;
}

.document-meta-grid > div:nth-child(3n) {
  border-right: 0;
}

.document-meta-grid > div:nth-last-child(-n + 3) {
  border-bottom: 0;
}

.document-meta-grid dt {
  margin-bottom: 5px;
  color: #8a96a8;
  font-size: 11px;
}

.document-meta-grid dd {
  margin: 0;
  overflow: hidden;
  color: #283548;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-status {
  color: var(--accent-dark);
  font-size: 12px;
}

.audit-footer {
  flex-wrap: wrap;
  border-top: 1px solid #dfe5ec;
}

.audit-footer-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #7a8698;
  font-size: 12px;
}

.audit-footer-summary strong {
  margin-left: 4px;
  color: var(--accent-dark);
  font-size: 14px;
}

.audit-footer > .audit-button {
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

  .audit-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .audit-header-actions {
    width: 100%;
  }

  .header-audit-button {
    flex: 1;
  }

  .source-strip {
    grid-template-columns: 1fr;
  }

  .source-item,
  .source-item:last-child {
    border-right: 0;
    border-bottom: 1px solid #edf1f5;
  }

  .source-item:last-child {
    border-bottom: 0;
  }

  .document-meta-grid {
    grid-template-columns: 1fr;
  }

  .document-meta-grid > div,
  .document-meta-grid > div:nth-child(3n),
  .document-meta-grid > div:nth-last-child(-n + 3) {
    border-right: 0;
    border-bottom: 1px solid #edf1f5;
  }

  .document-meta-grid > div:last-child {
    border-bottom: 0;
  }

  .audit-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .audit-footer-summary {
    width: 100%;
    justify-content: space-between;
    gap: 8px;
  }

  .audit-footer > .audit-button {
    width: 100%;
    margin-left: 0;
  }
}
</style>
