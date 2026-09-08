<template>
  <teleport to="body">
    <div
      v-if="visibleState"
      class="stock-in-modal-overlay"
      role="presentation"
      @click.self="requestClose"
    >
      <section
        class="stock-in-modal"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="modalTitleId"
        @click.stop
      >
        <header class="stock-in-header">
          <div>
            <span class="stock-in-eyebrow">ERP · 库存业务</span>
            <h2 :id="modalTitleId">{{ isEdit ? '编辑入库单' : '新建入库单' }}</h2>
          </div>
          <div class="stock-in-header-meta">
            <span :class="['status-pill', `status-${form.status}`]">{{ statusLabel }}</span>
            <button class="stock-in-close" type="button" title="关闭" @click="requestClose">×</button>
          </div>
        </header>

        <div class="stock-in-body">
          <div class="stock-in-section">
            <div class="section-title">
              <span class="section-index">1</span>
              <h3>单据基本信息</h3>
            </div>

            <div class="form-grid form-grid-3">
              <label class="form-field">
                <span>门店</span>
                <select v-model="form.storeId" @change="handleStoreChange">
                  <option value="">请选择门店</option>
                  <option v-for="store in stores" :key="store.id" :value="store.id">
                    {{ store.name }}
                  </option>
                </select>
              </label>

              <label class="form-field">
                <span>入库单号</span>
                <input v-model="form.documentNo" type="text" readonly class="readonly" />
              </label>

              <label class="form-field" :class="{ invalid: errors.documentDate }">
                <span>单据日期 <em>*</em></span>
                <input v-model="form.documentDate" type="date" />
                <small v-if="errors.documentDate" class="field-error">{{ errors.documentDate }}</small>
              </label>

              <label class="form-field">
                <span>入库类型</span>
                <input :value="typeLabel" type="text" readonly class="readonly" />
              </label>

              <label class="form-field" :class="{ invalid: errors.warehouseId }">
                <span>目标仓库 <em>*</em></span>
                <select v-model="form.warehouseId" @change="handleWarehouseChange">
                  <option value="">请选择仓库</option>
                  <option v-for="warehouse in filteredWarehouses" :key="warehouse.id" :value="warehouse.id">
                    {{ warehouse.name }}
                  </option>
                </select>
                <small v-if="errors.warehouseId" class="field-error">{{ errors.warehouseId }}</small>
              </label>

              <label v-if="isRawMaterial" class="form-field" :class="{ invalid: errors.supplierId }">
                <span>供应商 <em>*</em></span>
                <select v-model="form.supplierId">
                  <option value="">请选择供应商</option>
                  <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
                    {{ supplier.name || supplier.supplierName }}
                  </option>
                </select>
                <small v-if="errors.supplierId" class="field-error">{{ errors.supplierId }}</small>
              </label>

              <label v-else class="form-field">
                <span>生产车间 / 班组</span>
                <select v-model="form.workshop">
                  <option value="">请选择车间（选填）</option>
                  <option v-for="workshop in workshops" :key="workshop" :value="workshop">{{ workshop }}</option>
                </select>
              </label>
            </div>
          </div>

          <div class="stock-in-section detail-section">
            <div class="section-title section-title-with-actions">
              <div class="section-title-main">
                <span class="section-index">2</span>
                <div>
                  <h3>入库明细</h3>
                  <p>选择物料后自动带出规格和基本计量单位</p>
                </div>
              </div>
              <div class="detail-actions">
                <button type="button" class="btn btn-light" @click="addRow">＋ 添加物料行</button>
                <button type="button" class="btn btn-danger-light" :disabled="selectedRows.length === 0" @click="removeSelectedRows">
                  批量删除
                </button>
              </div>
            </div>

            <div class="detail-table-wrap">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th class="check-col"><input type="checkbox" :checked="allRowsSelected" @change="toggleAllRows" /></th>
                    <th class="index-col">行号</th>
                    <th class="material-col">物料编码 / 名称</th>
                    <th>规格型号</th>
                    <th class="unit-col">单位</th>
                    <th class="number-col">应收数量</th>
                    <th class="number-col required-head">实收数量</th>
                    <th>货位编码</th>
                    <th class="batch-col required-head">批次号</th>
                    <th class="number-col">单价</th>
                    <th class="tax-col">税率</th>
                    <th class="money-col">价税合计</th>
                    <th class="action-col">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in form.items" :key="row._key" :class="{ 'row-invalid': rowErrors[index] }">
                    <td class="check-col"><input v-model="selectedRows" type="checkbox" :value="row._key" /></td>
                    <td class="index-col">{{ index + 1 }}</td>
                    <td class="material-cell">
                      <select v-model="row.productId" @change="handleProductChange(row)">
                        <option value="">请选择物料</option>
                        <option v-for="product in availableProducts" :key="product.id" :value="product.id">
                          {{ product.code || '无编码' }} · {{ product.name }}
                        </option>
                      </select>
                      <small v-if="row.code">{{ row.code }}</small>
                    </td>
                    <td><input v-model="row.specification" type="text" readonly class="readonly" /></td>
                    <td><input v-model="row.unit" type="text" readonly class="readonly unit-input" /></td>
                    <td><input :value="formatQuantity(row.expectedQty)" type="text" readonly class="readonly number-input" /></td>
                    <td>
                      <input
                        v-model.number="row.receivedQty"
                        type="number"
                        min="0"
                        step="0.01"
                        class="number-input"
                        :class="{ invalid: rowErrors[index] && rowErrors[index].includes('实收') }"
                        @input="normalizeQuantity(row)"
                      />
                    </td>
                    <td><input v-model.trim="row.binCode" type="text" placeholder="货位" /></td>
                    <td>
                      <input
                        v-model.trim="row.batchNo"
                        type="text"
                        placeholder="必填"
                        :class="{ invalid: rowErrors[index] && rowErrors[index].includes('批次') }"
                      />
                    </td>
                    <td><input v-model.number="row.unitPrice" type="number" min="0" step="0.0001" class="number-input" @input="normalizePrice(row)" /></td>
                    <td>
                      <select v-model.number="row.taxRate" class="tax-select">
                        <option v-for="rate in taxRates" :key="rate" :value="rate">{{ rate }}%</option>
                      </select>
                    </td>
                    <td class="money-cell">{{ formatMoney(rowTotal(row)) }}</td>
                    <td class="action-col"><button type="button" class="row-delete" title="删除" @click="removeRow(index)">删除</button></td>
                  </tr>
                  <tr v-if="form.items.length === 0">
                    <td colspan="13" class="empty-detail">暂无物料，点击“添加物料行”开始录入</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="5" class="summary-label">合计</td>
                    <td class="number-cell">—</td>
                    <td class="number-cell">{{ formatQuantity(summary.totalQuantity) }}</td>
                    <td colspan="3"></td>
                    <td class="tax-cell">税额 {{ formatMoney(summary.totalTax) }}</td>
                    <td class="money-cell total-money">{{ formatMoney(summary.totalAmount) }}</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
            <p v-if="errors.items" class="table-error">{{ errors.items }}</p>
          </div>

          <div class="stock-in-section">
            <div class="section-title">
              <span class="section-index">3</span>
              <h3>质检与备注</h3>
            </div>
            <div class="form-grid form-grid-3 audit-grid">
              <label class="form-field"><span>检验员</span><input v-model.trim="form.inspector" type="text" placeholder="选填" /></label>
              <label class="form-field"><span>质检单号</span><input v-model.trim="form.qualityNo" type="text" placeholder="选填" /></label>
              <label class="form-field attachment-field">
                <span>附件</span>
                <input ref="fileInput" type="file" multiple accept="image/*,.pdf" @change="handleFiles" />
                <small v-if="form.attachments.length" class="attachment-list">
                  {{ form.attachments.map(file => file.name).join('、') }}
                </small>
              </label>
              <label class="form-field form-field-wide">
                <span>备注 <small>（{{ form.remark.length }}/200）</small></span>
                <textarea v-model.trim="form.remark" rows="3" maxlength="200" placeholder="请输入备注"></textarea>
              </label>
            </div>
          </div>
        </div>

        <footer class="stock-in-footer">
          <div class="footer-summary">
            <span>实收总数量 <strong>{{ formatQuantity(summary.totalQuantity) }}</strong></span>
            <span>总税额 <strong>¥{{ formatMoney(summary.totalTax) }}</strong></span>
            <span>价税合计 <strong class="accent">¥{{ formatMoney(summary.totalAmount) }}</strong></span>
          </div>
          <div class="footer-actions">
            <button type="button" class="btn btn-ghost" :disabled="saving" @click="requestClose">取消 / 关闭</button>
            <button type="button" class="btn btn-secondary" :disabled="saving" @click="save('draft')">保存草稿</button>
            <button type="button" class="btn btn-primary" :disabled="saving" @click="save('posted')">
              <span v-if="saving" class="spinner"></span>
              {{ saving ? '处理中…' : '提交过账' }}
            </button>
          </div>
        </footer>

        <div v-if="confirmCloseVisible" class="inner-confirm-overlay">
          <div class="inner-confirm" role="alertdialog" aria-modal="true">
            <div class="confirm-mark">!</div>
            <h3>确定关闭入库单？</h3>
            <p>当前表单有未保存的修改，关闭后内容将丢失。</p>
            <div class="confirm-actions">
              <button type="button" class="btn btn-ghost" @click="confirmCloseVisible = false">继续编辑</button>
              <button type="button" class="btn btn-danger" @click="closeWithoutSave">放弃修改</button>
            </div>
          </div>
        </div>

        <div v-if="notice.visible" :class="['stock-in-notice', `notice-${notice.type}`]" role="status">
          <span class="notice-icon">{{ notice.type === 'success' ? '✓' : '!' }}</span>
          {{ notice.message }}
        </div>
      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import request from '@/api/request'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  visible: { type: Boolean, default: undefined },
  type: { type: String, default: 'raw-material' },
  mode: { type: String, default: 'create' },
  initialItem: { type: Object, default: null },
  initialData: { type: Object, default: null }
})

