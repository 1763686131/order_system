<template>
  <div class="material-inventory-page">
    <section class="filter-panel">
      <div class="filter-row">
        <label class="search-field">
          <span class="sr-only">搜索原材料</span>
          <span class="search-icon" aria-hidden="true"></span>
          <input
            v-model.trim="filters.keyword"
            type="search"
            placeholder="搜索名称、编号或规格"
          />
        </label>

        <span class="filter-label">门店</span>
        <div class="store-tabs">
          <button
            type="button"
            :class="{ active: filters.storeId === null }"
            @click="filters.storeId = null"
          >
            全部门店
          </button>
          <button
            v-for="store in stores"
            :key="store.id"
            type="button"
            :class="{ active: filters.storeId === store.id }"
            @click="filters.storeId = store.id"
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

        <div class="status-filter" aria-label="库存状态">
          <span class="filter-label">库存状态</span>
          <div class="status-tabs">
            <button
              v-for="status in statusOptions"
              :key="status.value"
              type="button"
              :class="{ active: filters.status === status.value }"
              @click="filters.status = status.value"
            >
              {{ status.label }}
            </button>
          </div>
        </div>

        <div class="header-actions">
          <button class="btn btn-secondary" type="button" @click="resetFilters">
            重置筛选
          </button>
          <button class="btn btn-secondary" type="button" @click="exportInventory">
            <span class="button-icon" aria-hidden="true">↓</span>
            导出
          </button>
          <button class="btn btn-primary" type="button" @click="openStockInModal()">
            <span class="button-icon" aria-hidden="true">+</span>
            入库
          </button>
        </div>
      </div>
    </section>

    <section class="stats-grid" aria-label="库存概览">
      <article class="stat-card">
        <div class="stat-heading">
          <span>材料品种</span>
          <span class="stat-mark mark-blue">品</span>
        </div>
        <strong>{{ overview.totalTypes }}</strong>
        <small>当前筛选范围内</small>
      </article>
      <article class="stat-card">
        <div class="stat-heading">
          <span>库存总量</span>
          <span class="stat-mark mark-green">量</span>
        </div>
        <strong>{{ formatNumber(overview.totalStock) }}</strong>
        <small>按各自计量单位统计</small>
      </article>
      <article class="stat-card">
        <div class="stat-heading">
          <span>库存预警</span>
          <span class="stat-mark mark-orange">警</span>
        </div>
        <strong>{{ overview.warningCount }}</strong>
        <small>低于最低库存或暂无库存</small>
      </article>
      <article class="stat-card">
        <div class="stat-heading">
          <span>库存金额</span>
          <span class="stat-mark mark-purple">额</span>
        </div>
        <strong>¥{{ formatNumber(overview.totalValue, 2) }}</strong>
        <small>按参考成本价估算</small>
      </article>
    </section>

    <section class="table-panel">
      <div class="table-toolbar">
        <div>
          <h2>原材料明细</h2>
          <span>最后刷新：{{ lastRefreshed }}</span>
        </div>
        <button class="refresh-button" type="button" title="刷新" @click="refreshData">
          <span aria-hidden="true">↻</span>
          刷新
        </button>
      </div>

      <div class="table-scroll">
        <table class="inventory-table">
          <thead>
            <tr>
              <th>编号</th>
              <th class="sortable" @click="sortBy('name')">
                原材料
                <span :class="['sort-indicator', { active: sortKey === 'name' }]">
                  {{ getSortIndicator('name') }}
                </span>
              </th>
              <th>分类</th>
              <th>规格 / 型号</th>
              <th>仓库</th>
              <th class="sortable number-column" @click="sortBy('stock')">
                当前库存
                <span :class="['sort-indicator', { active: sortKey === 'stock' }]">
                  {{ getSortIndicator('stock') }}
                </span>
              </th>
              <th>单位</th>
              <th class="number-column">安全库存</th>
              <th>库存状态</th>
              <th class="sortable" @click="sortBy('updatedAt')">
                更新时间
                <span :class="['sort-indicator', { active: sortKey === 'updatedAt' }]">
                  {{ getSortIndicator('updatedAt') }}
                </span>
              </th>
              <th class="actions-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="material in paginatedMaterials" :key="material.id">
              <td class="code-cell">{{ material.code }}</td>
              <td>
                <div class="material-name">
                  <strong>{{ material.name }}</strong>
                  <small>{{ material.storeName }}</small>
                </div>
              </td>
              <td>
                <span class="category-tag">{{ material.category }}</span>
              </td>
              <td class="muted-cell">{{ material.specification || '-' }}</td>
              <td>{{ material.warehouse }}</td>
              <td class="number-column">
                <strong :class="['stock-number', getStatusClass(material)]">
                  {{ formatNumber(material.stock) }}
                </strong>
              </td>
              <td>{{ material.unit }}</td>
              <td class="number-column">
                <span>{{ formatNumber(material.minStock) }}</span>
                <small class="max-stock"> / {{ formatNumber(material.maxStock) }}</small>
              </td>
              <td>
                <span :class="['status-badge', getStatusClass(material)]">
                  <span class="status-dot"></span>
                  {{ getStatusText(material) }}
                </span>
              </td>
              <td class="muted-cell">{{ material.updatedAt }}</td>
              <td class="actions-column">
                <button class="table-action" type="button" @click="openStockInModal(material)">
                  入库
                </button>
              </td>
            </tr>
            <tr v-if="paginatedMaterials.length === 0">
              <td colspan="11" class="empty-state">
                <div class="empty-title">没有匹配的原材料</div>
                <p>可以尝试清空筛选条件后重新查看。</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="table-footer">
        <span>显示 {{ paginationStart }}-{{ paginationEnd }}，共 {{ filteredMaterials.length }} 条</span>
        <div class="pagination">
          <select v-model.number="pageSize" aria-label="每页条数">
            <option :value="8">8 条 / 页</option>
            <option :value="15">15 条 / 页</option>
            <option :value="30">30 条 / 页</option>
          </select>
          <button type="button" :disabled="currentPage === 1" @click="currentPage--">上一页</button>
          <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button type="button" :disabled="currentPage >= totalPages" @click="currentPage++">
            下一页
          </button>
        </div>
      </footer>
    </section>

    <StockInOrderModal ref="stockInModalRef" @saved="handleStockInSaved" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import request from '@/api/request'
