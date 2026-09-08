<template>
  <div class="material-product-page">
    <section class="page-heading">
      <div>
        <div class="breadcrumb">商品管理 / 原材料列表</div>
        <h1>原材料列表</h1>
        <p>维护树脂、助剂、填料等原材料的商品档案。</p>
      </div>
      <button class="btn-primary" type="button" @click="handleNew">
        <span aria-hidden="true">＋</span>
        新增原材料
      </button>
    </section>

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
              <td colspan="9" class="empty-state">
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
    const response = await request({ url: '/raw-material-products', method: 'GET' })
    products.value = Array.isArray(response) ? response : []
  } catch (error) {
    console.error('加载原材料商品失败:', error)
    products.value = []
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
  min-height: 100%;
  color: #172033;
}

.page-heading,
.filter-panel,
.table-section {
  background: #fff;
  border: 1px solid #e5eaf0;
  border-radius: 8px;
}

.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 24px;
  margin-bottom: 14px;
}

.breadcrumb {
  color: #7b8798;
  font-size: 12px;
  margin-bottom: 8px;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  font-size: 24px;
  letter-spacing: 0;
}

.page-heading p {
  margin-top: 8px;
  color: #7b8798;
  font-size: 13px;
}

.btn-primary,
.btn-secondary,
.btn-refresh,
.pagination button,
.pagination select {
  height: 34px;
  border-radius: 5px;
  border: 1px solid #d8e0e9;
  padding: 0 13px;
  background: #fff;
  color: #526174;
  cursor: pointer;
  font-size: 13px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #1677ff;
  border-color: #1677ff;
  color: #fff;
  font-weight: 600;
}

.btn-primary:hover {
  background: #0958d9;
}

.filter-panel {
  padding: 16px 20px;
  margin-bottom: 14px;
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
  font-size: 12px;
}

.filter-label {
  margin-right: 4px;
}

.store-chip {
  border: 1px solid #dbe3ec;
  border-radius: 4px;
  padding: 6px 13px;
  color: #69778a;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
}

.store-chip.active {
  border-color: #1677ff;
  color: #1677ff;
  background: #eaf3ff;
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
  height: 34px;
  padding: 0 10px;
  border: 1px solid #d8e0e9;
  border-radius: 5px;
  outline: none;
  color: #263548;
  background: #fff;
  font-size: 13px;
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
  padding: 16px 20px;
  background: #fff;
  border: 1px solid #e5eaf0;
  border-radius: 8px;
}

.summary-label {
  color: #69778a;
  font-size: 12px;
}

.summary-item strong {
  color: #172033;
  font-size: 26px;
  font-weight: 700;
}

.summary-note {
  grid-column: 1 / -1;
  color: #9aa6b5;
  font-size: 11px;
  margin-top: 5px;
}

.table-section {
  overflow: hidden;
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
}

.section-toolbar span,
.pagination {
  color: #8a96a6;
  font-size: 12px;
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
  padding: 13px 16px;
  text-align: left;
  border-bottom: 1px solid #edf0f4;
  white-space: nowrap;
  font-size: 13px;
}

th {
  color: #69778a;
  background: #fafbfd;
  font-size: 12px;
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
  width: 30px;
  height: 30px;
  border-radius: 5px;
  background: #e6f4ff;
  color: #1677ff;
  font-weight: 700;
}

.product-cell strong,
.product-cell small {
  display: block;
}

.product-cell strong {
  color: #253348;
  font-weight: 600;
}

.product-cell small {
  margin-top: 3px;
  color: #9aa6b5;
  font-size: 11px;
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
  padding: 4px 9px;
  border-radius: 12px;
  font-size: 11px;
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
  padding: 4px 5px;
  cursor: pointer;
  font-size: 12px;
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
}

.empty-icon {
  width: 38px;
  height: 38px;
  line-height: 38px;
  border-radius: 50%;
  color: #1677ff;
  background: #eaf3ff;
  font-size: 22px;
}

.pagination {
  border-top: 1px solid #edf0f4;
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
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .pagination {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