const emit = defineEmits([
  'update:modelValue',
  'update:visible',
  'saved',
  'submitted',
  'draft-saved',
  'close'
])

const modalTitleId = `stock-in-title-${Math.random().toString(36).slice(2)}`
const internalVisible = ref(false)
const activeType = ref(props.type)
const activeMode = ref(props.mode)
const activeInitialItem = ref(props.initialItem)
const activeInitialData = ref(props.initialData)
const saving = ref(false)
const confirmCloseVisible = ref(false)
const fileInput = ref(null)
const selectedRows = ref([])
const snapshot = ref('')
const stores = ref([])
const warehouses = ref([])
const products = ref([])
const rawProducts = ref([])
const suppliers = ref([])
const units = ref([])
const notice = reactive({ visible: false, type: 'success', message: '' })
const errors = reactive({ documentDate: '', warehouseId: '', supplierId: '', items: '' })
const rowErrors = ref([])
const workshops = ['大车间', '小车间']
const taxRates = [0, 6, 9, 13]

const blankRow = () => ({
  _key: `row-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  productId: '',
  code: '',
  name: '',
  specification: '',
  unit: '',
  expectedQty: null,
  receivedQty: null,
  binCode: '',
  batchNo: '',
  unitPrice: null,
  taxRate: 13,
  currentStock: 0,
  remark: ''
})

const today = () => {
  const date = new Date()
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 10)
}

const defaultForm = () => ({
  storeId: '',
  documentNo: `RK${today().replaceAll('-', '')}${String(Math.floor(Math.random() * 900) + 100)}`,
  documentDate: today(),
  warehouseId: '',
  supplierId: '',
  workshop: '',
  inspector: '',
  qualityNo: '',
  remark: '',
  attachments: [],
  status: 'draft',
  items: [blankRow()]
})

const form = reactive(defaultForm())

const normalizedType = (value) => {
  const text = String(value || '').toLowerCase()
  return text === 'finished' || text === 'finished-product' || text === 'product' || text === 'goods'
    ? 'finished-product'
    : 'raw-material'
}

const isRawMaterial = computed(() => normalizedType(activeType.value) === 'raw-material')
const typeLabel = computed(() => isRawMaterial.value ? '原材料采购入库' : '成品生产完工入库')
const isEdit = computed(() => activeMode.value === 'edit' || Boolean(activeInitialData.value?.id))
const visibleState = computed(() => props.visible !== undefined ? props.visible : (props.modelValue || internalVisible.value))
const availableProducts = computed(() => isRawMaterial.value ? rawProducts.value : products.value)
const filteredWarehouses = computed(() => {
  if (!form.storeId) return warehouses.value
  const filtered = warehouses.value.filter(item => String(item.storeId ?? item.store_id) === String(form.storeId))
  return filtered.length ? filtered : warehouses.value
})
const statusLabel = computed(() => ({ draft: '草稿', posted: '已过账', cancelled: '已作废' }[form.status] || '草稿'))
const allRowsSelected = computed(() => form.items.length > 0 && form.items.every(row => selectedRows.value.includes(row._key)))

const round = (value, digits = 2) => {
  const factor = 10 ** digits
  return Math.round((Number(value) + Number.EPSILON) * factor) / factor
}
const toNumber = value => Number.isFinite(Number(value)) ? Number(value) : 0
const rowTax = row => round(toNumber(row.receivedQty) * toNumber(row.unitPrice) * (toNumber(row.taxRate) / 100), 2)
const rowTotal = row => round(toNumber(row.receivedQty) * toNumber(row.unitPrice) + rowTax(row), 2)
const summary = computed(() => form.items.reduce((total, row) => ({
  totalQuantity: round(total.totalQuantity + toNumber(row.receivedQty), 2),
  totalTax: round(total.totalTax + rowTax(row), 2),
  totalAmount: round(total.totalAmount + rowTotal(row), 2)
}), { totalQuantity: 0, totalTax: 0, totalAmount: 0 }))
const formatMoney = value => toNumber(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const formatQuantity = value => toNumber(value).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })

const clearErrors = () => {
  errors.documentDate = ''
  errors.warehouseId = ''
  errors.supplierId = ''
  errors.items = ''
  rowErrors.value = []
}

const setForm = (data = null, item = null) => {
  const base = defaultForm()
  const source = data || {}
  Object.assign(form, base, {
    storeId: source.storeId ?? source.store_id ?? '',
    documentNo: source.documentNo || source.document_no || base.documentNo,
    documentDate: String(source.documentDate || source.document_date || base.documentDate).slice(0, 10),
    warehouseId: source.warehouseId ?? source.warehouse_id ?? '',
    supplierId: source.supplierId ?? source.supplier_id ?? '',
    workshop: source.workshop || source.productionWorkshop || '',
    inspector: source.inspector || '',
    qualityNo: source.qualityNo || source.quality_no || '',
    remark: source.remark || '',
    attachments: Array.isArray(source.attachments) ? source.attachments.map(file => ({ name: file.name || String(file) })) : [],
    status: source.status || 'draft',
    items: Array.isArray(source.items) && source.items.length
      ? source.items.map(itemValue => normalizeRow(itemValue))
      : (item ? [normalizeRow(item)] : [blankRow()])
  })
  selectedRows.value = []
  clearErrors()
  snapshot.value = JSON.stringify(serializableForm())
}

const normalizeRow = (value = {}) => ({
  ...blankRow(),
  _key: value._key || `row-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  productId: value.productId ?? value.product_id ?? '',
  code: value.code || value.productCode || value.product_code || '',
  name: value.name || value.productName || value.product_name || '',
  specification: value.specification || value.spec || '',
  unit: value.unit || value.unitName || '',
  expectedQty: value.expectedQty ?? value.expected_qty ?? value.receivableQty ?? null,
  receivedQty: value.receivedQty ?? value.received_qty ?? value.quantity ?? null,
  binCode: value.binCode || value.bin_code || '',
  batchNo: value.batchNo || value.batch_no || '',
  unitPrice: value.unitPrice ?? value.unit_price ?? value.price ?? null,
  taxRate: value.taxRate ?? value.tax_rate ?? 13,
  currentStock: value.currentStock ?? value.current_stock ?? 0,
  remark: value.remark || ''
})

