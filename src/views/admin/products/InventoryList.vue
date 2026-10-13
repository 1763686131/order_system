<template>
  <div class="inventory-list-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <label class="search-field">
        <span class="sr-only">搜索商品</span>
        <Search class="search-icon" :size="16" aria-hidden="true" />
        <input
          v-model.trim="filters.productName"
          type="search"
          placeholder="搜索名称、编号或规格"
        />
      </label>

      <span class="filter-label">门店</span>
      <div class="store-tabs">
        <div
          :class="['store-tab', { active: selectedStoreId === null }]"
          @click="selectedStoreId = null"
        >
          全部门店
        </div>
        <div
          v-for="store in allStores"
          :key="store.id"
          :class="['store-tab', { active: selectedStoreId === store.id }]"
          @click="selectedStoreId = store.id"
        >
          {{ store.name }}
        </div>
      </div>

      <label class="filter-field">
        <span>分类</span>
        <select v-model="filters.categoryId">
          <option :value="null">全部分类</option>
          <option v-for="category in allCategories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
      </label>

      <label class="filter-field">
        <span>仓库</span>
        <select v-model="filters.warehouseId">
          <option :value="null">全部仓库</option>
          <option v-for="warehouse in allWarehouses" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
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

      <label class="filter-field">
        <span>商品状态</span>
        <select v-model="filters.productStatus">
          <option value="all">全部状态</option>
          <option value="enabled">启用</option>
          <option value="disabled">停用</option>
        </select>
      </label>

      <div class="action-buttons">
        <button class="btn btn-secondary" type="button" @click="resetFilters">
          <RotateCcw :size="16" aria-hidden="true" />
          重置筛选
        </button>
        <button class="btn btn-secondary icon-button" type="button" title="刷新" aria-label="刷新" @click="loadInventory">
          <RefreshCw :size="16" aria-hidden="true" />
        </button>
        <button class="btn btn-secondary" type="button" @click="handleExport">
          <Download :size="16" aria-hidden="true" />
          导出
        </button>
        <button v-if="canManageProducts" class="btn btn-danger" type="button" :disabled="selectedCount === 0 || deleting" @click="handleBatchDelete">
          <Trash2 :size="16" aria-hidden="true" />
          批量删除
        </button>
        <button v-if="canManageProducts" class="btn btn-primary" type="button" @click="handleNew">
          <Plus :size="16" aria-hidden="true" />
          新增商品
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background: #dbeafe;">
          <span style="color: #2563eb;">📦</span>
        </div>
        <div class="stat-content">
          <div class="stat-label">商品总数</div>
          <div class="stat-value">{{ totalProducts }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #d1fae5;">
          <span style="color: #10b981;">✓</span>
        </div>
        <div class="stat-content">
          <div class="stat-label">库存正常</div>
          <div class="stat-value">{{ normalStockCount }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #fef3c7;">
          <span style="color: #f59e0b;">⚠</span>
        </div>
        <div class="stat-content">
          <div class="stat-label">库存预警</div>
          <div class="stat-value">{{ lowStockCount }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #fee2e2;">
          <span style="color: #ef4444;">!</span>
        </div>
        <div class="stat-content">
          <div class="stat-label">库存不足</div>
          <div class="stat-value">{{ outOfStockCount }}</div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table class="inventory-table">
        <thead>
          <tr>
            <th class="col-checkbox">
              <input
                type="checkbox"
                :checked="allPageSelected"
                :indeterminate="somePageSelected"
                :disabled="!canManageProducts || paginatedInventory.length === 0"
                aria-label="选择本页全部商品"
                @change="handleSelectAll($event.target.checked)"
              />
            </th>
            <th class="col-id">ID</th>
            <th class="col-code sortable" @click="handleSort('code')">
              商品编号
              <span class="sort-icon">{{ getSortIcon('code') }}</span>
            </th>
            <th class="col-name sortable" @click="handleSort('name')">
              商品名称
              <span class="sort-icon">{{ getSortIcon('name') }}</span>
            </th>
            <th class="col-spec">规格型号</th>
            <th class="col-warehouse">仓库</th>
            <th class="col-category">分类</th>
            <th class="col-stock sortable" @click="handleSort('stock')">
              当前库存
              <span class="sort-icon">{{ getSortIcon('stock') }}</span>
            </th>
            <th class="col-unit">单位</th>
            <th class="col-attributes">商品属性</th>
            <th class="col-price">零售价格</th>
            <th class="col-min-stock">最低库存</th>
            <th class="col-max-stock">最高库存</th>
            <th class="col-status">库存状态</th>
            <th class="col-product-status">商品状态</th>
            <th class="col-notes">备注信息</th>
            <th class="col-update-time sortable" @click="handleSort('updateTime')">
              更新时间
              <span class="sort-icon">{{ getSortIcon('updateTime') }}</span>
            </th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in paginatedInventory" :key="item.id" :class="{ 'row-disabled': item.enabled === false }">
            <td class="col-checkbox">
              <input type="checkbox" v-model="item.selected" :disabled="!canManageProducts" :aria-label="`选择商品${item.productName}`" />
            </td>
            <td class="col-id">{{ item.id }}</td>
            <td class="col-code">{{ item.productCode || '-' }}</td>
            <td class="col-name">
              <a v-if="canManageProducts" href="#" class="product-link" @click.prevent="handleEdit(item)">
                {{ item.productName }}
              </a>
              <span v-else>{{ item.productName }}</span>
            </td>
            <td class="col-spec">{{ item.specification || '-' }}</td>
            <td class="col-warehouse">{{ item.warehouseName || '-' }}</td>
            <td class="col-category">{{ item.categoryName || '-' }}</td>
            <td class="col-stock">
              <span :class="['stock-value', getStockClass(item)]">
                {{ item.stock }}
              </span>
            </td>
            <td class="col-unit">{{ item.unit || '-' }}</td>
            <td class="col-attributes">
              <template v-if="item.enableAttributes && item.attributeCombinations?.length">
                <div v-for="(combination, index) in item.attributeCombinations" :key="index" class="attribute-row">
                  {{ combination.name }}
                </div>
              </template>
              <span v-else>-</span>
            </td>
            <td class="col-price">
              <template v-if="item.enableAttributes && item.attributeCombinations?.length">
                <div v-for="(combination, index) in item.attributeCombinations" :key="index" class="attribute-row">
                  {{ formatPrice(combination.retailPrice) }} 元
                </div>
              </template>
              <span v-else>{{ formatPrice(item.attributeCombinations?.[0]?.retailPrice || item.price) }} 元</span>
            </td>
            <td class="col-min-stock">{{ item.minStock || '-' }}</td>
            <td class="col-max-stock">{{ item.maxStock || '-' }}</td>
            <td class="col-status">
              <span :class="['status-badge', getStockStatusClass(item)]">
                {{ getStockStatusText(item) }}
              </span>
            </td>
            <td class="col-product-status">
              <span :class="['status-badge', item.enabled === false ? 'status-disabled' : 'status-success']">
                {{ item.enabled === false ? '停用' : '启用' }}
              </span>
            </td>
            <td class="col-notes" :title="item.notes">{{ item.notes || '-' }}</td>
            <td class="col-update-time">{{ formatDateTime(item.updateTime) }}</td>
            <td class="col-actions">
              <div v-if="canManageProducts" class="row-actions">
                <button class="btn-action btn-edit" type="button" title="修改商品" :aria-label="`修改商品${item.productName}`" @click="handleEdit(item)">
                  <Pencil :size="15" aria-hidden="true" />
                </button>
                <button class="btn-action btn-edit" type="button" title="复制商品" :aria-label="`复制商品${item.productName}`" @click="handleCopy(item)">
                  <Copy :size="15" aria-hidden="true" />
                </button>
                <button class="btn-action btn-delete" type="button" title="删除商品" :aria-label="`删除商品${item.productName}`" :disabled="deleting" @click="deleteProducts([item])">
                  <Trash2 :size="15" aria-hidden="true" />
                </button>
              </div>
              <span v-else>-</span>
            </td>
          </tr>

          <tr v-if="filteredInventory.length === 0">
            <td colspan="18" class="empty-state">
              <div class="empty-content">
                <span class="empty-icon">📊</span>
                <p>暂无库存数据</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <div class="pagination-left">
        <button class="page-btn" :disabled="currentPage === 1" @click="goToPage(1)">首页</button>
        <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">上一页</button>
        <button class="page-btn next-btn" :disabled="currentPage >= totalPages" @click="nextPage">下一页</button>
        <span class="page-jump">
          到第
          <input
            type="number"
            v-model.number="jumpPage"
            @keyup.enter="jumpToPage"
            class="jump-input"
          />
          页
        </span>
        <button class="btn-jump" @click="jumpToPage">确定</button>
      </div>

      <div class="pagination-right">
        <span class="page-info">共 {{ totalInventory }} 条</span>
        <select v-model.number="pageSize" class="page-size-select" @change="handlePageSizeChange">
          <option :value="30">30 条/页</option>
          <option :value="50">50 条/页</option>
          <option :value="100">100 条/页</option>
        </select>
      </div>
    </div>

    <ProductFormModal
      ref="productFormModal"
      mode="finished-product"
      @save="handleProductSaved"
      @refresh="handleProductSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Copy, Download, Pencil, Plus, RefreshCw, RotateCcw, Search, Trash2 } from '@lucide/vue'
import request from '@/api/request'
import { getMeasurementUnits } from '@/utils/unitHelper'
import ProductFormModal from '@/components/admin/ProductFormModal.vue'
import { useUserStore } from '@/stores/user'
import { ADMIN_ROUTE_BRANCH_PERMISSIONS } from '@/utils/adminAccess'

const userStore = useUserStore()
const canManageProducts = computed(() => userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.LIST))

// 筛选条件
const filters = ref({
  productName: '',
  productCode: '',
  warehouseId: null,
  categoryId: null,
  status: 'all',
  productStatus: 'all',
  lowStockOnly: false
})

const selectedStoreId = ref(null)

// 状态选项
const statusOptions = [
  { value: 'all', label: '全部' },
  { value: 'normal', label: '正常' },
  { value: 'low', label: '预警' },
  { value: 'out', label: '缺货' }
]

// 数据
const inventory = ref([])
const allStores = ref([])
const allWarehouses = ref([])
const allUnits = ref([])
const currentPage = ref(1)
const pageSize = ref(30)
const jumpPage = ref(1)

// 排序相关
const sortKey = ref('')
const sortDirection = ref('asc') // 'asc' 或 'desc'

const productFormModal = ref(null)
const deleting = ref(false)

// 加载门店数据
const loadStores = async () => {
  try {
    const response = await request({
      url: '/stores',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      allStores.value = response
    }
  } catch (error) {
    console.error('加载门店失败:', error)
  }
}

// 加载仓库数据
const loadWarehouses = async () => {
  try {
    const response = await request({
      url: '/warehouses',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      allWarehouses.value = response
    }
  } catch (error) {
    console.error('加载仓库失败:', error)
  }
}

// 加载单位数据
const loadUnits = async () => {
  try {
    const response = await request({
      url: '/products/units',
      method: 'GET'
    })
    allUnits.value = getMeasurementUnits(response)
  } catch (error) {
    console.error('加载单位失败:', error)
  }
}

// 加载库存数据
const loadInventory = async () => {
  try {
    // 从 /api/products/inventory 获取带库存信息的商品数据
    const response = await request({
      url: '/products/inventory',
      method: 'GET'
    })

    if (response && Array.isArray(response)) {
      const selectedIds = new Set(inventory.value.filter(item => item.selected).map(item => item.id))
      inventory.value = response.map(product => {
        // 查找仓库名称
        const warehouse = allWarehouses.value.find(w => w.id === product.warehouseId)
        const warehouseName = warehouse ? warehouse.name : '无'

        // 查找分类名称
        let categoryName = '无'
        const categoryId = product.categoryId || product.category
        if (warehouse && categoryId) {
          const category = warehouse.categories?.find(c => c.id === categoryId)
          categoryName = category ? category.name : '无'
        }

        // 查找单位名称
        const unit = allUnits.value.find(u => u.id === product.unitId)
        const unitName = unit ? unit.name : '件'

        return {
          ...product,
          selected: selectedIds.has(product.id),
          id: product.id,
          productId: product.id,
          productCode: product.code || '',
          productName: product.name || '',
          specification: product.specification || '',
          warehouseId: product.warehouseId,
          warehouseName: warehouseName,
          categoryName: categoryName,
          stock: Number(product.stock || 0),
          unit: unitName,
          minStock: Number(product.minStock || 0),
          maxStock: Number(product.maxStock || 0),
          storeIds: product.storeIds || [],
          updateTime: product.inventoryUpdatedAt || product.updatedAt || product.createdAt || ''
        }
      })
    }
  } catch (error) {
    console.error('加载库存数据失败:', error)
  }
}

// 计算属性
const totalInventory = computed(() => filteredInventory.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalInventory.value / pageSize.value)))
const selectedCount = computed(() => inventory.value.filter(item => item.selected).length)
const allPageSelected = computed(() => (
  paginatedInventory.value.length > 0 && paginatedInventory.value.every(item => item.selected)
))
const somePageSelected = computed(() => (
  !allPageSelected.value && paginatedInventory.value.some(item => item.selected)
))

// 获取所有分类
const allCategories = computed(() => {
  const categories = []
  const categoryMap = new Map()

  allWarehouses.value.forEach(warehouse => {
    if (warehouse.categories && Array.isArray(warehouse.categories)) {
      warehouse.categories.forEach(category => {
        if (!categoryMap.has(category.id)) {
          categoryMap.set(category.id, category)
          categories.push(category)
        }
      })
    }
  })

  return categories
})

// 库存统计
const totalProducts = computed(() => filteredInventory.value.length)
const normalStockCount = computed(() =>
  filteredInventory.value.filter(item => getStockStatus(item) === 'normal').length
)
const lowStockCount = computed(() =>
  filteredInventory.value.filter(item => getStockStatus(item) === 'low').length
)
const outOfStockCount = computed(() =>
  filteredInventory.value.filter(item => getStockStatus(item) === 'out').length
)

// 过滤后的库存列表
const filteredInventory = computed(() => {
  let result = inventory.value

  // 按商品名称筛选
  if (filters.value.productName) {
    result = result.filter(item =>
      item.productName.toLowerCase().includes(filters.value.productName.toLowerCase()) ||
      (item.productCode && item.productCode.toLowerCase().includes(filters.value.productName.toLowerCase())) ||
      (item.specification && item.specification.toLowerCase().includes(filters.value.productName.toLowerCase()))
    )
  }

  // 按商品编号筛选
  if (filters.value.productCode) {
    result = result.filter(item =>
      item.productCode && item.productCode.toLowerCase().includes(filters.value.productCode.toLowerCase())
    )
  }

  // 按仓库筛选
  if (filters.value.warehouseId) {
    result = result.filter(item => item.warehouseId === filters.value.warehouseId)
  }

  // 按分类筛选
  if (filters.value.categoryId) {
    result = result.filter(item => (
      item.categoryId === filters.value.categoryId || item.category === filters.value.categoryId
    ))
  }

  // 按门店筛选
  if (selectedStoreId.value !== null) {
    result = result.filter(item =>
      item.storeIds && item.storeIds.includes(selectedStoreId.value)
    )
  }

  // 按状态筛选
  if (filters.value.status !== 'all') {
    result = result.filter(item => {
      const stockStatus = getStockStatus(item)
      return stockStatus === filters.value.status
    })
  }

  if (filters.value.productStatus !== 'all') {
    result = result.filter(item => filters.value.productStatus === 'disabled'
      ? item.enabled === false
      : item.enabled !== false)
  }

  // 仅显示低库存
  if (filters.value.lowStockOnly) {
    result = result.filter(item => item.stock < item.minStock)
  }

  // 排序
  if (sortKey.value) {
    result = [...result].sort((a, b) => {
      let aValue = a[sortKey.value]
      let bValue = b[sortKey.value]

      // 特殊处理不同字段
      if (sortKey.value === 'name') {
        aValue = a.productName
        bValue = b.productName
      } else if (sortKey.value === 'code') {
        aValue = a.productCode
        bValue = b.productCode
      } else if (sortKey.value === 'updateTime') {
        aValue = new Date(a.updateTime).getTime()
        bValue = new Date(b.updateTime).getTime()
      }

      // 比较
      let comparison = 0
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue
      } else {
        comparison = String(aValue || '').localeCompare(String(bValue || ''), 'zh-CN')
      }

      return sortDirection.value === 'asc' ? comparison : -comparison
    })
  }

  return result
})

// 获取库存状态
const getStockStatus = (item) => {
  if (item.stock === 0) return 'out'
  if (item.stock < item.minStock) return 'low'
  return 'normal'
}

// 分页后的库存列表
const paginatedInventory = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredInventory.value.slice(start, end)
})

