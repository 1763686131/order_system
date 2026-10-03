<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="material-edit-overlay"
      role="presentation"
      @click.self="requestClose"
    >
      <section
        class="material-edit-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="materialEditTitle"
        @click.stop
      >
        <form class="material-edit-form" @submit.prevent="submitChanges">
          <div class="top-info-bar">
            <div class="document-title">
              <span class="document-eyebrow">原材料出库</span>
              <h2 id="materialEditTitle">修改</h2>
            </div>

            <div class="header-fields">
              <label class="info-group source-field">
                <span>单据来源</span>
                <input :value="sourceLabel" type="text" readonly />
              </label>
              <label class="info-group">
                <span>门店</span>
                <select
                  v-model="form.storeId"
                  :disabled="!editing || saving"
                  aria-label="门店"
                  @change="syncStore"
                >
                  <option value="">请选择门店</option>
                  <option v-for="store in availableStores" :key="store.id" :value="String(store.id)">
                    {{ store.name }}
                  </option>
                </select>
              </label>
              <label class="info-group">
                <span>出库仓库</span>
                <select
                  v-model="form.warehouseId"
                  :disabled="!editing || saving"
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
              </label>
              <label class="info-group material-source-field">
                <span>触屏原材料</span>
                <div class="product-picker">
                  <input
                    v-model="rawProductQuery"
                    :readonly="!editing || saving"
                    type="text"
                    autocomplete="off"
                    aria-label="触屏原材料"
                    @focus="openPicker('raw-top')"
                    @input="openPicker('raw-top')"
                  />
                  <div v-if="activePicker === 'raw-top' && editing" class="picker-options">
                    <button
                      v-for="product in filteredRawProducts(rawProductQuery)"
                      :key="product.id"
                      type="button"
                      @mousedown.prevent="selectRawProduct(product, 0)"
                    >
                      <strong>{{ product.name }}</strong>
                      <small>{{ product.code || '无编码' }} · {{ product.specification || '无规格' }}</small>
                    </button>
                    <span v-if="filteredRawProducts(rawProductQuery).length === 0" class="picker-empty">
                      没有匹配的原材料
                    </span>
                  </div>
                </div>
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
              <span class="document-status">草稿</span>
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

          <div class="table-state" :class="{ error: optionsError }">
            <span v-if="optionsLoading">正在加载门店、仓库、商品和库存资料...</span>
            <template v-else-if="optionsError">
              <span>{{ optionsError }}</span>
              <button type="button" class="inline-button" @click="loadOptions">重新加载</button>
            </template>
          </div>

          <div v-if="!optionsLoading && !optionsError" class="products-table-wrapper">
            <table class="products-table">
              <colgroup>
                <col style="width: 64px" />
                <col style="width: 48px" />
                <col style="width: 235px" />
                <col style="width: 90px" />
                <col style="width: 180px" />
                <col style="width: 170px" />
                <col style="width: 125px" />
                <col style="width: 115px" />
                <col style="width: 220px" />
                <col style="width: 180px" />
                <col style="width: 115px" />
                <col style="width: 250px" />
              </colgroup>
              <thead>
                <tr>
                  <th>操作</th>
                  <th>序号</th>
                  <th>原材料</th>
                  <th>编码</th>
                  <th>规格 / 单位</th>
                  <th>出库仓库</th>
                  <th>仓库原材料数量</th>
                  <th>出库数量</th>
                  <th>成品商品</th>
                  <th>入库仓库</th>
                  <th>入库数量</th>
                  <th>备注信息</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in rows" :key="row.id" class="data-row">
                  <td class="row-actions-cell">
                    <button
                      type="button"
                      class="row-action add"
                      title="增加栏目"
                      :disabled="!editing || saving"
                      @click="addRow"
                    >
                      +
                    </button>
                    <button
                      type="button"
                      class="row-action delete"
                      title="删除栏目"
                      :disabled="!editing || saving || rows.length <= 1"
                      @click="removeRow(index)"
                    >
                      ×
                    </button>
                  </td>
                  <td class="center">{{ index + 1 }}</td>
                  <td>
                    <div class="product-picker">
                      <input
                        v-model="row.productQuery"
                        class="table-input"
                        :class="{ invalid: rowErrors[index]?.productId }"
                        :readonly="!editing || saving"
                        type="text"
                        autocomplete="off"
                        aria-label="原材料商品"
                        @focus="openPicker(`raw-${index}`)"
                        @input="openPicker(`raw-${index}`)"
                      />
                      <div v-if="activePicker === `raw-${index}` && editing" class="picker-options">
                        <button
                          v-for="product in filteredRawProducts(row.productQuery)"
                          :key="product.id"
                          type="button"
                          @mousedown.prevent="selectRawProduct(product, index)"
                        >
                          <strong>{{ product.name }}</strong>
                          <small>{{ product.code || '无编码' }} · {{ product.specification || '无规格' }}</small>
                        </button>
                        <span v-if="filteredRawProducts(row.productQuery).length === 0" class="picker-empty">
                          没有匹配的原材料
                        </span>
                      </div>
                    </div>
                    <small v-if="rowErrors[index]?.productId" class="cell-error">
                      {{ rowErrors[index].productId }}
                    </small>
                  </td>
                  <td>
                    <input :value="row.productCode || '-'" type="text" readonly aria-label="原材料编码" />
                  </td>
                  <td>
                    <div class="combined-spec">{{ row.specification || '-' }}</div>
                    <small class="cell-subtext">{{ row.unit || '-' }}</small>
                  </td>
                  <td>
                    <select
                      v-model="form.warehouseId"
                      class="table-input"
                      :disabled="!editing || saving"
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
                    <small v-if="rowErrors[index]?.warehouseId" class="cell-error">
                      {{ rowErrors[index].warehouseId }}
                    </small>
                  </td>
                  <td class="right">
                    <input :value="formatNumber(row.currentStock)" type="text" readonly aria-label="仓库原材料数量" />
                  </td>
                  <td class="right">
                    <input
                      v-model="row.quantity"
                      class="table-input number-input"
                      :class="{ invalid: rowErrors[index]?.quantity }"
                      :readonly="!editing || saving"
                      type="number"
                      min="0"
                      step="0.0001"
                      placeholder="出库数量"
                      aria-label="出库数量"
                    />
                    <small v-if="rowErrors[index]?.quantity" class="cell-error">
                      {{ rowErrors[index].quantity }}
                    </small>
                  </td>
                  <template v-if="index === 0">
                    <td>
                      <div class="product-picker">
                        <input
                          v-model="finishedProductQuery"
                          class="table-input"
                          :class="{ invalid: errors.finishedProductId }"
                          :readonly="!editing || saving"
                          type="text"
                          autocomplete="off"
                          aria-label="成品商品"
                          @focus="openPicker('finished')"
                          @input="openPicker('finished')"
                        />
                        <div v-if="activePicker === 'finished' && editing" class="picker-options">
                          <button
                            v-for="product in filteredFinishedProducts(finishedProductQuery)"
                            :key="product.id"
                            type="button"
                            @mousedown.prevent="selectFinishedProduct(product)"
                          >
                            <strong>{{ product.name }}</strong>
                            <small>{{ product.code || '无编码' }} · {{ product.specification || '无规格' }}</small>
                          </button>
                          <span v-if="filteredFinishedProducts(finishedProductQuery).length === 0" class="picker-empty">
                            没有匹配的成品商品
                          </span>
                        </div>
                      </div>
                      <small class="cell-subtext">
                        {{ finishedProduct?.specification || finishedProduct?.unit || '-' }}
                      </small>
                      <small v-if="errors.finishedProductId" class="cell-error">{{ errors.finishedProductId }}</small>
                    </td>
                    <td>
                      <select
                        v-model="form.finishedWarehouseId"
                        class="table-input"
                        :class="{ invalid: errors.finishedWarehouseId }"
                        :disabled="!editing || saving"
                        aria-label="入库仓库"
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
                    <td class="right">
                      <input
                        v-model="form.finishedQuantity"
                        class="table-input number-input"
                        :class="{ invalid: errors.finishedQuantity }"
                        :readonly="!editing || saving"
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
                  </template>
                  <template v-else>
                    <td colspan="3" class="shared-finished-cell">成品入库信息见第 1 行</td>
                  </template>
                  <td>
                    <input
                      v-model.trim="row.remark"
                      class="table-input"
                      :readonly="!editing || saving"
                      type="text"
                      maxlength="200"
                      placeholder="默认继承触屏备注"
                      aria-label="备注信息"
                    />
                  </td>
                </tr>
                <tr class="total-row">
                  <td colspan="6" class="center">合计</td>
                  <td class="right">-</td>
                  <td class="right">{{ formatNumber(totalQuantity) }}</td>
                  <td></td>
                  <td></td>
                  <td class="right">{{ formatNumber(form.finishedQuantity || 0) }}</td>
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
                <input :value="primaryRemark || '-'" type="text" readonly />
              </label>
              <label class="info-group">
                <span>修改人</span>
                <input :value="currentUserName" type="text" readonly />
              </label>
              <label class="info-group">
                <span>单据状态</span>
                <input value="草稿，待审核" type="text" readonly />
              </label>
            </div>
            <div class="finance-row">
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
import { useUserStore } from '@/stores/user'