const serializableForm = () => ({
  storeId: form.storeId,
  documentNo: form.documentNo,
  documentDate: form.documentDate,
  warehouseId: form.warehouseId,
  supplierId: form.supplierId,
  workshop: form.workshop,
  inspector: form.inspector,
  qualityNo: form.qualityNo,
  remark: form.remark,
  status: form.status,
  attachments: form.attachments.map(file => ({ name: file.name, size: file.size, type: file.type })),
  items: form.items.map(row => ({ ...row, totalAmount: rowTotal(row), taxAmount: rowTax(row) }))
})

const markDirty = () => {
  // Kept as a function for consumers that mutate rows programmatically.
  // The computed comparison in isDirty always reads the current reactive state.
}
const isDirty = computed(() => JSON.stringify(serializableForm()) !== snapshot.value)

const loadData = async () => {
  const calls = [
    request({ url: '/stores', method: 'GET' }),
    request({ url: '/warehouses', method: 'GET' }),
    request({ url: isRawMaterial.value ? '/raw-material-products' : '/products', method: 'GET' }),
    request({ url: '/products/units/measurements', method: 'GET' }),
    request({ url: '/suppliers', method: 'GET' })
  ]
  const results = await Promise.allSettled(calls)
  const valueAt = index => results[index].status === 'fulfilled' ? results[index].value : []
  stores.value = Array.isArray(valueAt(0)) ? valueAt(0) : []
  warehouses.value = Array.isArray(valueAt(1)) ? valueAt(1) : []
  if (isRawMaterial.value) rawProducts.value = Array.isArray(valueAt(2)) ? valueAt(2) : []
  else products.value = Array.isArray(valueAt(2)) ? valueAt(2) : []
  units.value = Array.isArray(valueAt(3)) ? valueAt(3) : (valueAt(3)?.measurements || [])
  suppliers.value = Array.isArray(valueAt(4)) ? valueAt(4) : []
  hydrateRows()
}