import { getMeasurementUnits } from '@/utils/unitHelper'
import StockInOrderModal from '@/components/common/StockInOrderModal.vue'

const stores = ref([
  { id: 1, name: '绝缘门店' },
  { id: 2, name: '中固门店' }
])
const allWarehouses = ref([])
const units = ref([])

const materials = ref([
  {
    id: 1,
    code: 'RM-001',
    name: '环氧树脂',
    category: '树脂',
    specification: 'E-44 / 20kg',
    warehouse: '一号原料仓',
    storeId: 1,
    storeName: '绝缘门店',
    stock: 1260,
    unit: '公斤',
    minStock: 500,
    maxStock: 2400,
    costPrice: 18.5,
    updatedAt: '2026-09-08 10:24'
  },
  {
    id: 2,
    code: 'RM-002',
    name: '聚酰胺固化剂',
    category: '固化剂',
    specification: '低粘度 / 25kg',
    warehouse: '一号原料仓',
    storeId: 1,
    storeName: '绝缘门店',
    stock: 320,
    unit: '公斤',
    minStock: 400,
    maxStock: 1500,
    costPrice: 22.8,
    updatedAt: '2026-09-08 09:48'
  },
  {
    id: 3,
    code: 'RM-003',
    name: '轻质碳酸钙',
    category: '填料',
    specification: '1250目 / 40kg',
    warehouse: '二号原料仓',
    storeId: 2,
    storeName: '中固门店',
    stock: 2850,
    unit: '公斤',
    minStock: 1000,
    maxStock: 5000,
    costPrice: 1.85,
    updatedAt: '2026-09-07 16:32'
  },
  {
    id: 4,
    code: 'RM-004',
    name: '活性硅微粉',
    category: '填料',
    specification: '800目 / 25kg',
    warehouse: '二号原料仓',
    storeId: 2,
    storeName: '中固门店',
    stock: 0,
    unit: '公斤',
    minStock: 600,
    maxStock: 2400,
    costPrice: 2.4,
    updatedAt: '2026-09-06 14:10'
  },
  {
    id: 5,
    code: 'RM-005',
    name: '氢氧化铝',
    category: '阻燃填料',
    specification: '1250目 / 25kg',
    warehouse: '一号原料仓',
    storeId: 1,
    storeName: '绝缘门店',
    stock: 740,
    unit: '公斤',
    minStock: 600,
    maxStock: 1800,
    costPrice: 4.6,
    updatedAt: '2026-09-08 08:16'
  },
  {
    id: 6,
    code: 'RM-006',
    name: '氧化锌',
    category: '助剂',
    specification: '工业级 / 25kg',
    warehouse: '二号原料仓',
    storeId: 2,
    storeName: '中固门店',
    stock: 980,
    unit: '公斤',
    minStock: 500,
    maxStock: 1600,
    costPrice: 16.2,
    updatedAt: '2026-09-05 11:26'
  },
  {
    id: 7,
    code: 'RM-007',
    name: '沉淀硫酸钡',
    category: '填料',
    specification: '1250目 / 25kg',
    warehouse: '二号原料仓',
    storeId: 2,
    storeName: '中固门店',
    stock: 460,
    unit: '公斤',
    minStock: 500,
    maxStock: 2000,
    costPrice: 3.1,
    updatedAt: '2026-09-04 17:05'
  },
  {
    id: 8,
    code: 'RM-008',
    name: '色浆蓝',
    category: '色浆',
    specification: '蓝色 / 20kg',
    warehouse: '辅料仓',
    storeId: 1,
    storeName: '绝缘门店',
    stock: 82,
    unit: '公斤',
    minStock: 80,
    maxStock: 300,
    costPrice: 32,
    updatedAt: '2026-09-03 13:42'
  },
  {
    id: 9,
    code: 'RM-009',
    name: '消泡剂',
    category: '助剂',
    specification: '通用型 / 25kg',
    warehouse: '辅料仓',
    storeId: 1,
    storeName: '绝缘门店',
    stock: 165,
    unit: '公斤',
    minStock: 120,
    maxStock: 500,
    costPrice: 12.5,
    updatedAt: '2026-09-02 15:18'
  },
  {
    id: 10,
    code: 'RM-010',
    name: '玻璃纤维短切丝',
    category: '增强材料',
    specification: '6mm / 20kg',
    warehouse: '二号原料仓',
    storeId: 2,
    storeName: '中固门店',
    stock: 1250,
    unit: '公斤',
    minStock: 800,
    maxStock: 3000,
    costPrice: 6.8,
    updatedAt: '2026-09-01 10:06'
  }
])