// 获取库存状态类名
const getStockClass = (item) => {
  if (item.stock === 0) return 'out-of-stock'
  if (item.stock < item.minStock) return 'low-stock'
  if (item.maxStock > 0 && item.stock > item.maxStock) return 'over-stock'
  return 'normal-stock'
}

const getStockStatusClass = (item) => {
  if (item.stock === 0) return 'status-danger'
  if (item.stock < item.minStock) return 'status-warning'
  if (item.maxStock > 0 && item.stock > item.maxStock) return 'status-info'
  return 'status-success'
}

const getStockStatusText = (item) => {
  if (item.stock === 0) return '缺货'
  if (item.stock < item.minStock) return '库存不足'
  if (item.maxStock > 0 && item.stock > item.maxStock) return '库存过高'
  return '正常'
}

// 格式化日期时间
const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  const date = new Date(datetime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 方法
const handleExport = () => {
  alert('导出功能开发中...')
}

const resetFilters = () => {
  filters.value.productName = ''
  filters.value.productCode = ''
  filters.value.warehouseId = null
  filters.value.categoryId = null
  filters.value.status = 'all'
  filters.value.productStatus = 'all'
  filters.value.lowStockOnly = false
  selectedStoreId.value = null
  sortKey.value = ''
  sortDirection.value = 'asc'
}

const formatPrice = value => Number(value || 0).toLocaleString('zh-CN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
})