const hydrateRows = () => {
  form.items.forEach(row => {
    if (row.productId) handleProductChange(row, false)
  })
}

const handleStoreChange = () => {
  const valid = filteredWarehouses.value.some(item => String(item.id) === String(form.warehouseId))
  if (!valid) form.warehouseId = ''
}
const handleWarehouseChange = () => { if (errors.warehouseId) errors.warehouseId = '' }

const handleProductChange = (row, resetValues = true) => {
  const product = availableProducts.value.find(item => String(item.id) === String(row.productId))
  if (!product) return
  row.code = product.code || ''
  row.name = product.name || ''
  row.specification = product.specification || product.spec || ''
  row.unit = product.unitName || units.value.find(unit => String(unit.id) === String(product.unitId))?.name || product.unit || ''
  row.currentStock = product.stock || 0
  if (resetValues && (row.unitPrice === null || row.unitPrice === '')) row.unitPrice = product.costPrice ?? product.price ?? null
  if (resetValues && !row.expectedQty && product.expectedQty) row.expectedQty = product.expectedQty
}

const addRow = () => form.items.push(blankRow())
const removeRow = index => {
  const key = form.items[index]?._key
  form.items.splice(index, 1)
  selectedRows.value = selectedRows.value.filter(item => item !== key)
}
const toggleAllRows = event => { selectedRows.value = event.target.checked ? form.items.map(row => row._key) : [] }
const removeSelectedRows = () => {
  const selected = new Set(selectedRows.value)
  form.items = form.items.filter(row => !selected.has(row._key))
  selectedRows.value = []
}
const normalizeQuantity = row => { if (row.receivedQty !== null && row.receivedQty !== '') row.receivedQty = round(Math.max(0, toNumber(row.receivedQty)), 2) }
const normalizePrice = row => { if (row.unitPrice !== null && row.unitPrice !== '') row.unitPrice = round(Math.max(0, toNumber(row.unitPrice)), 4) }

