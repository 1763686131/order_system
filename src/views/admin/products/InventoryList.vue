<template>
  <div class="inventory-list-page" :class="{ 'raw-material-mode': isRawMaterial }">
    <div class="search-bar">
      <label class="search-field">
        <span class="sr-only">搜索{{ entityLabel }}</span>
        <Search class="search-icon" :size="16" aria-hidden="true" />
        <input v-model.trim="filters.productName" type="search" placeholder="搜索名称、编号或规格" />
      </label>

      <span class="filter-label">门店</span>
      <div class="store-tabs" aria-label="门店">
        <button type="button" class="store-tab" :class="{ active: selectedStoreId === null }" :aria-pressed="selectedStoreId === null" @click="selectedStoreId = null">
          全部门店
        </button>
        <button v-for="store in allStores" :key="store.id" type="button" class="store-tab" :class="{ active: sameId(selectedStoreId, store.id) }" :aria-pressed="sameId(selectedStoreId, store.id)" @click="selectedStoreId = store.id">
          {{ store.name }}
        </button>
      </div>

      <label class="filter-field">
        <span>分类</span>
        <select v-model="filters.categoryId">
          <option :value="null">全部分类</option>
          <option v-for="category in allCategories" :key="category.id" :value="category.id">{{ category.name }}</option>
        </select>
      </label>
      <label class="filter-field">
        <span>仓库</span>
        <select v-model="filters.warehouseId">
          <option :value="null">全部仓库</option>
          <option v-for="warehouse in allWarehouses" :key="warehouse.id" :value="warehouse.id">{{ warehouse.name }}</option>
        </select>
      </label>

      <div class="status-filter" aria-label="库存状态">
        <span class="filter-label">库存状态</span>
        <div class="status-tabs">
          <button v-for="status in statusOptions" :key="status.value" type="button" :class="{ active: filters.status === status.value }" :aria-pressed="filters.status === status.value" @click="filters.status = status.value">
            {{ status.label }}
          </button>
        </div>
      </div>
      <label class="filter-field">
        <span>{{ entityLabel }}状态</span>
        <select v-model="filters.productStatus">
          <option value="all">全部状态</option>
          <option value="enabled">启用</option>
          <option value="disabled">停用</option>
        </select>
      </label>

      <div class="action-buttons">
        <button class="btn btn-secondary" type="button" @click="resetFilters">
          <RotateCcw :size="16" aria-hidden="true" />重置筛选
        </button>
        <button class="btn btn-secondary icon-button" type="button" title="刷新" aria-label="刷新" :disabled="loading" @click="loadInventory">
          <RefreshCw :size="16" aria-hidden="true" />
        </button>
        <button class="btn btn-secondary" type="button" :disabled="loading || !!loadError" @click="handleExport">
          <Download :size="16" aria-hidden="true" />导出
        </button>
        <button v-if="canManageProducts" class="btn btn-danger" type="button" :disabled="selectedCount === 0 || deleting || loading" @click="handleBatchDelete">
          <Trash2 :size="16" aria-hidden="true" />批量删除
        </button>
        <button v-if="canManageProducts" class="btn btn-primary" type="button" :disabled="deleting || loading" @click="handleNew">
          <Plus :size="16" aria-hidden="true" />新增{{ entityLabel }}
        </button>
      </div>
    </div>

    <section class="stats-cards" aria-label="库存概览">
      <div v-for="stat in summaryStats" :key="stat.label" class="stat-card">
        <div class="stat-icon" :class="`stat-${stat.tone}`">
          <component :is="stat.icon" :size="22" aria-hidden="true" />
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ stat.value }}</div>
        </div>
      </div>
    </section>

    <section class="table-panel">
      <div class="table-toolbar">
        <h2>{{ pageTitle }}</h2>
        <span v-if="lastRefreshed">最后刷新：{{ lastRefreshed }}</span>
      </div>
      <div class="table-container">
        <table class="inventory-table">
          <thead>
            <tr>
              <th class="col-checkbox">
                <input type="checkbox" :checked="allPageSelected" :indeterminate="somePageSelected" :disabled="!canManageProducts || loading || deleting || paginatedInventory.length === 0" :aria-label="`选择本页全部${entityLabel}`" @change="handleSelectAll($event.target.checked)" />
              </th>
              <th class="col-id">ID</th>
              <th class="col-code sortable" @click="handleSort('code')">
                {{ entityLabel }}编号<span class="sort-icon">{{ getSortIcon('code') }}</span>
              </th>
              <th class="col-name sortable" @click="handleSort('name')">
                {{ entityLabel }}名称<span class="sort-icon">{{ getSortIcon('name') }}</span>
              </th>
              <th class="col-spec">规格型号</th>
              <th class="col-warehouse">仓库</th>
              <th class="col-category">分类</th>
              <th class="col-stock sortable" @click="handleSort('stock')">
                当前库存<span class="sort-icon">{{ getSortIcon('stock') }}</span>
              </th>
              <th v-if="isRawMaterial" class="col-amount sortable" @click="handleSort('inventoryAmount')">
                库存金额<span class="sort-icon">{{ getSortIcon('inventoryAmount') }}</span>
              </th>
              <th class="col-unit">单位</th>
              <th v-if="!isRawMaterial" class="col-attributes">商品属性</th>
              <th v-if="!isRawMaterial" class="col-price">零售价格</th>
              <th class="col-min-stock">最低库存</th>
              <th class="col-max-stock">最高库存</th>
              <th class="col-status">库存状态</th>
              <th class="col-product-status">{{ entityLabel }}状态</th>
              <th class="col-notes">备注信息</th>
              <th class="col-update-time sortable" @click="handleSort('updateTime')">
                更新时间<span class="sort-icon">{{ getSortIcon('updateTime') }}</span>
              </th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedInventory"
              :key="item.id"
              :class="{ 'row-disabled': item.enabled === false, 'inventory-row': isRawMaterial }"
              :tabindex="isRawMaterial ? 0 : undefined"
              @click="openMovementDetail(item)"
              @keydown.enter.self="openMovementDetail(item)"
              @keydown.space.self="handleRowSpace($event, item)"
            >
              <td class="col-checkbox" @click.stop @keydown.stop>
                <input type="checkbox" :checked="isSelected(item)" :disabled="!canManageProducts || loading || deleting" :aria-label="`选择${entityLabel}${item.productName}`" @change="handleSelect(item, $event.target.checked)" />
              </td>
              <td class="col-id">{{ item.id }}</td>
              <td class="col-code">{{ item.productCode || '-' }}</td>
              <td class="col-name">
                <a v-if="canManageProducts" href="#" class="product-link" @click.stop.prevent="handleEdit(item)" @keydown.stop>{{ item.productName }}</a>
                <span v-else>{{ item.productName }}</span>
                <small v-if="isRawMaterial" class="store-name">{{ item.storeName }}</small>
              </td>
              <td class="col-spec">{{ item.specification || '-' }}</td>
              <td class="col-warehouse">{{ item.warehouseName || '-' }}</td>
              <td class="col-category">{{ item.categoryName || '-' }}</td>
              <td class="col-stock">
                <span :class="['stock-value', getStockClass(item)]">{{ formatNumber(item.stock) }}</span>
              </td>
              <td v-if="isRawMaterial" class="col-amount">¥{{ formatPrice(item.inventoryAmount) }}</td>
              <td class="col-unit">{{ item.unit || '-' }}</td>
              <td v-if="!isRawMaterial" class="col-attributes">
                <template v-if="item.enableAttributes && item.attributeCombinations?.length">
                  <div v-for="(combination, index) in item.attributeCombinations" :key="index" class="attribute-row">{{ combination.name }}</div>
                </template>
                <span v-else>-</span>
              </td>
              <td v-if="!isRawMaterial" class="col-price">
                <template v-if="item.enableAttributes && item.attributeCombinations?.length">
                  <div v-for="(combination, index) in item.attributeCombinations" :key="index" class="attribute-row">{{ formatPrice(combination.retailPrice) }} 元</div>
                </template>
                <span v-else>{{ formatPrice(item.attributeCombinations?.[0]?.retailPrice || item.price) }} 元</span>
              </td>
              <td class="col-min-stock">{{ item.minStock || '-' }}</td>
              <td class="col-max-stock">{{ item.maxStock || '-' }}</td>
              <td class="col-status">
                <span :class="['status-badge', getStockStatusClass(item)]">{{ getStockStatusText(item) }}</span>
              </td>
              <td class="col-product-status">
                <span :class="['status-badge', item.enabled === false ? 'status-disabled' : 'status-success']">{{ item.enabled === false ? '停用' : '启用' }}</span>
              </td>
              <td class="col-notes" :title="item.notes">{{ item.notes || '-' }}</td>
              <td class="col-update-time">{{ formatDateTime(item.updateTime) }}</td>
              <td class="col-actions" @click.stop @keydown.stop>
                <div class="row-actions">
                  <button v-if="isRawMaterial" class="btn-action btn-edit" type="button" title="库存流水" :aria-label="`查看${item.productName}库存流水`" @click="openMovementDetail(item)">
                    <List :size="15" aria-hidden="true" />
                  </button>
                  <template v-if="canManageProducts">
                    <button class="btn-action btn-edit" type="button" :title="`修改${entityLabel}`" :aria-label="`修改${entityLabel}${item.productName}`" :disabled="deleting || loading" @click="handleEdit(item)">
                      <Pencil :size="15" aria-hidden="true" />
                    </button>
                    <button class="btn-action btn-edit" type="button" :title="`复制${entityLabel}`" :aria-label="`复制${entityLabel}${item.productName}`" :disabled="deleting || loading" @click="handleCopy(item)">
                      <Copy :size="15" aria-hidden="true" />
                    </button>
                    <button class="btn-action btn-delete" type="button" :title="`删除${entityLabel}`" :aria-label="`删除${entityLabel}${item.productName}`" :disabled="deleting || loading" @click="deleteProducts([item])">
                      <Trash2 :size="15" aria-hidden="true" />
                    </button>
                  </template>
                  <span v-else-if="!isRawMaterial">-</span>
                </div>
              </td>
            </tr>
            <tr v-if="loading || loadError || filteredInventory.length === 0">
              <td :colspan="columnCount" class="empty-state">
                <p v-if="loading">正在加载{{ pageTitle }}...</p>
                <div v-else-if="loadError" class="load-error" role="alert">
                  <span>{{ loadError }}</span>
                  <button class="btn btn-secondary" type="button" @click="loadInventory">重试</button>
                </div>
                <p v-else>暂无匹配的{{ entityLabel }}</p>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="pagination">
        <div class="pagination-left">
          <button class="page-btn" type="button" :disabled="currentPage === 1" @click="goToPage(1)">首页</button>
          <button class="page-btn" type="button" :disabled="currentPage === 1" @click="prevPage">上一页</button>
          <button class="page-btn" type="button" :disabled="currentPage >= totalPages" @click="nextPage">下一页</button>
          <span class="page-jump">
            到第<input v-model.number="jumpPage" type="number" min="1" :max="totalPages" class="jump-input" aria-label="跳转页码" @keyup.enter="jumpToPage" />页
          </span>
          <button class="btn-jump" type="button" @click="jumpToPage">确定</button>
        </div>
        <div class="pagination-right">
          <span class="page-info">共 {{ totalInventory }} 条</span>
          <select v-model.number="pageSize" class="page-size-select" aria-label="每页条数">
            <option v-for="size in pageSizes" :key="size" :value="size">{{ size }} 条/页</option>
          </select>
        </div>
      </footer>
    </section>

    <ProductFormModal :key="mode" ref="productFormModal" :mode="mode" @save="handleProductSaved" @refresh="handleProductSaved" />
    <InventoryMovementModal
      v-if="isRawMaterial"
      :item="movementDetailItem"
      :records="movementRecords"
      :loading="movementDetailLoading"
      :error="movementDetailError"
      @close="closeMovementDetail"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { CircleAlert, CircleCheck, Coins, Copy, Download, Layers, List, Package, Pencil, Plus, RefreshCw, RotateCcw, Search, Trash2, TriangleAlert } from '@lucide/vue'