const fallbackInventoryByCode = new Map(
  materials.value.map(material => [material.code, { ...material }])
)

const findById = (items, id) => (
  items.find(item => String(item.id) === String(id))
)

const loadMaterialProducts = async () => {
  try {
    const [productResponse, storeResponse, warehouseResponse, unitResponse] = await Promise.all([
      request({ url: '/raw-material-products', method: 'GET' }),
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: '/products/units/measurements', method: 'GET' })
    ])

    const rawProducts = Array.isArray(productResponse) ? productResponse : []
    if (Array.isArray(storeResponse) && storeResponse.length > 0) {
      stores.value = storeResponse
    }
    allWarehouses.value = Array.isArray(warehouseResponse) ? warehouseResponse : []
    units.value = getMeasurementUnits(unitResponse)

    if (rawProducts.length === 0) {
      return
    }

    materials.value = rawProducts.map(product => {
      const fallback = fallbackInventoryByCode.get(product.code) || {}
      const warehouse = findById(allWarehouses.value, product.warehouseId)
      const category = warehouse?.categories?.find(item => (
        String(item.id) === String(product.categoryId || product.category)
      ))
      const storeIds = Array.isArray(product.storeIds) ? product.storeIds : []
      const storeNames = storeIds
        .map(storeId => findById(stores.value, storeId)?.name)
        .filter(Boolean)
        .join('、')

      return {
        ...fallback,
        ...product,
        category: category?.name
          || (typeof product.category === 'string' ? product.category : fallback.category || '未分类'),
        warehouse: warehouse?.name || fallback.warehouse || '未分配',
        storeId: storeIds[0] ?? null,
        storeIds,
        storeName: storeNames || fallback.storeName || '全部门店',
        stock: fallback.stock ?? 0,
        unit: findById(units.value, product.unitId)?.name || fallback.unit || '未设置',
        minStock: fallback.minStock ?? 0,
        maxStock: fallback.maxStock ?? 0,
        costPrice: fallback.costPrice ?? 0,
        updatedAt: product.updatedAt || fallback.updatedAt || '刚刚'
      }
    })
  } catch (error) {
    console.error('加载原材料商品档案失败:', error)
  }
}

const filters = ref({
  keyword: '',
  category: '',
  warehouse: '',
  status: 'all',
  storeId: null
})

const categories = computed(() => [...new Set(materials.value.map(item => item.category))])
const warehouses = computed(() => [...new Set(materials.value.map(item => item.warehouse))])
const statusOptions = [
  { value: 'all', label: '全部' },
  { value: 'normal', label: '正常' },
  { value: 'low', label: '预警' },
  { value: 'out', label: '缺货' }
]

const sortKey = ref('name')
const sortDirection = ref('asc')
const currentPage = ref(1)
const pageSize = ref(8)
const lastRefreshed = ref('刚刚')