const handleFiles = event => {
  const files = Array.from(event.target.files || [])
  form.attachments = files.map(file => ({ name: file.name, size: file.size, type: file.type }))
}

const validate = (submit = false) => {
  clearErrors()
  let valid = true
  if (!form.documentDate) { errors.documentDate = '请选择单据日期'; valid = false }
  if (!form.warehouseId) { errors.warehouseId = '请选择目标仓库'; valid = false }
  if (submit && isRawMaterial.value && !form.supplierId) { errors.supplierId = '请选择供应商'; valid = false }
  const validRows = form.items.filter(row => row.productId && toNumber(row.receivedQty) > 0)
  if (submit && validRows.length === 0) { errors.items = '提交过账至少需要 1 条有效物料明细'; valid = false }
  if (submit) {
    rowErrors.value = form.items.map(row => {
      if (!row.productId) return '请选择物料'
      if (toNumber(row.receivedQty) <= 0) return '实收数量必须大于 0'
      if (!String(row.batchNo || '').trim()) return '批次号不能为空'
      return ''
    })
    if (rowErrors.value.some(Boolean)) valid = false
  }
  return valid
}

const payload = status => ({
  id: activeInitialData.value?.id,
  storeId: form.storeId || null,
  documentNo: form.documentNo,
  documentDate: form.documentDate,
  type: normalizedType(activeType.value),
  warehouseId: form.warehouseId || null,
  supplierId: isRawMaterial.value ? (form.supplierId || null) : null,
  workshop: isRawMaterial.value ? null : (form.workshop || null),
  inspector: form.inspector,
  qualityNo: form.qualityNo,
  remark: form.remark,
  attachments: form.attachments,
  status,
  items: form.items.filter(row => row.productId || row.name).map(row => ({
    productId: row.productId || null,
    code: row.code,
    name: row.name,
    specification: row.specification,
    unit: row.unit,
    expectedQty: row.expectedQty === '' ? null : row.expectedQty,
    receivedQty: row.receivedQty === '' ? null : row.receivedQty,
    binCode: row.binCode,
    batchNo: row.batchNo,
    unitPrice: row.unitPrice === '' ? null : row.unitPrice,
    taxRate: row.taxRate,
    taxAmount: rowTax(row),
    totalAmount: rowTotal(row),
    remark: row.remark
  }))
})