import request from '@/api/request'
import { getMeasurementUnits } from '@/utils/unitHelper'
import ProductFormModal from '@/components/admin/ProductFormModal.vue'
import InventoryMovementModal from '@/components/admin/InventoryMovementModal.vue'
import { useUserStore } from '@/stores/user'
import { ADMIN_ROUTE_BRANCH_PERMISSIONS } from '@/utils/adminAccess'

const props = defineProps({
  mode: {
    type: String,
    default: 'finished-product',
    validator: value => ['finished-product', 'raw-material'].includes(value)
  }
})

const isRawMaterial = computed(() => props.mode === 'raw-material')
const entityLabel = computed(() => isRawMaterial.value ? '原材料' : '商品')
const pageTitle = computed(() => isRawMaterial.value ? '原材料库存' : '成品库存')
const apiPrefix = computed(() => isRawMaterial.value ? '/raw-material-products' : '/products')
const userStore = useUserStore()
const canManageProducts = computed(() => userStore.hasPerm(
  isRawMaterial.value
    ? ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.MATERIALS
    : ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.LIST
))

const createFilters = () => ({
  productName: '',
  productCode: '',
  warehouseId: null,
  categoryId: null,
  status: 'all',
  productStatus: 'all',
  lowStockOnly: false
})
const filters = ref(createFilters())
const selectedStoreId = ref(null)
const products = ref([])
const stockBalances = ref([])
const allStores = ref([])
const allWarehouses = ref([])
const allUnits = ref([])
const selectedIds = ref([])
const currentPage = ref(1)
const pageSize = ref(30)
const jumpPage = ref(1)
const sortKey = ref('')
const sortDirection = ref('asc')
const loading = ref(false)
const loadError = ref('')
const lastRefreshed = ref('')
const productFormModal = ref(null)
const deleting = ref(false)
const movementDetailItem = ref(null)
const movementRecords = ref([])
const movementDetailLoading = ref(false)
const movementDetailError = ref('')
let loadVersion = 0
let movementVersion = 0
let modeVersion = 0
let disposed = false

