<template>
  <div class="material-product-page">
    <section class="filter-panel">
      <div class="store-filter">
        <span class="filter-label">门店</span>
        <button
          class="store-chip"
          :class="{ active: selectedStoreId === null }"
          type="button"
          @click="selectedStoreId = null"
        >
          全部
        </button>
        <button
          v-for="store in stores"
          :key="store.id"
          class="store-chip"
          :class="{ active: selectedStoreId === store.id }"
          type="button"
          @click="selectedStoreId = store.id"
        >
          {{ store.name }}
        </button>
        <button class="btn-primary" type="button" @click="handleNew">
          <span aria-hidden="true">＋</span>
          新增原材料
        </button>
      </div>

      <div class="filter-grid">
        <label class="field">
          <span>原材料名称</span>
          <input v-model.trim="filters.name" type="search" placeholder="搜索名称" />
        </label>
        <label class="field">
          <span>编号</span>
          <input v-model.trim="filters.code" type="search" placeholder="搜索编号" />
        </label>
        <label class="field">
          <span>规格型号</span>
          <input v-model.trim="filters.specification" type="search" placeholder="搜索规格" />
        </label>
        <label class="field">
          <span>状态</span>
          <select v-model="filters.status">
            <option value="all">全部状态</option>
            <option value="enabled">启用</option>
            <option value="disabled">停用</option>
          </select>
        </label>
        <button class="btn-secondary" type="button" @click="resetFilters">重置</button>
      </div>
    </section>

    <section class="summary-grid" aria-label="原材料统计">
      <div class="summary-item">
        <span class="summary-label">原材料品种</span>
        <strong>{{ filteredProducts.length }}</strong>
        <span class="summary-note">当前筛选结果</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">启用中</span>
        <strong>{{ enabledCount }}</strong>
        <span class="summary-note">可用于业务录入</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">已停用</span>
        <strong>{{ disabledCount }}</strong>
        <span class="summary-note">仅保留历史记录</span>
      </div>
    </section>

    <section class="table-section">
      <div class="section-toolbar">
        <div>
          <h2>原材料商品信息</h2>
          <span>共 {{ filteredProducts.length }} 条记录</span>
        </div>
        <button class="btn-refresh" type="button" @click="loadProducts">
          <span aria-hidden="true">↻</span>
          刷新
        </button>
      </div>

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>原材料</th>
              <th>编号</th>
              <th>规格型号</th>
              <th>单位</th>
              <th>分类</th>
              <th>默认仓库</th>
              <th>门店</th>
              <th class="stock-column">当前库存</th>
              <th>状态</th>
              <th class="actions-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in paginatedProducts" :key="product.id">
              <td>
                <div class="product-cell">
                  <span class="product-mark" aria-hidden="true">{{ getInitial(product.name) }}</span>
                  <div>
                    <strong>{{ product.name }}</strong>
                    <small>{{ product.notes || '暂无备注' }}</small>
                  </div>
                </div>
              </td>
              <td class="muted">{{ product.code || '-' }}</td>
              <td>{{ product.specification || '-' }}</td>
              <td>{{ product.unitName || '-' }}</td>
              <td>{{ product.categoryName || '-' }}</td>
              <td>{{ product.warehouseName || '-' }}</td>
              <td>
                <span class="store-text">{{ product.storeNames || '全部门店' }}</span>
              </td>
              <td class="stock-column">
                <strong
                  class="stock-value"
                  :title="selectedStoreId === null ? '全部门店库存合计' : '当前门店库存合计'"
                >
                  {{ formatStock(product.currentStock) }}
                </strong>
                <small v-if="product.inventoryUpdatedAt" class="stock-updated">
                  {{ formatStockUpdatedAt(product.inventoryUpdatedAt) }}
                </small>
              </td>
              <td>
                <span class="status-pill" :class="product.enabled === false ? 'disabled' : 'enabled'">
                  {{ product.enabled === false ? '停用' : '启用' }}
                </span>
              </td>
              <td class="actions-column">
                <button class="table-action edit" type="button" @click="handleEdit(product)">修改</button>
                <button class="table-action copy" type="button" @click="handleCopy(product)">复制</button>
                <button class="table-action delete" type="button" @click="handleDelete(product)">删除</button>
              </td>
            </tr>
            <tr v-if="paginatedProducts.length === 0">
              <td colspan="10" class="empty-state">
                <span class="empty-icon" aria-hidden="true">□</span>
                <strong>暂无原材料商品</strong>
                <span>点击右上角“新增原材料”开始建立档案</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
        <div class="pagination-actions">
          <select v-model.number="pageSize" aria-label="每页条数">
            <option :value="10">10 条/页</option>
            <option :value="20">20 条/页</option>
            <option :value="50">50 条/页</option>
          </select>
          <button type="button" :disabled="currentPage <= 1" @click="currentPage -= 1">上一页</button>
          <button type="button" :disabled="currentPage >= totalPages" @click="currentPage += 1">下一页</button>
        </div>
      </div>
    </section>

    <ProductFormModal
      ref="productFormModal"
      mode="raw-material"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import ProductFormModal from '@/components/admin/ProductFormModal.vue'