const showNotice = (message, type = 'success') => {
  notice.message = message
  notice.type = type
  notice.visible = true
  window.clearTimeout(showNotice.timer)
  showNotice.timer = window.setTimeout(() => { notice.visible = false }, 2600)
}

const save = async (status) => {
  if (saving.value) return
  if (!validate(status === 'posted')) { showNotice('请先完善必填信息', 'error'); return }
  saving.value = true
  try {
    const response = await request({
      url: isEdit.value && activeInitialData.value?.id ? `/stock-inbounds/${activeInitialData.value.id}` : '/stock-inbounds',
      method: isEdit.value && activeInitialData.value?.id ? 'PUT' : 'POST',
      data: payload(status)
    })
    const saved = response?.stockIn || response?.stockInbound || response?.receipt || response
    form.status = status
    snapshot.value = JSON.stringify(serializableForm())
    emit('saved', saved, status)
    if (status === 'posted') emit('submitted', saved)
    else emit('draft-saved', saved)
    showNotice(status === 'posted' ? '入库单已提交过账' : '入库草稿已保存')
    if (status === 'posted') {
      window.setTimeout(() => closeWithoutSave(), 450)
    }
  } catch (error) {
    console.error('保存入库单失败', error)
    showNotice(error?.response?.data?.message || error?.message || '保存失败，请稍后重试', 'error')
  } finally {
    saving.value = false
  }
}

const requestClose = () => {
  if (saving.value) return
  if (isDirty.value) confirmCloseVisible.value = true
  else closeWithoutSave()
}
const closeWithoutSave = () => {
  confirmCloseVisible.value = false
  internalVisible.value = false
  emit('update:modelValue', false)
  emit('update:visible', false)
  emit('close')
}

const open = async (options = {}) => {
  activeType.value = normalizedType(options.type || options.modeType || props.type)
  activeMode.value = options.mode || (options.data?.id || options.initialData?.id ? 'edit' : props.mode)
  activeInitialItem.value = options.item || options.initialItem || props.initialItem
  activeInitialData.value = options.data || options.initialData || props.initialData
  setForm(activeInitialData.value, activeInitialItem.value)
  internalVisible.value = true
  await nextTick()
  await loadData()
}

const close = requestClose

watch(() => props.type, value => { if (!internalVisible.value) activeType.value = normalizedType(value) })
watch(() => props.modelValue, value => { if (value && !internalVisible.value) open() })
watch(() => props.visible, value => { if (value && !internalVisible.value) open() })
watch(() => form.items.length, () => {
  selectedRows.value = selectedRows.value.filter(key => form.items.some(row => row._key === key))
})

defineExpose({ open, close })
</script>

