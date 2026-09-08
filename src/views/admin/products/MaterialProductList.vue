<template>
  <div class="material-product-page">
    <section class="filter-panel">
      <label class="search-field">
        <span class="sr-only">搜索原材料</span>
        <span class="search-icon" aria-hidden="true"></span>
        <input
          v-model.trim="filters.name"
          type="search"
          placeholder="搜索名称、编号或规格"
        />
      </label>

      <span class="filter-label">门店</span>
      <div class="store-tabs">
        <button
          class="store-chip"
          :class="{ active: selectedStoreId === null }"
          type="button"
          @click="selectedStoreId = null"
        >
          全部门店
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
      </div>

      <label class="filter-field">
        <span>分类</span>
        <select v-model="filters.category">
          <option value="">全部分类</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </label>

      <label class="filter-field">
        <span>仓库</span>
        <select v-model="filters.warehouse">
          <option value="">全部仓库</option>
          <option v-for="warehouse in warehouses" :key="warehouse" :value="warehouse">
            {{ warehouse }}
          </option>
        </select>
      </label>

      <label class="filter-field">
        <span>状态</span>
        <select v-model="filters.status">
          <option value="all">全部状态</option>
          <option value="enabled">启用</option>
          <option value="disabled">停用</option>
        </select>
      </label>

      <div class="action-buttons">
        <button class="btn-primary" type="button" @click="handleNew">
          <span aria-hidden="true">＋</span>
          新增原材料
        </button>
        <button
          class="btn-batch-delete"
          :disabled="selectedCount === 0"
          type="button"
          @click="handleBatchDelete"
        >
          批量删除
        </button>
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
              <th class="col-checkbox">
                <input type="checkbox" v-model="selectAll" @change="handleSelectAll" />
              </th>
              <th>原材料</th>
              <th>编号</th>
              <th>规格型号</th>
              <th>单位</th>
              <th>分类</th>
              <th>默认仓库</th>
              <th>门店</th>
              <th>状态</th>
              <th class="actions-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in paginatedProducts" :key="product.id">
              <td class="col-checkbox">
                <input type="checkbox" v-model="product.selected" />
              </td>
              <td>
                <div class="product-cell">
                  <span class="product-mark" aria-hidden="true">{{ getInitial(product.name) }}</span>
                  <div>
                    <strong>{{ product.name }}</strong>
                    <small>{{ product.notes || '暂无备注' }}</small>
                  </div>
                </div>
              </td>
              <td class=”muted”>{{ product.code || '-' }}</td>
              <td>{{ product.specification || '-' }}</td>
              <td>{{ product.unitName || '-' }}</td>
              <td>{{ product.categoryName || '-' }}</td>
              <td>{{ product.warehouseName || '-' }}</td>
              <td>
                <span class=”store-text”>{{ product.storeNames || '全部门店' }}</span>
              </td>
              <td>
                <span class=”status-pill” :class="product.enabled === false ? 'disabled' : 'enabled'">
                  {{ product.enabled === false ? '停用' : '启用' }}
                </span>
              </td>
              <td class=”actions-column”>
                <button class=”table-action edit” type=”button” @click="handleEdit(product)">修改</button>
                <button class=”table-action copy” type=”button” @click="handleCopy(product)">复制</button>
              </td>
            </tr>
            <tr v-if="paginatedProducts.length === 0">
              <td colspan="10" class="empty-state">
                <span class="empty-icon" aria-hidden="true">□</span>
                <strong>暂无原材料商品</strong>
                <span>点击右上角"新增原材料"开始建立档案</span>
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
const allWarehouses = ref([])
const units = ref([])
const selectedStoreId = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const selectAll = ref(false)
const filters = reactive({
  name: '',
  code: '',
  specification: '',
  category: '',
  warehouse: '',
  status: 'all'
})

const warehouseMap = computed(() => new Map(allWarehouses.value.map(item => [item.id, item])))
const unitMap = computed(() => new Map(units.value.map(item => [item.id, item.name])))

// 选中数量
const selectedCount = computed(() => {
  return products.value.filter(p => p.selected).length
})

// 获取所有分类
const categories = computed(() => {
  const cats = new Set()
  decoratedProducts.value.forEach(p => {
    if (p.categoryName) cats.add(p.categoryName)
  })
  return Array.from(cats)
})

// 获取所有仓库名称
const warehouses = computed(() => {
  const whs = new Set()
  decoratedProducts.value.forEach(p => {
    if (p.warehouseName) whs.add(p.warehouseName)
  })
  return Array.from(whs)
})