import request from '@/api/request'
import { getMeasurementUnits } from '@/utils/unitHelper'

const productFormModal = ref(null)
const products = ref([])
const stores = ref([])
const warehouses = ref([])
const units = ref([])
const stockBalances = ref([])
const selectedStoreId = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const filters = reactive({
  name: '',
  code: '',
  specification: '',
  status: 'all'
})

const warehouseMap = computed(() => new Map(warehouses.value.map(item => [item.id, item])))
const unitMap = computed(() => new Map(units.value.map(item => [item.id, item.name])))
const stockBalanceMap = computed(() => {
  const balancesByProduct = new Map()

  stockBalances.value.forEach(balance => {
    if (balance.productType && balance.productType !== 'raw-material') return

    const productKey = String(balance.productId)
    if (!balancesByProduct.has(productKey)) balancesByProduct.set(productKey, [])
    balancesByProduct.get(productKey).push(balance)
  })

  return balancesByProduct
})

const decoratedProducts = computed(() => products.value.map(product => {
  const warehouse = warehouseMap.value.get(product.warehouseId)
  const categoryId = product.categoryId || product.category
  const category = warehouse?.categories?.find(item => item.id === categoryId)
  const productBalances = stockBalanceMap.value.get(String(product.id)) || []
  const visibleBalances = selectedStoreId.value === null
    ? productBalances
    : productBalances.filter(balance => String(balance.storeId) === String(selectedStoreId.value))
  const currentStock = visibleBalances.reduce((sum, balance) => {
    const quantity = Number(balance.quantity)
    return sum + (Number.isFinite(quantity) ? quantity : 0)
  }, 0)
  const inventoryUpdatedAt = visibleBalances.reduce((latest, balance) => {
    const updatedAt = balance.updatedAt || ''
    return updatedAt > latest ? updatedAt : latest
  }, '')
  const storeNames = (product.storeIds || [])
    .map(storeId => stores.value.find(store => store.id === storeId)?.name)
    .filter(Boolean)
    .join('、')

  return {
    ...product,
    unitName: unitMap.value.get(product.unitId),
    warehouseName: warehouse?.name,
    categoryName: category?.name,
    storeNames,
    currentStock,
    inventoryUpdatedAt
  }
}))

const filteredProducts = computed(() => decoratedProducts.value.filter(product => {
  const nameMatched = !filters.name
    || product.name?.toLowerCase().includes(filters.name.toLowerCase())
  const codeMatched = !filters.code
    || product.code?.toLowerCase().includes(filters.code.toLowerCase())
  const specificationMatched = !filters.specification
    || product.specification?.toLowerCase().includes(filters.specification.toLowerCase())
  const storeMatched = selectedStoreId.value === null
    || product.storeIds?.includes(selectedStoreId.value)
  const statusMatched = filters.status === 'all'
    || (filters.status === 'enabled' && product.enabled !== false)
    || (filters.status === 'disabled' && product.enabled === false)

  return nameMatched && codeMatched && specificationMatched && storeMatched && statusMatched
}))