const props = defineProps({
  visible: { type: Boolean, default: false },
  record: { type: Object, default: null }
})

const emit = defineEmits(['close', 'updated'])
const userStore = useUserStore()
const minVisibleRows = 5

const stores = ref([])
const warehouses = ref([])
const rawProducts = ref([])
const finishedProducts = ref([])
const stockBalances = ref([])
const units = ref([])
const allowedProductIds = ref([])
const rows = ref([])
const activePicker = ref('')
const rawProductQuery = ref('')
const finishedProductQuery = ref('')
const optionsLoading = ref(false)
const optionsError = ref('')
const optionsLoaded = ref(false)
const saving = ref(false)
const editing = ref(false)
const formError = ref('')
const initializedRecordId = ref(null)

const form = reactive({
  storeId: '',
  warehouseId: '',
  warehouseName: '',
  documentDate: '',
  finishedProductId: '',
  finishedWarehouseId: '',
  finishedQuantity: '',
  finishedRemark: ''
})

const errors = reactive({
  documentDate: '',
  finishedProductId: '',
  finishedWarehouseId: '',
  finishedQuantity: ''
})
const rowErrors = ref([])

const currentUserName = computed(() => userStore.name || userStore.username || '当前操作员')
const sourceLabel = computed(() => props.record?.source === 'touch'
  ? '触屏端辅助输入'
  : (props.record?.source || '-'))