const statusOptions = [
  { value: 'all', label: '全部' },
  { value: 'normal', label: '正常' },
  { value: 'low', label: '预警' },
  { value: 'out', label: '缺货' }
]
const pageSizes = computed(() => isRawMaterial.value ? [8, 15, 30] : [30, 50, 100])
const columnCount = computed(() => isRawMaterial.value ? 17 : 18)
const sameId = (left, right) => left !== null && left !== undefined
  && right !== null && right !== undefined && String(left) === String(right)
const findById = (items, id) => items.find(item => sameId(item.id, id))
const toFiniteNumber = value => Number.isFinite(Number(value)) ? Number(value) : 0

// 保留原材料页已有的安全库存基线，档案中的配置优先。
const rawMaterialStockLimits = {
  'RM-001': [500, 2400],
  'RM-002': [400, 1500],
  'RM-003': [1000, 5000],
  'RM-004': [600, 2400],
  'RM-005': [600, 1800],
  'RM-006': [500, 1600],
  'RM-007': [500, 2000],
  'RM-008': [80, 300],
  'RM-009': [120, 500],
  'RM-010': [800, 3000]
}

const loadInventory = async () => {
  const version = ++loadVersion
  const mode = props.mode
  const raw = mode === 'raw-material'
  loading.value = true
  loadError.value = ''
  try {
    const [productResponse, balanceResponse, stores, warehouses, units] = await Promise.all([
      request({ url: raw ? '/raw-material-products' : '/products/inventory', method: 'GET' }),
      raw ? request({ url: '/stock-balances', method: 'GET', params: { type: mode } }) : Promise.resolve([]),
      request({ url: '/stores', method: 'GET' }),
      request({ url: '/warehouses', method: 'GET' }),
      request({ url: '/products/units/measurements', method: 'GET' })
    ])
    // 切换模式或刷新后，较早的请求不能覆盖当前列表。
    if (disposed || version !== loadVersion || mode !== props.mode) return
    products.value = Array.isArray(productResponse) ? productResponse : []
    stockBalances.value = Array.isArray(balanceResponse) ? balanceResponse : []
    allStores.value = Array.isArray(stores) ? stores : []
    allWarehouses.value = Array.isArray(warehouses) ? warehouses : []
    allUnits.value = getMeasurementUnits(units)
    const existingIds = new Set(products.value.map(item => String(item.id)))
    selectedIds.value = selectedIds.value.filter(id => existingIds.has(id))
    lastRefreshed.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch (error) {
    if (disposed || version !== loadVersion || mode !== props.mode) return
    products.value = []
    stockBalances.value = []
    selectedIds.value = []
    loadError.value = error?.response?.data?.message || `${pageTitle.value}加载失败，请重试。`
  } finally {
    if (!disposed && version === loadVersion && mode === props.mode) loading.value = false
  }
}

const stockBalanceMap = computed(() => {
  const result = new Map()
  stockBalances.value.forEach(balance => {
    if (balance.productType && balance.productType !== 'raw-material') return
    const id = String(balance.productId)
    if (!result.has(id)) result.set(id, [])
    result.get(id).push(balance)
  })
  return result
})

const inventory = computed(() => products.value.map(product => {
  const warehouse = findById(allWarehouses.value, product.warehouseId)
  const categoryId = product.categoryId ?? product.category
  const category = findById(warehouse?.categories || [], categoryId)
  const storeIds = Array.isArray(product.storeIds) ? product.storeIds : []
  const stockLimits = isRawMaterial.value ? rawMaterialStockLimits[product.code] : null
  const item = {
    ...product,
    productId: product.id,
    productCode: product.code || '',
    productName: product.name || '',
    categoryId,
    categoryName: category?.name || (isRawMaterial.value && typeof categoryId === 'string' ? categoryId : '未分类'),
    warehouseName: warehouse?.name || '未分配',
    storeIds,
    storeName: storeIds.map(id => findById(allStores.value, id)?.name).filter(Boolean).join('、') || '全部门店',
    unit: findById(allUnits.value, product.unitId)?.name || (isRawMaterial.value ? '未设置' : '件'),
    minStock: toFiniteNumber(product.minStock ?? stockLimits?.[0]),
    maxStock: toFiniteNumber(product.maxStock ?? stockLimits?.[1]),
    stock: toFiniteNumber(product.stock),
    updateTime: product.inventoryUpdatedAt || product.updatedAt || product.createdAt || ''
  }
  if (!isRawMaterial.value) return item

  const balances = (stockBalanceMap.value.get(String(product.id)) || []).filter(balance => (
    (selectedStoreId.value === null || sameId(balance.storeId, selectedStoreId.value))
    && (filters.value.warehouseId === null || sameId(balance.warehouseId, filters.value.warehouseId))
  ))
  const stock = balances.reduce((sum, balance) => sum + toFiniteNumber(balance.quantity), 0)
  const inventoryAmount = balances.reduce((sum, balance) => sum + (
    balance.inventoryAmount === null || balance.inventoryAmount === undefined
      ? toFiniteNumber(balance.quantity) * toFiniteNumber(balance.averageUnitCost)
      : toFiniteNumber(balance.inventoryAmount)
  ), 0)
  const balanceUpdatedAt = balances.reduce((latest, balance) => (
    String(balance.updatedAt || '') > latest ? String(balance.updatedAt) : latest
  ), '')
  const warehouseNames = [...new Set(balances.map(balance => (
    findById(allWarehouses.value, balance.warehouseId)?.name
  )).filter(Boolean))]

  return {
    ...item,
    stock,
    inventoryAmount,
    averageUnitCost: stock > 0 ? inventoryAmount / stock : 0,
    visibleBalanceCount: balances.length,
    warehouseName: findById(allWarehouses.value, filters.value.warehouseId)?.name
      || warehouseNames.join('、') || item.warehouseName,
    storeName: findById(allStores.value, selectedStoreId.value)?.name || item.storeName,
    updateTime: balanceUpdatedAt || item.updateTime
  }
}))

const allCategories = computed(() => {
  const categories = new Map()
  allWarehouses.value.forEach(warehouse => (warehouse.categories || []).forEach(category => {
    if (!categories.has(String(category.id))) categories.set(String(category.id), category)
  }))
  if (isRawMaterial.value) {
    inventory.value.forEach(item => {
      if (item.categoryId !== null && item.categoryId !== undefined && item.categoryId !== ''
        && !categories.has(String(item.categoryId))) {
        categories.set(String(item.categoryId), { id: item.categoryId, name: item.categoryName })
      }
    })
  }
  return [...categories.values()]
})

const getStockStatus = item => {
  if (item.stock <= 0) return 'out'
  if (item.stock < item.minStock) return 'low'
  return 'normal'
}

const filteredInventory = computed(() => {
  const keyword = filters.value.productName.toLowerCase()
  const result = inventory.value.filter(item => {
    const matchesKeyword = !keyword || [item.productName, item.productCode, item.specification, ...(isRawMaterial.value ? [item.categoryName] : [])]
      .some(value => String(value || '').toLowerCase().includes(keyword))
    const matchesCode = !filters.value.productCode || item.productCode.toLowerCase().includes(filters.value.productCode.toLowerCase())
    const matchesCategory = filters.value.categoryId === null || sameId(item.categoryId, filters.value.categoryId)
    const matchesStore = selectedStoreId.value === null || item.storeIds.some(id => sameId(id, selectedStoreId.value))
    const matchesWarehouse = filters.value.warehouseId === null || sameId(item.warehouseId, filters.value.warehouseId)
    // 已有余额按实际位置筛选；零库存档案仍可按默认门店、仓库查到。
    const matchesLocation = matchesStore && matchesWarehouse || isRawMaterial.value && item.visibleBalanceCount > 0
    const matchesStock = filters.value.status === 'all' || getStockStatus(item) === filters.value.status
    const matchesEnabled = filters.value.productStatus === 'all'
      || (filters.value.productStatus === 'disabled' ? item.enabled === false : item.enabled !== false)
    return matchesKeyword && matchesCode && matchesCategory && matchesLocation && matchesStock && matchesEnabled
      && (!filters.value.lowStockOnly || item.stock < item.minStock)
  })
  if (!sortKey.value) return result
  return result.sort((left, right) => {
    const field = { name: 'productName', code: 'productCode' }[sortKey.value] || sortKey.value
    const a = field === 'updateTime' ? new Date(left[field]).getTime() || 0 : left[field]
    const b = field === 'updateTime' ? new Date(right[field]).getTime() || 0 : right[field]
    const comparison = typeof a === 'number' && typeof b === 'number'
      ? a - b : String(a || '').localeCompare(String(b || ''), 'zh-CN')
    return sortDirection.value === 'asc' ? comparison : -comparison
  })
})

const totalInventory = computed(() => filteredInventory.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalInventory.value / pageSize.value)))
const paginatedInventory = computed(() => filteredInventory.value.slice(
  (currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value
))
const isSelected = item => selectedIds.value.includes(String(item.id))
const selectedCount = computed(() => selectedIds.value.length)
const allPageSelected = computed(() => paginatedInventory.value.length > 0 && paginatedInventory.value.every(isSelected))
const somePageSelected = computed(() => !allPageSelected.value && paginatedInventory.value.some(isSelected))
const normalStockCount = computed(() => filteredInventory.value.filter(item => getStockStatus(item) === 'normal').length)
const lowStockCount = computed(() => filteredInventory.value.filter(item => getStockStatus(item) === 'low').length)
const outOfStockCount = computed(() => filteredInventory.value.filter(item => getStockStatus(item) === 'out').length)
const totalStock = computed(() => filteredInventory.value.reduce((sum, item) => sum + item.stock, 0))
const totalValue = computed(() => filteredInventory.value.reduce((sum, item) => sum + toFiniteNumber(item.inventoryAmount), 0))
const formatNumber = value => toFiniteNumber(value).toLocaleString('zh-CN', { maximumFractionDigits: 3 })
const formatPrice = value => toFiniteNumber(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const summaryStats = computed(() => isRawMaterial.value ? [
  { label: '材料品种', value: totalInventory.value, icon: Package, tone: 'blue' },
  { label: '库存总量', value: formatNumber(totalStock.value), icon: Layers, tone: 'green' },
  { label: '库存预警', value: lowStockCount.value + outOfStockCount.value, icon: TriangleAlert, tone: 'amber' },
  { label: '库存金额', value: `¥${formatPrice(totalValue.value)}`, icon: Coins, tone: 'red' }
] : [
  { label: '商品总数', value: totalInventory.value, icon: Package, tone: 'blue' },
  { label: '库存正常', value: normalStockCount.value, icon: CircleCheck, tone: 'green' },
  { label: '库存预警', value: lowStockCount.value, icon: TriangleAlert, tone: 'amber' },
  { label: '库存不足', value: outOfStockCount.value, icon: CircleAlert, tone: 'red' }
])

const getStockClass = item => {
  const status = getStockStatus(item)
  if (status === 'out') return 'out-of-stock'
  if (status === 'low') return 'low-stock'
  if (!isRawMaterial.value && item.maxStock > 0 && item.stock > item.maxStock) return 'over-stock'
  return 'normal-stock'
}
const getStockStatusClass = item => ({
  'out-of-stock': 'status-danger', 'low-stock': 'status-warning',
  'over-stock': 'status-info', 'normal-stock': 'status-success'
}[getStockClass(item)])
const getStockStatusText = item => isRawMaterial.value
  ? { normal: '库存正常', low: '库存预警', out: '库存不足' }[getStockStatus(item)]
  : ({
  'out-of-stock': '缺货', 'low-stock': '库存不足',
  'over-stock': '库存过高', 'normal-stock': '正常'
}[getStockClass(item)])
const formatDateTime = value => {
  if (!value) return '-'
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return String(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const resetFilters = () => {
  filters.value = createFilters()
  selectedStoreId.value = null
  sortKey.value = isRawMaterial.value ? 'name' : ''
  sortDirection.value = 'asc'
}
const handleSelect = (item, selected) => {
  if (!canManageProducts.value || loading.value || deleting.value) return
  const id = String(item.id)
  selectedIds.value = selected ? [...new Set([...selectedIds.value, id])] : selectedIds.value.filter(value => value !== id)
}
const handleSelectAll = selected => paginatedInventory.value.forEach(item => handleSelect(item, selected))
const handleNew = () => {
  if (!canManageProducts.value || loading.value || deleting.value) return
  productFormModal.value?.open(selectedStoreId.value === null ? null : { storeIds: [selectedStoreId.value] })
}
const getFormData = item => {
  // 使用原始档案并深拷贝，避免展示字段或取消编辑污染分类、仓库和配置。
  const product = findById(products.value, item.id)
  return product ? JSON.parse(JSON.stringify(product)) : null
}
const handleEdit = item => {
  if (!canManageProducts.value || loading.value || deleting.value) return
  const product = getFormData(item)
  if (product) productFormModal.value?.open(product)
}
const handleCopy = item => {
  if (!canManageProducts.value || loading.value || deleting.value) return
  const product = getFormData(item)
  if (!product) return
  delete product.id
  productFormModal.value?.open(product)
}
const handleProductSaved = () => loadInventory()
const deleteProducts = async items => {
  if (!canManageProducts.value || !items.length || deleting.value || loading.value) return
  if (!window.confirm(`确定要删除选中的 ${items.length} 个${entityLabel.value}吗？`)) return
  const mode = props.mode
  const generation = modeVersion
  const prefix = apiPrefix.value
  const label = entityLabel.value
  deleting.value = true
  try {
    const results = await Promise.allSettled(items.map(item => request({ url: `${prefix}/${item.id}`, method: 'DELETE' })))
    if (disposed || generation !== modeVersion || mode !== props.mode) return
    if (items.some((item, index) => results[index].status === 'fulfilled' && sameId(item.id, movementDetailItem.value?.id))) closeMovementDetail()
    await loadInventory()
    if (disposed || generation !== modeVersion || mode !== props.mode) return
    const failed = results.filter(result => result.status === 'rejected')
    if (failed.length) {
      const error = failed[0].reason
      window.alert(`${failed.length} 个${label}删除失败：${error?.response?.data?.message || error?.message || '请重试。'}`)
    }
  } finally {
    if (!disposed && generation === modeVersion && mode === props.mode) deleting.value = false
  }
}
const handleBatchDelete = () => deleteProducts(inventory.value.filter(isSelected))
const handleSort = field => {
  sortDirection.value = sortKey.value === field && sortDirection.value === 'asc' ? 'desc' : 'asc'
  sortKey.value = field
}
const getSortIcon = field => sortKey.value !== field ? '⇅' : sortDirection.value === 'asc' ? '↑' : '↓'
const goToPage = page => { currentPage.value = Math.max(1, Math.min(totalPages.value, page)) }
const prevPage = () => goToPage(currentPage.value - 1)
const nextPage = () => goToPage(currentPage.value + 1)
const jumpToPage = () => {
  if (Number.isInteger(jumpPage.value) && jumpPage.value >= 1 && jumpPage.value <= totalPages.value) goToPage(jumpPage.value)
}

const handleExport = () => {
  if (loading.value || loadError.value) return
  const header = ['编号', `${entityLabel.value}名称`, '分类', '规格', '门店', '仓库', '当前库存', '单位',
    ...(isRawMaterial.value ? ['库存金额'] : ['商品属性', '零售价格']),
    '最低库存', '最高库存', '库存状态', `${entityLabel.value}状态`, '备注', '更新时间']
  const rows = filteredInventory.value.map(item => [
    item.productCode, item.productName, item.categoryName, item.specification, item.storeName, item.warehouseName, item.stock, item.unit,
    ...(isRawMaterial.value ? [item.inventoryAmount] : [
      (item.attributeCombinations || []).map(combo => combo.name).join('、'),
      item.enableAttributes && item.attributeCombinations?.length
        ? item.attributeCombinations.map(combo => toFiniteNumber(combo.retailPrice)).join('、')
        : toFiniteNumber(item.attributeCombinations?.[0]?.retailPrice || item.price)
    ]),
    item.minStock, item.maxStock, getStockStatusText(item), item.enabled === false ? '停用' : '启用', item.notes, formatDateTime(item.updateTime)
  ])
  const csv = [header, ...rows].map(row => row.map(value => `"${String(value ?? '').replaceAll('"', '""')}"`).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `${pageTitle.value}-${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

const closeMovementDetail = () => {
  movementVersion++
  movementDetailItem.value = null
  movementRecords.value = []
  movementDetailError.value = ''
  movementDetailLoading.value = false
}
const openMovementDetail = async item => {
  if (!isRawMaterial.value || loading.value) return
  const version = ++movementVersion
  movementDetailItem.value = item
  movementRecords.value = []
  movementDetailError.value = ''
  movementDetailLoading.value = true
  try {
    const params = { type: 'raw-material', productId: item.id, limit: 200 }
    if (selectedStoreId.value !== null) params.storeId = selectedStoreId.value
    if (filters.value.warehouseId !== null) params.warehouseId = filters.value.warehouseId
    const response = await request({ url: '/stock-movements', method: 'GET', params })
    if (!disposed && version === movementVersion) movementRecords.value = Array.isArray(response) ? response : []
  } catch (error) {
    if (!disposed && version === movementVersion) movementDetailError.value = error?.response?.data?.message || '库存流水加载失败。'
  } finally {
    if (!disposed && version === movementVersion) movementDetailLoading.value = false
  }
}
const handleRowSpace = (event, item) => {
  if (!isRawMaterial.value) return
  event.preventDefault()
  openMovementDetail(item)
}

watch([filters, selectedStoreId, pageSize], () => {
  currentPage.value = 1
  jumpPage.value = 1
}, { deep: true })
watch(totalPages, pages => { currentPage.value = Math.min(currentPage.value, pages) })
watch(() => props.mode, () => {
  modeVersion++
  resetFilters()
  selectedIds.value = []
  products.value = []
  stockBalances.value = []
  currentPage.value = 1
  jumpPage.value = 1
  pageSize.value = isRawMaterial.value ? 8 : 30
  lastRefreshed.value = ''
  deleting.value = false
  closeMovementDetail()
  loadInventory()
}, { immediate: true })
onBeforeUnmount(() => {
  disposed = true
  loadVersion++
  movementVersion++
})
defineExpose({ reload: loadInventory })
</script>

<style scoped>
.inventory-list-page {
  padding: 0;
  background: #f5f5f5;
  min-height: 100vh;
  color: #1f2937;
}
.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
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
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #1f2937;
  font-size: 14px;
}
.search-icon { position: absolute; left: 13px; color: #94a3b8; }
.filter-label { color: #6b7280; font-size: 14px; font-weight: 500; white-space: nowrap; }
.store-tabs, .status-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}
.store-tab, .status-tabs button {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  white-space: nowrap;
  background: transparent;
  border: 1px solid transparent;
}
.store-tab:hover, .status-tabs button:hover { background: #e5e7eb; color: #374151; }
.store-tab.active, .status-tabs button.active { background: #10b981; color: #fff; }
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
.filter-field span { color: #6b7280; font-size: 14px; white-space: nowrap; }
.filter-field select {
  border: 0;
  outline: 0;
  color: #1f2937;
  background: transparent;
  font-size: 14px;
  min-width: 100px;
  height: 36px;
}
.status-filter { display: flex; align-items: center; gap: 10px; }
.action-buttons { display: flex; align-items: center; gap: 8px; margin-left: auto; flex-wrap: wrap; }
.btn {
  min-height: 38px;
  padding: 0 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
}
.btn svg { flex-shrink: 0; }
.btn-secondary { color: #374151; background: #fff; border: 1px solid #d1d5db; }
.btn-secondary:hover { border-color: #3b82f6; color: #3b82f6; background: #f3f4f6; }
.btn-primary { color: #fff; background: #10b981; border: 1px solid #10b981; }
.btn-primary:hover { background: #059669; border-color: #059669; }
.icon-button { width: 38px; height: 38px; padding: 0; }
.btn-danger { color: #fff; background: #ef4444; border: 1px solid #ef4444; }
.btn-danger:hover:not(:disabled) { background: #dc2626; }
button:disabled { opacity: 0.55; cursor: not-allowed; }
button:focus-visible, input:focus-visible, select:focus-visible, .inventory-row:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
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
.stats-cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); background: #fff; }
.stat-card { padding: 20px; display: flex; align-items: center; gap: 16px; min-width: 0; border-bottom: 1px solid #e5e7eb; }
.stat-icon { width: 44px; height: 44px; flex-shrink: 0; border-radius: 6px; display: flex; align-items: center; justify-content: center; }
.stat-blue { color: #2563eb; background: #dbeafe; }
.stat-green { color: #059669; background: #d1fae5; }
.stat-amber { color: #d97706; background: #fef3c7; }
.stat-red { color: #dc2626; background: #fee2e2; }
.stat-content { min-width: 0; }
.stat-label { font-size: 13px; color: #6b7280; margin-bottom: 4px; }
.stat-value { font-size: 24px; font-weight: 600; overflow-wrap: anywhere; color: #111827; font-variant-numeric: tabular-nums; }
.table-panel { background: white; }
.table-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 14px 20px; border-bottom: 1px solid #e5e7eb; }
.table-toolbar h2 { font-size: 16px; font-weight: 600; margin: 0; }
.table-toolbar span { color: #9ca3af; font-size: 13px; }
.table-container { overflow-x: auto; }
.inventory-table { width: 100%; min-width: 1900px; border-collapse: collapse; font-size: 13px; }
.raw-material-mode .inventory-table { min-width: 1700px; }
.inventory-table thead { background: #f9fafb; border-bottom: 2px solid #e5e7eb; }
.inventory-table th { padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; white-space: nowrap; }
.inventory-table th.sortable { cursor: pointer; user-select: none; }
.inventory-table th.sortable:hover { background: #f3f4f6; }
.sort-icon { margin-left: 4px; color: #9ca3af; font-size: 12px; }
.inventory-table td { padding: 12px 16px; border-bottom: 1px solid #e5e7eb; color: #1f2937; }
.inventory-table tbody tr:hover { background: #f9fafb; }
.inventory-table tbody tr.row-disabled { background: #f3f4f6; }
.inventory-row { cursor: pointer; }
.col-checkbox { width: 40px; text-align: center; }
.col-id { width: 60px; }
.col-code, .col-spec { width: 120px; }
.col-name { min-width: 120px; max-width: 180px; overflow-wrap: anywhere; }
.col-warehouse, .col-category { min-width: 100px; }
.col-stock { min-width: 100px; }
.col-unit { width: 60px; }
.col-min-stock, .col-max-stock { width: 90px; }
.col-status, .col-product-status { min-width: 90px; white-space: nowrap; }
.col-update-time { min-width: 140px; white-space: nowrap; }
.col-attributes, .col-price, .col-amount, .col-notes { min-width: 120px; }
.col-stock, .col-min-stock, .col-max-stock, .col-price, .col-amount { text-align: right !important; font-variant-numeric: tabular-nums; }
.attribute-row { padding: 4px 0; }
.col-notes { max-width: 200px; overflow-wrap: anywhere; }
.product-link { color: #3b82f6; text-decoration: none; }
.product-link:hover { text-decoration: underline; }
.store-name { display: block; margin-top: 4px; font-size: 12px; color: #9ca3af; }
.stock-value { font-weight: 600; padding: 4px 8px; border-radius: 4px; white-space: nowrap; }
.stock-value.normal-stock, .status-badge.status-success { color: #059669; background: #d1fae5; }
.stock-value.low-stock, .status-badge.status-warning { color: #d97706; background: #fef3c7; }
.stock-value.out-of-stock, .status-badge.status-danger { color: #dc2626; background: #fee2e2; }
.stock-value.over-stock, .status-badge.status-info { color: #3b82f6; background: #dbeafe; }
.status-badge { display: inline-block; padding: 4px 10px; border-radius: 5px; font-size: 12px; font-weight: 500; }
.status-badge.status-disabled { color: #6b7280; background: #e5e7eb; }
.empty-state { padding: 60px 20px !important; text-align: center; color: #6b7280; }
.empty-state p { margin: 0; }
.load-error { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 12px; color: #dc2626; }
.pagination { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; flex-wrap: wrap; gap: 12px; }
.pagination-left, .pagination-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.page-btn, .btn-jump, .page-size-select { padding: 6px 12px; background: white; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; cursor: pointer; }
.page-btn:hover:not(:disabled), .btn-jump:hover { border-color: #3b82f6; color: #3b82f6; }
.page-jump { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #6b7280; }
.jump-input { width: 50px; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; text-align: center; }
.page-info { font-size: 13px; color: #6b7280; }
.col-actions { min-width: 128px; }
.raw-material-mode .col-actions { min-width: 158px; }
.row-actions { display: flex; gap: 6px; white-space: nowrap; }
.btn-action { display: inline-flex; width: 30px; height: 30px; align-items: center; justify-content: center; padding: 0; border: 1px solid #d1d5db; border-radius: 3px; cursor: pointer; background: white; }
.btn-action.btn-edit { color: #3b82f6; border-color: #3b82f6; }
.btn-action.btn-edit:hover { background: #3b82f6; color: white; }
.btn-action.btn-delete { color: #dc2626; border-color: #fecaca; }
.btn-action.btn-delete:hover:not(:disabled) { background: #fef2f2; }
@media (max-width: 1000px) {
  .stats-cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 700px) {
  .search-bar, .table-toolbar, .pagination { padding: 12px; }
  .search-field { flex: 1 1 200px; max-width: 100%; }
  .store-tabs, .status-tabs { max-width: 100%; flex-wrap: wrap; }
  .status-filter { max-width: 100%; flex-wrap: wrap; }
  .action-buttons { width: 100%; margin-left: 0; }
  .stat-card { padding: 12px; gap: 8px; }
  .stat-icon { width: 32px; height: 32px; }
  .stat-value { font-size: 20px; }
}
</style>