const handleSelectAll = selected => {
  paginatedInventory.value.forEach(item => {
    item.selected = selected
  })
}

const handleNew = () => {
  if (!canManageProducts.value) return
  productFormModal.value?.open(selectedStoreId.value === null
    ? null
    : { storeIds: [selectedStoreId.value] })
}

// 表单内部会修改数组和对象，使用副本避免取消编辑时污染列表。
const handleEdit = item => {
  if (!canManageProducts.value) return
  productFormModal.value?.open(JSON.parse(JSON.stringify(item)))
}

const handleCopy = item => {
  if (!canManageProducts.value) return
  const copy = JSON.parse(JSON.stringify(item))
  delete copy.id
  productFormModal.value?.open(copy)
}

const handleProductSaved = async () => {
  await Promise.all([loadWarehouses(), loadUnits()])
  await loadInventory()
}

const deleteProducts = async items => {
  if (!canManageProducts.value || !items.length || deleting.value) return
  if (!window.confirm(`确定要删除选中的 ${items.length} 个商品吗？`)) return
  deleting.value = true
  try {
    const results = await Promise.allSettled(items.map(item => request({
      url: `/products/${item.productId}`,
      method: 'DELETE'
    })))
    await loadInventory()
    const failed = results.filter(result => result.status === 'rejected')
    if (failed.length) {
      const error = failed[0].reason
      window.alert(`${failed.length} 个商品删除失败：${error.response?.data?.message || error.message}`)
    }
  } finally {
    deleting.value = false
  }
}