const totalPages = computed(() => Math.max(1, Math.ceil(filteredProducts.value.length / pageSize.value)))
const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredProducts.value.slice(start, start + pageSize.value)
})
const enabledCount = computed(() => filteredProducts.value.filter(item => item.enabled !== false).length)
const disabledCount = computed(() => filteredProducts.value.filter(item => item.enabled === false).length)

watch(
  () => [filters.name, filters.code, filters.specification, filters.status, selectedStoreId.value, pageSize.value],
  () => {
    currentPage.value = 1
  }
)

watch(totalPages, value => {
  if (currentPage.value > value) currentPage.value = value
})

const loadStores = async () => {
  const response = await request({ url: '/stores', method: 'GET' })
  stores.value = Array.isArray(response) ? response : []
}

const loadWarehouses = async () => {
  const response = await request({ url: '/warehouses', method: 'GET' })
  warehouses.value = Array.isArray(response) ? response : []
}

const loadUnits = async () => {
  const response = await request({ url: '/products/units/measurements', method: 'GET' })
  units.value = getMeasurementUnits(response)
}

const loadProducts = async () => {
  try {
    const [productResponse, balanceResponse] = await Promise.all([
      request({ url: '/raw-material-products', method: 'GET' }),
      request({ url: '/stock-balances', method: 'GET', params: { type: 'raw-material' } })
    ])
    products.value = Array.isArray(productResponse) ? productResponse : []
    stockBalances.value = Array.isArray(balanceResponse) ? balanceResponse : []
  } catch (error) {
    console.error('加载原材料商品或库存失败:', error)
    products.value = []
    stockBalances.value = []
  }
}

const resetFilters = () => {
  filters.name = ''
  filters.code = ''
  filters.specification = ''
  filters.status = 'all'
  selectedStoreId.value = null
}

const getInitial = name => (name || '原').slice(0, 1)

const formatStock = value => Number(value || 0).toLocaleString('zh-CN', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 3
})

const formatStockUpdatedAt = value => {
  if (!value) return ''
  return String(value).slice(0, 16)
}

const handleNew = () => productFormModal.value?.open()
const handleEdit = product => productFormModal.value?.open(product)
const handleCopy = product => {
  const { id, ...copy } = product
  productFormModal.value?.open(copy)
}

const handleSave = async () => {
  await loadProducts()
}

const handleDelete = async product => {
  if (!window.confirm(`确定要删除原材料“${product.name}”吗？`)) return

  try {
    await request({
      url: `/raw-material-products/${product.id}`,
      method: 'DELETE'
    })
    await loadProducts()
  } catch (error) {
    window.alert(`删除失败：${error.response?.data?.message || error.message}`)
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadStores(), loadWarehouses(), loadUnits(), loadProducts()])
  } catch (error) {
    console.error('加载原材料页面数据失败:', error)
  }
})
</script>

<style scoped>
.material-product-page {
  padding: 0;
  background: #f5f5f5;
  min-height: 100vh;
}

.filter-panel,
.table-section {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.filter-panel {
  padding: 16px 20px;
}

.store-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding-bottom: 14px;
  border-bottom: 1px solid #edf0f4;
}

.filter-label,
.field span {
  color: #69778a;
  font-size: 14px;
  font-weight: 500;
}

.filter-label {
  margin-right: 4px;
}

.store-chip {
  border: 1px solid #dbe3ec;
  border-radius: 4px;
  padding: 8px 16px;
  color: #69778a;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}

.store-chip.active {
  border-color: #1677ff;
  color: #1677ff;
  background: #eaf3ff;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 38px;
  border-radius: 5px;
  border: 1px solid #1677ff;
  padding: 0 16px;
  background: #1677ff;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  margin-left: auto;
}

.btn-primary:hover {
  background: #0958d9;
  border-color: #0958d9;
}

.btn-secondary,
.btn-refresh,
.pagination button,
.pagination select {
  height: 38px;
  border-radius: 5px;
  border: 1px solid #d8e0e9;
  padding: 0 16px;
  background: #fff;
  color: #526174;
  cursor: pointer;
  font-size: 14px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr)) auto;
  align-items: end;
  gap: 12px;
  padding-top: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field input,