const getStatusKey = (material) => {
  if (material.stock <= 0) return 'out'
  if (material.stock < material.minStock) return 'low'
  return 'normal'
}

const getStatusText = (material) => {
  const statusMap = {
    normal: '库存正常',
    low: '库存预警',
    out: '库存不足'
  }
  return statusMap[getStatusKey(material)]
}

const getStatusClass = (material) => `status-${getStatusKey(material)}`

const filteredMaterials = computed(() => {
  const keyword = filters.value.keyword.toLowerCase()
  const result = materials.value.filter(material => {
    const matchesKeyword = !keyword || [
      material.code,
      material.name,
      material.specification,
      material.category
    ].some(value => String(value).toLowerCase().includes(keyword))
    const matchesCategory = !filters.value.category || material.category === filters.value.category
    const matchesWarehouse = !filters.value.warehouse || material.warehouse === filters.value.warehouse
    const matchesStore = filters.value.storeId === null
      || material.storeIds?.includes(filters.value.storeId)
      || material.storeId === filters.value.storeId
    const matchesStatus = filters.value.status === 'all' || getStatusKey(material) === filters.value.status

    return matchesKeyword && matchesCategory && matchesWarehouse && matchesStore && matchesStatus
  })

  return result.sort((left, right) => {
    const leftValue = left[sortKey.value]
    const rightValue = right[sortKey.value]
    const comparison = typeof leftValue === 'number'
      ? leftValue - rightValue
      : String(leftValue).localeCompare(String(rightValue), 'zh-CN')
    return sortDirection.value === 'asc' ? comparison : -comparison
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredMaterials.value.length / pageSize.value)))
const paginatedMaterials = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredMaterials.value.slice(start, start + pageSize.value)
})
const paginationStart = computed(() => filteredMaterials.value.length ? (currentPage.value - 1) * pageSize.value + 1 : 0)
const paginationEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredMaterials.value.length))

const overview = computed(() => {
  const list = filteredMaterials.value
  return {
    totalTypes: list.length,
    totalStock: list.reduce((sum, item) => sum + item.stock, 0),
    warningCount: list.filter(item => getStatusKey(item) !== 'normal').length,
    totalValue: list.reduce((sum, item) => sum + item.stock * item.costPrice, 0)
  }
})

watch(
  () => [
    filters.value.keyword,
    filters.value.category,
    filters.value.warehouse,
    filters.value.status,
    filters.value.storeId,
    pageSize.value
  ],
  () => {
    currentPage.value = 1
  }
)

watch(totalPages, (value) => {
  if (currentPage.value > value) {
    currentPage.value = value
  }
})

const formatNumber = (value, digits = 0) => {
  return Number(value || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  })
}

const sortBy = (key) => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