const handleBatchDelete = () => {
  return deleteProducts(inventory.value.filter(item => item.selected))
}

const handleSort = (field) => {
  if (sortKey.value === field) {
    // 如果点击同一列，切换排序方向
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    // 如果点击不同列，设置新的排序键并默认升序
    sortKey.value = field
    sortDirection.value = 'asc'
  }
}

// 获取排序图标
const getSortIcon = (field) => {
  if (sortKey.value !== field) {
    return '⇅' // 未排序
  }
  return sortDirection.value === 'asc' ? '↑' : '↓'
}

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}

const goToPage = (page) => {
  currentPage.value = page
}

const jumpToPage = () => {
  if (jumpPage.value >= 1 && jumpPage.value <= totalPages.value) {
    currentPage.value = jumpPage.value
  }
}

const handlePageSizeChange = () => {
  currentPage.value = 1
}

watch([filters, selectedStoreId, pageSize], () => {
  currentPage.value = 1
  jumpPage.value = 1
}, { deep: true })

watch(totalPages, pages => {
  currentPage.value = Math.min(currentPage.value, pages)
})

defineExpose({ reload: loadInventory })

onMounted(async () => {
  await Promise.all([loadStores(), loadWarehouses(), loadUnits()])
  await loadInventory()
})
</script>