.field select {
  width: 100%;
  height: 38px;
  padding: 0 12px;
  border: 1px solid #d8e0e9;
  border-radius: 5px;
  outline: none;
  color: #263548;
  background: #fff;
  font-size: 14px;
  box-sizing: border-box;
}

.field input:focus,
.field select:focus {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.btn-secondary:hover,
.btn-refresh:hover,
.pagination button:hover:not(:disabled) {
  border-color: #1677ff;
  color: #1677ff;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 14px;
}

.summary-item {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  padding: 18px 22px;
  background: #fff;
  border-bottom: 1px solid #e5eaf0;
}

.summary-label {
  color: #69778a;
  font-size: 14px;
  font-weight: 500;
}

.summary-item strong {
  color: #172033;
  font-size: 28px;
  font-weight: 700;
}

.summary-note {
  grid-column: 1 / -1;
  color: #9aa6b5;
  font-size: 13px;
  margin-top: 6px;
}

.table-section {
  overflow: hidden;
  background: white;
}

h2 {
  margin: 0;
}

.section-toolbar,
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
}

.section-toolbar {
  border-bottom: 1px solid #edf0f4;
}

.section-toolbar h2 {
  font-size: 16px;
  font-weight: 600;
}

.section-toolbar span,
.pagination {
  color: #8a96a6;
  font-size: 13px;
}

.section-toolbar span {
  display: block;
  margin-top: 5px;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1160px;
}

th,
td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #edf0f4;
  white-space: nowrap;
  font-size: 14px;
}

th {
  color: #69778a;
  background: #fafbfd;
  font-size: 14px;
  font-weight: 600;
}

tbody tr:hover {
  background: #f8fbff;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 190px;
}

.product-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 5px;
  background: #e6f4ff;
  color: #1677ff;
  font-weight: 700;
  font-size: 14px;
}

.product-cell strong,
.product-cell small {
  display: block;
}

.product-cell strong {
  color: #253348;
  font-weight: 600;
  font-size: 14px;
}

.product-cell small {
  margin-top: 3px;
  color: #9aa6b5;
  font-size: 13px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.muted,
.store-text {
  color: #748196;
}

.stock-column {
  min-width: 118px;
  text-align: right;
}

.stock-value,
.stock-updated {
  display: block;
  font-variant-numeric: tabular-nums;
}

.stock-value {
  color: #172033;
  font-size: 15px;
  font-weight: 700;
}

.stock-updated {
  margin-top: 3px;
  color: #9aa6b5;
  font-size: 11px;
  font-weight: 400;
}

.status-pill {
  display: inline-flex;
  padding: 5px 11px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.status-pill.enabled {
  color: #147a4b;
  background: #e8f8ef;
}

.status-pill.disabled {
  color: #9a5b13;
  background: #fff3df;
}

.actions-column {
  width: 170px;
  text-align: right;
}

.table-action {
  border: 0;
  background: transparent;
  padding: 5px 6px;
  cursor: pointer;
  font-size: 13px;
}

.table-action.edit {
  color: #1677ff;
}

.table-action.copy {
  color: #6e58c8;
}

.table-action.delete {
  color: #d4380d;
}

.empty-state {
  height: 230px;
  text-align: center;
  color: #9aa6b5;
}

.empty-state > * {
  display: block;
  margin: 6px auto;
}

.empty-state strong {
  color: #526174;
  font-size: 14px;
}

.empty-icon {
  width: 42px;
  height: 42px;
  line-height: 42px;
  border-radius: 50%;
  color: #1677ff;
  background: #eaf3ff;
  font-size: 24px;
}

.pagination {
  border-top: 1px solid #edf0f4;
  background: white;
}

.pagination-actions {
  display: flex;
  gap: 8px;
}

.pagination button:disabled {
  color: #b8c1cc;
  background: #f5f7fa;
  cursor: not-allowed;
}

@media (max-width: 960px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .pagination {
    align-items: flex-start;
    flex-direction: column;
  }

  .store-filter {
    flex-direction: column;
    align-items: flex-start;
  }

  .btn-primary {
    width: 100%;
    justify-content: center;
  }
}
</style>