const getSortIndicator = (key) => {
  if (sortKey.value !== key) return '↕'
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

const resetFilters = () => {
  filters.value = {
    keyword: '',
    category: '',
    warehouse: '',
    status: 'all',
    storeId: null
  }
}

const refreshData = () => {
  loadMaterialProducts()
  lastRefreshed.value = new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const exportInventory = () => {
  const header = ['编号', '原材料', '分类', '规格', '仓库', '当前库存', '单位', '状态']
  const rows = filteredMaterials.value.map(item => [
    item.code,
    item.name,
    item.category,
    item.specification,
    item.warehouse,
    item.stock,
    item.unit,
    getStatusText(item)
  ])
  const csv = [header, ...rows]
    .map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(','))
    .join('\n')
  const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `原材料库存-${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

const stockInModalRef = ref(null)

// 原材料库存页固定使用采购入库模式；行操作会预填所选原材料。
const openStockInModal = (material = null) => {
  const initialItem = material
    ? { ...material, productId: material.productId ?? material.id }
    : null
  const initialData = filters.value.storeId === null
    ? undefined
    : { storeId: filters.value.storeId }

  stockInModalRef.value?.open({
    type: 'raw-material',
    item: initialItem,
    data: initialData
  })
}

const handleStockInSaved = async () => {
  await loadMaterialProducts()
  lastRefreshed.value = new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(loadMaterialProducts)
</script>

<style scoped>
.material-inventory-page {
  padding: 0;
  background: #f5f5f5;
  min-height: 100vh;
}

.filter-panel,
.table-panel {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.filter-panel {
  padding: 16px 20px;
}

.filter-row {
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

.store-tabs,
.status-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}

.store-tabs button,
.status-tabs button {
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

.store-tabs button:hover,
.status-tabs button:hover {
  background: #e5e7eb;
  color: #374151;
}

.store-tabs button.active,
.status-tabs button.active {
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

.status-filter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.btn {
  min-height: 38px;
  padding: 0 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-secondary {
  color: #374151;
  background: #fff;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #f3f4f6;
}

.btn-primary {
  color: #fff;
  background: #10b981;
  border: 1px solid #10b981;
}

.btn-primary:hover {
  background: #059669;
  border-color: #059669;
}

.button-icon {
  font-size: 16px;
  line-height: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
}

.stat-card {
  padding: 18px 22px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.stat-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
}

.stat-card strong {
  display: block;
  margin: 12px 0 5px;
  color: #111827;
  font-size: 28px;
  font-weight: 700;
}

.stat-card small {
  color: #9ca3af;
  font-size: 13px;
}

.stat-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
}

.mark-blue {
  color: #2563eb;
  background: #dbeafe;
}

.mark-green {
  color: #059669;
  background: #d1fae5;
}

.mark-orange {
  color: #d97706;
  background: #fef3c7;
}

.mark-purple {
  color: #7c3aed;
  background: #ede9fe;
}

.table-panel {
  overflow: hidden;
  background: white;
}

.table-toolbar,
.table-footer {
  display: flex;
  align-items: center;
}

.table-toolbar {
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.table-toolbar h2 {
  margin: 0 0 5px;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.table-toolbar span {
  color: #9ca3af;
  font-size: 13px;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  color: #6b7280;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}

.refresh-button:hover {
  color: #3b82f6;
  border-color: #3b82f6;
}

.refresh-button span {
  color: inherit;
  font-size: 16px;
}

.table-scroll {
  overflow-x: auto;
}

.inventory-table {
  width: 100%;
  min-width: 1080px;
  border-collapse: collapse;
  font-size: 14px;
}

.inventory-table th {
  padding: 14px 16px;
  color: #6b7280;
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  font-size: 14px;
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
}

.inventory-table td {
  padding: 14px 16px;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.inventory-table tbody tr:hover {
  background: #f9fafb;
}

.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background: #f3f4f6;
}

.sort-indicator {
  margin-left: 4px;
  color: #cbd5e1;
}

.sort-indicator.active {
  color: #3b82f6;
}

.number-column {
  text-align: right !important;
}

.code-cell,
.muted-cell {
  color: #6b7280 !important;
}

.material-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.material-name strong {
  color: #1f2937;
  font-weight: 600;
  font-size: 14px;
}

.material-name small,
.max-stock {
  color: #9ca3af;
  font-size: 13px;
}

.category-tag {
  display: inline-block;
  padding: 5px 9px;
  color: #475569;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 13px;
}

.stock-number {
  font-size: 15px;
  font-weight: 600;
}

.status-normal {
  color: #059669 !important;
}

.status-low {
  color: #d97706 !important;
}

.status-out {
  color: #dc2626 !important;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 5px;
  background: #f8fafc;
  font-size: 13px;
  font-weight: 500;
}

.status-normal.status-badge {
  background: #ecfdf5;
}

.status-low.status-badge {
  background: #fffbeb;
}

.status-out.status-badge {
  background: #fef2f2;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.actions-column {
  text-align: right !important;
}

.table-action {
  padding: 6px 12px;
  color: #3b82f6;
  background: white;
  border: 1px solid #3b82f6;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
}

.table-action:hover {
  color: #fff;
  background: #3b82f6;
}

.empty-state {
  padding: 60px 20px !important;
  color: #9ca3af !important;
  text-align: center !important;
}

.empty-title {
  color: #6b7280;
  font-weight: 600;
  font-size: 14px;
}

.empty-state p {
  margin: 8px 0 0;
  font-size: 13px;
}

.table-footer {
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  color: #9ca3af;
  font-size: 13px;
  border-top: 1px solid #e5e7eb;
  background: white;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination select,
.pagination button {
  min-height: 34px;
  padding: 0 12px;
  color: #6b7280;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 13px;
}

.pagination button {
  cursor: pointer;
}

.pagination button:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
}

.pagination button:disabled {
  color: #cbd5e1;
  background: #f8fafc;
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
}

@media (max-width: 1000px) {
  .material-inventory-page {
    padding: 22px 18px 30px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .material-inventory-page {
    padding: 18px 12px 24px;
  }

  .header-actions,
  .header-actions .btn {
    width: 100%;
  }

  .header-actions .btn {
    justify-content: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .filter-field,
  .search-field,
  .status-filter {
    width: 100%;
    flex-basis: 100%;
  }

  .store-filter {
    align-items: flex-start;
    flex-direction: column;
  }

  .filter-result {
    margin-left: 0;
  }

  .table-footer {
    align-items: flex-start;
    flex-direction: column;
  }

}
</style>