<style scoped>
.inventory-list-page {
  padding: 0;
  background: #f5f5f5;
  min-height: 100vh;
}

/* 搜索栏 */
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
  border: 0;
  outline: 0;
  background: transparent;
  color: #1f2937;
  font-size: 14px;
}

.search-icon {
  position: absolute;
  left: 13px;
  color: #94a3b8;
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

.store-tab,
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

.store-tab:hover,
.status-tabs button:hover {
  background: #e5e7eb;
  color: #374151;
}

.store-tab.active,
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

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-wrap: wrap;
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
  white-space: nowrap;
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

.icon-button {
  width: 38px;
  height: 38px;
  padding: 0;
  justify-content: center;
}

.btn-danger {
  color: #fff;
  background: #ef4444;
  border: 1px solid #ef4444;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

button:disabled {
  opacity: 0.55;
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

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 20px;
  background: #f5f5f5;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.stat-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
}

/* 表格 */
.table-container {
  background: white;
  overflow-x: auto;
  margin: 0 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.inventory-table {
  width: 100%;
  min-width: 1900px;
  border-collapse: collapse;
  font-size: 13px;
}

.inventory-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
}

.inventory-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}

.inventory-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.inventory-table th.sortable:hover {
  background: #f3f4f6;
}

.sort-icon {
  margin-left: 4px;
  color: #9ca3af;
  font-size: 12px;
}

.inventory-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
}