const decoratedProducts = computed(() => products.value.map(product => {
  const warehouse = warehouseMap.value.get(product.warehouseId)
  const categoryId = product.categoryId || product.category
  const category = warehouse?.categories?.find(item => item.id === categoryId)
  const storeNames = (product.storeIds || [])
    .map(storeId => stores.value.find(store => store.id === storeId)?.name)
    .filter(Boolean)
    .join('、')

  return {
    ...product,
    unitName: unitMap.value.get(product.unitId),
    warehouseName: warehouse?.name,
    categoryName: category?.name,
    storeNames
  }
}))

const filteredProducts = computed(() => decoratedProducts.value.filter(product => {
  const nameMatched = !filters.name
    || product.name?.toLowerCase().includes(filters.name.toLowerCase())
    || product.code?.toLowerCase().includes(filters.name.toLowerCase())
    || product.specification?.toLowerCase().includes(filters.name.toLowerCase())
  const categoryMatched = !filters.category
    || product.categoryName === filters.category
  const warehouseMatched = !filters.warehouse
    || product.warehouseName === filters.warehouse
  const storeMatched = selectedStoreId.value === null
    || product.storeIds?.includes(selectedStoreId.value)
  const statusMatched = filters.status === 'all'
    || (filters.status === 'enabled' && product.enabled !== false)
    || (filters.status === 'disabled' && product.enabled === false)

  return nameMatched && categoryMatched && warehouseMatched && storeMatched && statusMatched
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
  allWarehouses.value = Array.isArray(response) ? response : []
}

const loadUnits = async () => {
  const response = await request({ url: '/products/units/measurements', method: 'GET' })
  units.value = getMeasurementUnits(response)
}

const loadProducts = async () => {
  try {
    const response = await request({ url: '/raw-material-products', method: 'GET' })
    products.value = Array.isArray(response) ? response.map(p => ({ ...p, selected: false })) : []
  } catch (error) {
    console.error('加载原材料商品失败:', error)
    products.value = []
  }
}

const resetFilters = () => {
  filters.name = ''
  filters.category = ''
  filters.warehouse = ''
  filters.status = 'all'
  selectedStoreId.value = null
}

const getInitial = name => (name || '原').slice(0, 1)

const handleSelectAll = () => {
  products.value.forEach(p => {
    p.selected = selectAll.value
  })
}

const handleNew = () => productFormModal.value?.open()
const handleEdit = product => productFormModal.value?.open(product)

const handleBatchDelete = async () => {
  const selectedProducts = products.value.filter(p => p.selected)
  if (selectedProducts.length === 0) {
    return
  }

  if (!window.confirm(`确定要删除选中的 ${selectedProducts.length} 个原材料吗？`)) {
    return
  }

  try {
    const deletePromises = selectedProducts.map(product =>
      request({
        url: `/raw-material-products/${product.id}`,
        method: 'DELETE'
      })
    )

    await Promise.all(deletePromises)
    await loadProducts()
    window.alert('删除成功')
  } catch (error) {
    window.alert(`删除失败：${error.response?.data?.message || error.message}`)
  }
}
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
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-field {
  display: flex;
  align-items: center;
  min-height: 38px;
  max-width: 200px;
  flex: 0 0 200px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  position: relative;
  padding-left: 34px;
}

.search-field input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #1f2937;
  font-size: 14px;
}

.search-icon {
  position: absolute;
  left: 13px;
  width: 13px;
  height: 13px;
  border: 1.8px solid #94a3b8;
  border-radius: 50%;
}

.search-icon::after {
  content: '';
  position: absolute;
  right: -5px;
  bottom: -3px;
  width: 6px;
  height: 1.8px;
  background: #94a3b8;
  transform: rotate(45deg);
}

.filter-label {
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.store-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}

.store-chip {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
  white-space: nowrap;
  user-select: none;
  background: transparent;
  border: 1px solid transparent;
}

.store-chip:hover {
  background: #e5e7eb;
  color: #374151;
}

.store-chip.active {
  background: #34d399;
  color: #fff;
  box-shadow: 0 2px 4px rgba(52, 211, 153, 0.3);
}

.filter-field {
  display: flex;
  align-items: center;
  min-height: 38px;
  padding: 0 12px;
  gap: 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
}

.filter-field span {
  color: #6b7280;
  font-size: 14px;
  white-space: nowrap;
}

.filter-field select {
  border: 0;
  outline: 0;
  color: #1f2937;
  background: transparent;
  font-size: 14px;
  min-width: 100px;
  height: 36px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.btn-primary {
  height: 38px;
  padding: 0 16px;
  background: #10b981;
  color: white;
  border: 1px solid #10b981;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-primary:hover {
  background: #059669;
  border-color: #059669;
}

.btn-batch-delete {
  height: 38px;
  padding: 0 16px;
  background: #ef4444;
  color: white;
  border: 1px solid #ef4444;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-batch-delete:hover:not(:disabled) {
  background: #dc2626;
  border-color: #dc2626;
}

.btn-batch-delete:disabled {
  background: #d1d5db;
  border-color: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
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
  min-width: 1060px;
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