<style scoped>
.stock-in-modal-overlay { position: fixed; inset: 0; z-index: 2147483000; display: flex; align-items: center; justify-content: center; padding: 22px; background: rgba(15, 23, 42, .58); }
.stock-in-modal { position: relative; display: flex; flex-direction: column; width: min(1440px, 96vw); max-height: 94vh; overflow: hidden; color: #1f2937; background: #f8fafc; border: 1px solid #dbe3ee; border-radius: 12px; box-shadow: 0 24px 80px rgba(15, 23, 42, .32); }
.stock-in-header, .stock-in-footer { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 18px 24px; background: #fff; }
.stock-in-header { border-bottom: 1px solid #e5e7eb; }
.stock-in-eyebrow { color: #64748b; font-size: 11px; letter-spacing: .12em; }
.stock-in-header h2 { margin: 4px 0 0; color: #0f172a; font-size: 22px; }
.stock-in-header-meta, .footer-actions, .detail-actions, .footer-summary { display: flex; align-items: center; gap: 10px; }
.status-pill { display: inline-flex; align-items: center; padding: 5px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.status-draft { color: #92400e; background: #fef3c7; }.status-posted { color: #166534; background: #dcfce7; }.status-cancelled { color: #991b1b; background: #fee2e2; }
.stock-in-close { width: 34px; height: 34px; color: #64748b; font-size: 26px; line-height: 1; background: transparent; border: 0; border-radius: 6px; cursor: pointer; }.stock-in-close:hover { background: #f1f5f9; }
.stock-in-body { overflow: auto; padding: 18px 24px 28px; }
.stock-in-section { margin-bottom: 18px; padding: 18px; background: #fff; border: 1px solid #e5e7eb; border-radius: 9px; }
.section-title { display: flex; align-items: center; gap: 9px; margin-bottom: 16px; }.section-title h3 { margin: 0; color: #1e293b; font-size: 16px; }.section-title p { margin: 4px 0 0; color: #94a3b8; font-size: 12px; }.section-index { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; color: #fff; background: #2563eb; border-radius: 50%; font-size: 12px; font-weight: 700; }.section-title-with-actions { justify-content: space-between; }.section-title-main { display: flex; align-items: center; gap: 9px; }
.form-grid { display: grid; gap: 14px 18px; }.form-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }.form-field { position: relative; display: flex; flex-direction: column; gap: 6px; min-width: 0; }.form-field > span { color: #475569; font-size: 13px; font-weight: 600; }.form-field em { color: #dc2626; font-style: normal; }.form-field input, .form-field select, .form-field textarea, .detail-table input, .detail-table select { box-sizing: border-box; width: 100%; min-height: 36px; padding: 7px 9px; color: #1f2937; background: #fff; border: 1px solid #d5dce7; border-radius: 5px; outline: none; font: inherit; font-size: 13px; }.form-field textarea { resize: vertical; }.form-field input:focus, .form-field select:focus, .form-field textarea:focus, .detail-table input:focus, .detail-table select:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37, 99, 235, .1); }.readonly { color: #64748b !important; background: #f8fafc !important; }.form-field.invalid > input, .form-field.invalid > select, .invalid { border-color: #ef4444 !important; }.field-error, .table-error { color: #dc2626; font-size: 12px; }.field-error { position: absolute; bottom: -17px; left: 0; }.form-field-wide { grid-column: 1 / -1; }.audit-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }.attachment-field input[type='file'] { padding: 5px; }.attachment-list { display: block; overflow: hidden; color: #64748b; text-overflow: ellipsis; white-space: nowrap; }
.detail-table-wrap { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 7px; }.detail-table { width: 100%; min-width: 1240px; border-collapse: collapse; table-layout: fixed; font-size: 12px; }.detail-table th { padding: 10px 7px; color: #64748b; background: #f8fafc; border-bottom: 1px solid #e2e8f0; font-weight: 700; white-space: nowrap; }.detail-table td { padding: 7px; border-bottom: 1px solid #eef2f7; vertical-align: middle; }.detail-table tbody tr:hover { background: #f8fbff; }.detail-table tbody tr.row-invalid { background: #fff7f7; }.detail-table tfoot td { padding: 11px 7px; color: #475569; background: #f8fafc; border-top: 1px solid #dbe3ee; font-weight: 600; }.detail-table .check-col { width: 30px; text-align: center; }.detail-table .index-col { width: 42px; text-align: center; }.detail-table .material-col { width: 190px; }.detail-table .unit-col { width: 64px; }.detail-table .number-col { width: 92px; text-align: right; }.detail-table .batch-col { width: 112px; }.detail-table .tax-col { width: 78px; }.detail-table .money-col { width: 110px; text-align: right; }.detail-table .action-col { width: 54px; text-align: center; }.detail-table .required-head::before { content: '*'; margin-right: 2px; color: #dc2626; }.material-cell small { display: block; margin-top: 3px; color: #94a3b8; }.number-input { text-align: right; }.unit-input { text-align: center; }.tax-select { min-width: 65px; }.money-cell, .number-cell { text-align: right; font-variant-numeric: tabular-nums; }.total-money { color: #1d4ed8 !important; font-size: 13px; }.summary-label { text-align: right; }.empty-detail { padding: 28px !important; color: #94a3b8; text-align: center; }.row-delete { padding: 4px 5px; color: #dc2626; background: transparent; border: 0; cursor: pointer; font-size: 12px; }.row-delete:hover { text-decoration: underline; }.table-error { margin: 8px 0 0; }
.btn { display: inline-flex; align-items: center; justify-content: center; min-height: 35px; padding: 0 13px; border: 1px solid transparent; border-radius: 5px; cursor: pointer; font: inherit; font-size: 13px; font-weight: 600; transition: .18s ease; }.btn:disabled { opacity: .55; cursor: not-allowed; }.btn-primary { color: #fff; background: #2563eb; border-color: #2563eb; }.btn-primary:hover:not(:disabled) { background: #1d4ed8; }.btn-secondary { color: #1e40af; background: #eff6ff; border-color: #bfdbfe; }.btn-light { color: #1d4ed8; background: #fff; border-color: #bfdbfe; }.btn-light:hover:not(:disabled), .btn-secondary:hover:not(:disabled) { background: #dbeafe; }.btn-danger-light { color: #b91c1c; background: #fff; border-color: #fecaca; }.btn-danger-light:hover:not(:disabled) { background: #fef2f2; }.btn-ghost { color: #475569; background: #fff; border-color: #cbd5e1; }.btn-danger { color: #fff; background: #dc2626; border-color: #dc2626; }.spinner { width: 13px; height: 13px; margin-right: 7px; border: 2px solid rgba(255,255,255,.45); border-top-color: #fff; border-radius: 50%; animation: stock-in-spin .7s linear infinite; }@keyframes stock-in-spin { to { transform: rotate(360deg); } }
.stock-in-footer { flex-wrap: wrap; border-top: 1px solid #e5e7eb; }.footer-summary { color: #64748b; font-size: 12px; }.footer-summary strong { margin-left: 4px; color: #1e293b; font-size: 14px; }.footer-summary .accent { color: #2563eb; }
.inner-confirm-overlay { position: absolute; inset: 0; z-index: 3; display: flex; align-items: center; justify-content: center; background: rgba(15, 23, 42, .45); }.inner-confirm { width: min(390px, calc(100% - 40px)); padding: 24px; text-align: center; background: #fff; border-radius: 10px; box-shadow: 0 20px 60px rgba(15,23,42,.3); }.confirm-mark { display: flex; align-items: center; justify-content: center; width: 38px; height: 38px; margin: 0 auto 10px; color: #92400e; background: #fef3c7; border-radius: 50%; font-weight: 800; }.inner-confirm h3 { margin: 0 0 8px; font-size: 17px; }.inner-confirm p { margin: 0 0 18px; color: #64748b; font-size: 13px; }.confirm-actions { display: flex; justify-content: center; gap: 10px; }
.stock-in-notice { position: absolute; top: 72px; left: 50%; z-index: 5; display: flex; align-items: center; gap: 8px; transform: translateX(-50%); padding: 10px 16px; color: #166534; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 7px; box-shadow: 0 8px 25px rgba(15,23,42,.14); font-size: 13px; }.notice-error { color: #991b1b; background: #fff1f2; border-color: #fecdd3; }.notice-icon { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; color: #fff; background: #16a34a; border-radius: 50%; font-size: 12px; font-weight: 700; }.notice-error .notice-icon { background: #dc2626; }
@media (max-width: 900px) { .stock-in-modal-overlay { padding: 0; }.stock-in-modal { width: 100vw; max-height: 100vh; height: 100vh; border-radius: 0; }.form-grid-3, .audit-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }.stock-in-footer { align-items: flex-start; flex-direction: column; }.footer-actions { width: 100%; justify-content: flex-end; } }
@media (max-width: 560px) { .stock-in-header, .stock-in-body, .stock-in-footer { padding-left: 14px; padding-right: 14px; }.form-grid-3, .audit-grid { grid-template-columns: 1fr; }.footer-summary { flex-wrap: wrap; }.footer-actions { flex-wrap: wrap; }.footer-actions .btn { flex: 1; } }
</style>