.inventory-table tbody tr:hover {
  background: #f9fafb;
}

.inventory-table tbody tr.row-disabled {
  background: #f3f4f6;
  color: #6b7280;
}

/* 列宽 */
.col-checkbox {
  width: 40px;
  text-align: center;
}

.col-id {
  width: 60px;
}

.col-code {
  width: 120px;
}

.col-name {
  min-width: 120px;
  max-width: 180px;
}

.col-spec {
  width: 120px;
}

.col-warehouse {
  width: 100px;
}

.col-category {
  width: 100px;
}

.col-stock {
  width: 100px;
  text-align: center;
}

.col-unit {
  width: 60px;
  text-align: center;
}

.col-min-stock,
.col-max-stock {
  width: 90px;
  text-align: center;
}

.col-status {
  width: 120px;
}

.col-update-time {
  width: 140px;
}

.col-attributes,
.col-price,
.col-notes {
  min-width: 120px;
}

.col-price {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.attribute-row {
  padding: 4px 0;
}

.col-notes {
  max-width: 200px;
  overflow-wrap: anywhere;
}

.product-link {
  color: #3b82f6;
  text-decoration: none;
}

.product-link:hover {
  text-decoration: underline;
}

/* 库存状态样式 */
.stock-value {
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.stock-value.normal-stock {
  color: #10b981;
  background: #d1fae5;
}

.stock-value.low-stock {
  color: #f59e0b;
  background: #fef3c7;
}

.stock-value.out-of-stock {
  color: #ef4444;
  background: #fee2e2;
}

.stock-value.over-stock {
  color: #3b82f6;
  background: #dbeafe;
}

/* 状态标签 */
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.status-success {
  color: #10b981;
  background: #d1fae5;
}

.status-badge.status-warning {
  color: #f59e0b;
  background: #fef3c7;
}

.status-badge.status-danger {
  color: #ef4444;
  background: #fee2e2;
}

.status-badge.status-info {
  color: #3b82f6;
  background: #dbeafe;
}

.status-badge.status-disabled {
  color: #6b7280;
  background: #e5e7eb;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
}

.empty-content p {
  font-size: 14px;
  color: #9ca3af;
  margin: 0;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  margin: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  flex-wrap: wrap;
  gap: 12px;
}

.pagination-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-btn {
  padding: 4px 12px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 36px;
}

.page-btn:hover:not(:disabled) {
  border-color: #3b82f6;
  color: #3b82f6;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-jump {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
}

.jump-input {
  width: 50px;
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
  outline: none;
}

.jump-input:focus {
  border-color: #3b82f6;
}

.btn-jump {
  padding: 4px 12px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-jump:hover {
  background: #f3f4f6;
}

.page-info {
  font-size: 14px;
  color: #6b7280;
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  outline: none;
}

.page-size-select:focus {
  border-color: #3b82f6;
}

.col-actions {
  width: 128px;
}

.row-actions {
  display: flex;
  gap: 6px;
  white-space: nowrap;
}

.btn-action {
  display: inline-flex;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.btn-action.btn-edit {
  color: #3b82f6;
  border-color: #3b82f6;
}

.btn-action.btn-edit:hover {
  background: #3b82f6;
  color: white;
}

.btn-action.btn-delete {
  color: #dc2626;
  border-color: #fecaca;
}

.btn-action.btn-delete:hover:not(:disabled) {
  background: #fef2f2;
}

@media (max-width: 700px) {
  .search-bar {
    padding: 12px;
  }

  .search-field {
    flex: 1 1 200px;
    max-width: 100%;
  }

  .store-tabs {
    max-width: 100%;
    overflow-x: auto;
  }

  .store-tab {
    flex-shrink: 0;
  }

  .action-buttons {
    width: 100%;
    margin-left: 0;
  }

  .stats-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 12px;
    gap: 8px;
  }

  .stat-card {
    padding: 12px;
    gap: 8px;
    min-width: 0;
  }

  .stat-icon {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
  }

  .table-container,
  .pagination {
    margin: 12px;
  }
}
</style>