const filledRows = computed(() => rows.value.filter(row => (
  row.productId
  || row.productQuery
  || row.quantity !== ''
  || row.remark
)))
const primaryRemark = computed(() => filledRows.value[0]?.remark || form.finishedRemark || '')
const totalQuantity = computed(() => rows.value.reduce(
  (sum, row) => sum + Number(row.quantity || 0),
  0
))
const availableStores = computed(() => stores.value.filter(item => item.status !== 'inactive'))
const availableWarehouses = computed(() => warehouses.value.filter(item => {
  if (item.status === 'inactive') return false
  return !form.storeId
    || !item.storeId
    || String(item.storeId) === String(form.storeId)
}))
const finishedProduct = computed(() => finishedProducts.value.find(
  item => String(item.id) === String(form.finishedProductId)
) || null)

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

const productUnit = product => product?.unit
  || product?.unitName
  || units.value.find(unit => String(unit.id) === String(product?.unitId ?? product?.unit_id))?.name
  || ''

const makeRow = item => ({
  id: `row-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  productId: item?.productId ? String(item.productId) : '',
  productQuery: item?.productName || '',
  productCode: item?.productCode || '',
  productName: item?.productName || '',
  specification: item?.specification || '',
  unit: item?.unit || '',
  warehouseId: form.warehouseId,
  quantity: item?.quantity != null ? String(item.quantity) : '',
  currentStock: 0,
  remark: item ? (item.remark || props.record?.remark || '') : ''
})

const ensureMinimumRows = () => {
  while (rows.value.length < minVisibleRows) {
    rows.value.push(makeRow())
  }
}

const clearErrors = () => {
  errors.documentDate = ''
  errors.finishedProductId = ''
  errors.finishedWarehouseId = ''
  errors.finishedQuantity = ''
  rowErrors.value = []
  formError.value = ''
}

const resetForm = () => {
  clearErrors()
  editing.value = false
  form.storeId = props.record?.storeId ? String(props.record.storeId) : ''
  form.warehouseId = props.record?.warehouseId ? String(props.record.warehouseId) : ''
  form.warehouseName = props.record?.warehouseName || ''
  form.documentDate = props.record?.documentDate || ''
  form.finishedProductId = props.record?.finishedProductId
    ? String(props.record.finishedProductId)
    : ''
  form.finishedWarehouseId = props.record?.finishedWarehouseId
    ? String(props.record.finishedWarehouseId)
    : ''
  form.finishedQuantity = Number(props.record?.producedQuantity || 0) > 0
    ? String(props.record.producedQuantity)
    : ''
  form.finishedRemark = props.record?.finishedRemark || props.record?.remark || ''
  const sourceRows = Array.isArray(props.record?.items) && props.record.items.length
    ? props.record.items
    : [props.record?.primaryItem]
  rows.value = sourceRows.filter(Boolean).map(makeRow)
  if (rows.value.length === 0) rows.value = [makeRow()]
  ensureMinimumRows()
  rawProductQuery.value = rows.value[0]?.productQuery || ''
  finishedProductQuery.value = props.record?.finishedProductName || ''
}

const filteredRawProducts = query => {
  const text = String(query || '').trim().toLowerCase()
  return rawProducts.value.filter(product => {
    if (product.enabled === false) return false
    if (
      allowedProductIds.value.length
      && !allowedProductIds.value.some(id => String(id) === String(product.id))
    ) {
      return false
    }
    const storeIds = parseIds(product.storeIds ?? product.store_ids)
    if (storeIds.length && form.storeId && !storeIds.some(id => String(id) === String(form.storeId))) {
      return false
    }
    if (!text) return true
    return [product.name, product.code, product.specification]
      .some(value => String(value || '').toLowerCase().includes(text))
  })
}

const filteredFinishedProducts = query => {
  const text = String(query || '').trim().toLowerCase()
  return finishedProducts.value.filter(product => {
    if (product.enabled === false) return false
    const storeIds = parseIds(product.storeIds ?? product.store_ids)
    if (storeIds.length && form.storeId && !storeIds.some(id => String(id) === String(form.storeId))) {
      return false
    }
    const warehouseId = product.warehouseId ?? product.warehouse_id
    if (warehouseId && form.finishedWarehouseId && String(warehouseId) !== String(form.finishedWarehouseId)) {
      return false
    }
    if (!text) return true
    return [product.name, product.code, product.specification]
      .some(value => String(value || '').toLowerCase().includes(text))
  })
}

const stockFor = (productId, warehouseId, storeId) => stockBalances.value
  .filter(item => (
    String(item.productId) === String(productId)
    && String(item.warehouseId) === String(warehouseId)
    && String(item.storeId) === String(storeId)
  ))
  .reduce((sum, item) => sum + Number(item.quantity || 0), 0)

const refreshRowStock = row => {
  row.currentStock = row.productId
    ? stockFor(row.productId, form.warehouseId, form.storeId)
    : 0
  row.warehouseId = form.warehouseId
}

const refreshAllStock = () => rows.value.forEach(refreshRowStock)

const loadOptions = async () => {
  optionsLoading.value = true
  optionsError.value = ''
  optionsLoaded.value = false
  try {
    const results = await Promise.all([
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: '/material-outbound-settings', method: 'GET' }),
      request({ url: '/products', method: 'GET' }),
      request({ url: '/stock-balances', method: 'GET', params: { type: 'raw-material' } }),
      request({ url: '/products/units/measurements', method: 'GET' })
    ])
    stores.value = Array.isArray(results[0]) ? results[0] : []
    warehouses.value = Array.isArray(results[1]) ? results[1] : []
    const settings = results[2] || {}
    allowedProductIds.value = parseIds(settings.allowedProductIds)
    rawProducts.value = Array.isArray(settings.products)
      ? settings.products
      : (Array.isArray(settings.allowedProducts) ? settings.allowedProducts : [])
    finishedProducts.value = Array.isArray(results[3]) ? results[3] : []
    stockBalances.value = Array.isArray(results[4]) ? results[4] : []
    units.value = Array.isArray(results[5]) ? results[5] : (results[5]?.measurements || [])
    const currentRaw = props.record?.primaryItem
    if (
      currentRaw?.productId
      && !rawProducts.value.some(item => String(item.id) === String(currentRaw.productId))
    ) {
      rawProducts.value.push({
        id: currentRaw.productId,
        code: currentRaw.productCode || '',
        name: currentRaw.productName || '',
        specification: currentRaw.specification || '',
        unit: currentRaw.unit || '',
        enabled: true
      })
    }
    optionsLoaded.value = true
    rows.value.forEach(row => {
      const product = rawProducts.value.find(item => String(item.id) === String(row.productId))
      if (product) {
        row.productName = product.name || ''
        row.productQuery = product.name || ''
        row.productCode = product.code || ''
        row.specification = product.specification || ''
        row.unit = productUnit(product)
      }
    })
    refreshAllStock()
  } catch (error) {
    optionsError.value = error?.response?.data?.message || '基础资料和库存加载失败。'
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

const openPicker = key => {
  if (editing.value) activePicker.value = key
}

const selectRawProduct = (product, index) => {
  const row = rows.value[index] || rows.value[0]
  if (!row) return
  row.productId = String(product.id)
  row.productQuery = product.name || ''
  row.productName = product.name || ''
  row.productCode = product.code || ''
  row.specification = product.specification || ''
  row.unit = productUnit(product)
  refreshRowStock(row)
  if (index === 0) rawProductQuery.value = row.productQuery
  activePicker.value = ''
}

const selectFinishedProduct = product => {
  form.finishedProductId = String(product.id)
  finishedProductQuery.value = product.name || ''
  activePicker.value = ''
  errors.finishedProductId = ''
}

const syncStore = () => {
  const warehouseValid = availableWarehouses.value.some(
    item => String(item.id) === String(form.warehouseId)
  )
  if (!warehouseValid) {
    form.warehouseId = ''
    form.warehouseName = ''
  }
  refreshAllStock()
}

const syncWarehouse = () => {
  const warehouse = availableWarehouses.value.find(
    item => String(item.id) === String(form.warehouseId)
  )
  form.warehouseName = warehouse?.name || ''
  refreshAllStock()
}

const addRow = () => {
  rows.value.push(makeRow())
}

const removeRow = index => {
  if (rows.value.length <= 1) return
  rows.value.splice(index, 1)
  ensureMinimumRows()
  if (index === 0) {
    rawProductQuery.value = rows.value[0]?.productQuery || ''
  }
  refreshAllStock()
}

const cancelEditing = () => {
  if (!saving.value) resetForm()
}

const startEditing = () => {
  clearErrors()
  editing.value = true
}

const validate = () => {
  clearErrors()
  let valid = true
  const activeRows = rows.value.filter(row => (
    row.productId
    || row.productQuery
    || row.quantity !== ''
    || row.remark
  ))
  if (!form.storeId) {
    formError.value = '请选择门店。'
    valid = false
  }
  if (!form.documentDate || !/^\d{4}-\d{2}-\d{2}$/.test(form.documentDate)) {
    errors.documentDate = '请选择有效的单据日期。'
    valid = false
  }
  if (!form.warehouseId) {
    formError.value = formError.value || '请选择出库仓库。'
    valid = false
  }
  if (!activeRows.length) {
    formError.value = formError.value || '至少保留一条原材料明细。'
    valid = false
  }
  const requestedByStock = new Map()
  rowErrors.value = rows.value.map(() => ({}))
  activeRows.forEach(row => {
    const index = rows.value.indexOf(row)
    const rowError = {}
    if (!row.productId) {
      rowError.productId = '请选择原材料'
      valid = false
    }
    if (!form.warehouseId) {
      rowError.warehouseId = '请选择仓库'
      valid = false
    }
    const quantity = Number(row.quantity)
    const key = `${row.productId}:${form.warehouseId}`
    requestedByStock.set(key, (requestedByStock.get(key) || 0) + (Number.isFinite(quantity) ? quantity : 0))
    if (!Number.isFinite(quantity) || quantity <= 0) {
      rowError.quantity = '数量必须大于 0'
      valid = false
    }
    rowErrors.value[index] = rowError
  })
  activeRows.forEach(row => {
    const index = rows.value.indexOf(row)
    const key = `${row.productId}:${form.warehouseId}`
    if (
      row.productId
      && requestedByStock.get(key) > Number(row.currentStock || 0) + 0.0000001
    ) {
      rowErrors.value[index].quantity = `不能超过库存 ${formatNumber(row.currentStock)}`
      valid = false
    }
  })
  if (!form.finishedProductId) {
    errors.finishedProductId = '请选择成品商品。'
    valid = false
  }
  if (!form.finishedWarehouseId) {
    errors.finishedWarehouseId = '请选择入库仓库。'
    valid = false
  }
  const finishedQuantity = Number(form.finishedQuantity)
  if (!Number.isFinite(finishedQuantity) || finishedQuantity <= 0) {
    errors.finishedQuantity = '入库数量必须大于 0。'
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
        storeId: Number(form.storeId),
        warehouseId: Number(form.warehouseId),
        quantity: Number(rows.value[0]?.quantity || 0),
        productId: Number(rows.value[0]?.productId || 0),
        remark: primaryRemark.value,
        items: rows.value.filter(row => (
          row.productId
          || row.productQuery
          || row.quantity !== ''
          || row.remark
        )).map(row => ({
          productId: Number(row.productId),
          quantity: Number(row.quantity),
          remark: row.remark || primaryRemark.value
        })),
        finishedProductId: Number(form.finishedProductId),
        finishedWarehouseId: Number(form.finishedWarehouseId),
        finishedQuantity: Number(form.finishedQuantity),
        finishedRemark: primaryRemark.value
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
      activePicker.value = ''
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
.material-edit-overlay {
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
  background: rgba(15, 23, 42, .52);
  font-size: 13px;
}

.material-edit-modal,
.material-edit-modal * {
  box-sizing: border-box;
  letter-spacing: 0;
}

.material-edit-modal {
  display: flex;
  width: min(1780px, calc(100vw - 24px));
  max-height: calc(100vh - 24px);
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  box-shadow: 0 18px 54px rgba(23, 33, 43, .24);
}

.material-edit-form {
  display: flex;
  min-height: 0;
  flex-direction: column;
  overflow: auto;
  background: #fff;
}

.top-info-bar,
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
  flex: 1 1 980px;
  flex-wrap: wrap;
  align-items: center;
  gap: 9px 12px;
  min-width: 0;
}

.info-group {
  position: relative;
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
}

.info-group > span {
  flex: none;
  color: #46535f;
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

.info-group input[readonly],
.info-group input:disabled {
  color: #64717c;
  background: #f8fafb;
}

.info-group input:focus,
.info-group select:focus,
.table-input:focus,
.product-picker input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(21, 154, 124, .12);
}

.info-group input.invalid,
.table-input.invalid {
  border-color: #d64550;
  background: #fff6f6;
}

.source-field input {
  width: 150px;
}

.material-source-field {
  flex: 1 1 230px;
}

.material-source-field .product-picker {
  width: 190px;
}

.date-field input {
  width: 132px;
}

.document-no-field input {
  width: 154px;
}

.top-error {
  position: absolute;
  top: calc(100% + 1px);
  left: 58px;
  color: #b5363e;
  font-size: 11px;
  white-space: nowrap;
}

.toolbar-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 9px;
  margin-left: auto;
}

.document-status {
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

.close-button:disabled,
.edit-button:disabled,
.row-action:disabled,
button:disabled {
  cursor: default;
  opacity: .55;
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
  min-width: 1720px;
  table-layout: fixed;
  border-collapse: collapse;
}

.products-table th,
.products-table td {
  height: 44px;
  padding: 4px 7px;
  overflow: visible;
  border-right: 1px solid #eef1f3;
  border-bottom: 1px solid #e9eef1;
}

.products-table th {
  height: 48px;
  padding: 8px 7px;
}

.products-table tbody tr.data-row td {
  height: 64px;
  padding: 8px 7px;
  vertical-align: middle;
}

.products-table tbody tr.data-row td input,
.products-table tbody tr.data-row td select {
  height: 40px;
}

.products-table tbody tr.data-row .row-action {
  width: 30px;
  height: 30px;
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

.products-table td input[readonly],
.products-table td input:disabled {
  color: #46535f;
  background: #f8fafb;
}

.table-input {
  background: #fff !important;
  border-color: var(--border-strong) !important;
}

.table-input:disabled {
  color: #87939b;
  background: #f8fafb !important;
}

.product-picker {
  position: relative;
  min-width: 0;
}

.product-picker > input {
  width: 100%;
}

.picker-options {
  position: absolute;
  top: calc(100% + 3px);
  left: 0;
  z-index: 20;
  width: min(290px, 32vw);
  max-height: 230px;
  overflow-y: auto;
  padding: 4px;
  background: #fff;
  border: 1px solid #cbd8d5;
  border-radius: 4px;
  box-shadow: 0 12px 26px rgba(23, 33, 43, .17);
}

.picker-options button {
  display: flex;
  width: 100%;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 8px;
  color: var(--text);
  background: #fff;
  border: 0;
  border-radius: 3px;
  cursor: pointer;
  text-align: left;
}

.picker-options button:hover {
  background: #eef8f5;
}

.picker-options button small,
.picker-empty {
  color: #7b8892;
  font-size: 11px;
}

.picker-empty {
  display: block;
  padding: 10px 8px;
}

.row-actions-cell {
  text-align: center;
  white-space: nowrap;
}

.row-action {
  display: inline-flex;
  width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: transparent;
  border: 0;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.row-action.add {
  color: #08755e;
}

.row-action.delete {
  color: #d64550;
}

.combined-spec {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shared-finished-cell {
  color: #87939b !important;
  background: #f8fafb !important;
  text-align: center;
  white-space: nowrap;
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

.right {
  text-align: right !important;
  font-variant-numeric: tabular-nums;
}

.center {
  text-align: center !important;
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
  justify-content: flex-end;
  gap: 9px;
  background: #fbfcfc;
}

.edit-button {
  min-height: 38px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
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
}

@media (max-width: 720px) {
  .material-edit-overlay {
    padding: 5px;
  }

  .material-edit-modal {
    width: calc(100vw - 10px);
    max-height: calc(100vh - 10px);
  }

  .top-info-bar,
  .finance-row-full,
  .finance-row {
    gap: 9px;
    padding: 9px;
  }

  .document-title {
    width: 100%;
  }

  .header-fields {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .header-fields .info-group,
  .finance-row-full .info-group {
    width: 100%;
  }

  .info-group input,
  .info-group select,
  .material-source-field .product-picker,
  .date-field input,
  .document-no-field input,
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
  }

  .finance-row .edit-button {
    width: 100%;
  }
}
</style>
