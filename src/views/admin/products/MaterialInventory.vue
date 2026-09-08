<template>
  <div class="material-inventory-page">
    <header class="page-header">
      <div>
        <div class="breadcrumb">库存管理 / 原材料库存</div>
        <h1>原材料库存</h1>
        <p>集中查看树脂、助剂、填料等原材料的库存状态。</p>
      </div>

      <div class="header-actions">
        <button class="btn btn-secondary" type="button" @click="resetFilters">
          重置筛选
        </button>
        <button class="btn btn-secondary" type="button" @click="exportInventory">
          <span class="button-icon" aria-hidden="true">↓</span>
          导出
        </button>
        <button class="btn btn-primary" type="button" @click="openAdjustmentModal()">
          <span class="button-icon" aria-hidden="true">+</span>
          库存调整
        </button>
      </div>
    </header>

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
      </div>

      <div class="store-filter">
        <span class="filter-label">所属门店</span>
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
        <span class="filter-result">共 {{ filteredMaterials.length }} 条结果</span>
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
        <button class="refresh-button" type="button" title="刷新模拟数据" @click="refreshData">
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
                <button class="table-action" type="button" @click="openAdjustmentModal(material)">
                  调整库存
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

    <div v-if="adjustmentModal.visible" class="modal-backdrop" @click.self="closeAdjustmentModal">
      <section class="adjustment-modal" role="dialog" aria-modal="true" aria-labelledby="adjustment-title">
        <header class="modal-header">
          <div>
            <span class="modal-eyebrow">本地演示</span>
            <h2 id="adjustment-title">库存调整</h2>
          </div>
          <button class="modal-close" type="button" title="关闭" @click="closeAdjustmentModal">×</button>
        </header>

        <div class="modal-body">
          <label class="modal-field">
            <span>原材料</span>
            <select v-model="adjustmentForm.materialId">
              <option v-for="material in materials" :key="material.id" :value="material.id">
                {{ material.name }} · {{ material.code }}
              </option>
            </select>
          </label>

          <div class="modal-field">
            <span>调整类型</span>
            <div class="adjustment-types">
              <button
                type="button"
                :class="{ active: adjustmentForm.type === 'in' }"
                @click="adjustmentForm.type = 'in'"
              >
                入库增加
              </button>
              <button
                type="button"
                :class="{ active: adjustmentForm.type === 'out' }"
                @click="adjustmentForm.type = 'out'"
              >
                出库减少
              </button>
            </div>
          </div>

          <div class="modal-grid">
            <label class="modal-field">
              <span>调整数量</span>
              <input v-model.number="adjustmentForm.quantity" type="number" min="0" step="0.01" />
            </label>
            <div class="modal-field current-stock-field">
              <span>调整后库存</span>
              <strong>{{ formatNumber(adjustedStockPreview) }} {{ selectedMaterial?.unit || '' }}</strong>
            </div>
          </div>

          <label class="modal-field">
            <span>备注</span>
            <textarea v-model.trim="adjustmentForm.remark" rows="3" placeholder="请输入本次调整原因"></textarea>
          </label>
        </div>

        <footer class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="closeAdjustmentModal">取消</button>
          <button class="btn btn-primary" type="button" @click="saveAdjustment">保存调整</button>
        </footer>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import request from '@/api/request'
import { getMeasurementUnits } from '@/utils/unitHelper'

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

const adjustmentModal = ref({ visible: false })
const adjustmentForm = ref({
  materialId: materials.value[0].id,
  type: 'in',
  quantity: 0,
  remark: ''
})

const selectedMaterial = computed(() => {
  return materials.value.find(item => item.id === Number(adjustmentForm.value.materialId)) || null
})

const adjustedStockPreview = computed(() => {
  if (!selectedMaterial.value) return 0
  const quantity = Number(adjustmentForm.value.quantity) || 0
  return adjustmentForm.value.type === 'in'
    ? selectedMaterial.value.stock + quantity
    : Math.max(0, selectedMaterial.value.stock - quantity)
})

const openAdjustmentModal = (material = null) => {
  adjustmentForm.value = {
    materialId: material?.id || materials.value[0]?.id,
    type: 'in',
    quantity: 0,
    remark: ''
  }
  adjustmentModal.value.visible = true
}

const closeAdjustmentModal = () => {
  adjustmentModal.value.visible = false
}

const saveAdjustment = () => {
  const material = selectedMaterial.value
  const quantity = Number(adjustmentForm.value.quantity)

  if (!material || !quantity || quantity <= 0) {
    window.alert('请选择原材料并填写大于 0 的调整数量')
    return
  }

  material.stock = adjustedStockPreview.value
  material.updatedAt = new Date().toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).replaceAll('/', '-')
  closeAdjustmentModal()
}

onMounted(loadMaterialProducts)
</script>

<style scoped>
.material-inventory-page {
  min-height: 100%;
  padding: 28px 30px 36px;
  color: #172033;
  background: #f6f8fb;
}

.page-header,
.filter-row,
.store-filter,
.table-toolbar,
.table-footer,
.header-actions {
  display: flex;
  align-items: center;
}

.page-header {
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.breadcrumb,
.modal-eyebrow {
  color: #718096;
  font-size: 12px;
  letter-spacing: 0.04em;
}

.page-header h1 {
  margin: 7px 0 6px;
  color: #111827;
  font-size: 26px;
  letter-spacing: 0;
}

.page-header p {
  margin: 0;
  color: #718096;
  font-size: 13px;
}

.header-actions {
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  min-height: 36px;
  padding: 0 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s ease;
}

.btn-secondary {
  color: #4b5563;
  background: #fff;
  border: 1px solid #d8dee8;
}

.btn-secondary:hover {
  border-color: #aeb8c8;
  background: #f9fafb;
}

.btn-primary {
  color: #fff;
  background: #2563eb;
  border: 1px solid #2563eb;
}

.btn-primary:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.button-icon {
  margin-right: 5px;
  font-size: 16px;
  line-height: 0;
}

.filter-panel,
.table-panel {
  background: #fff;
  border: 1px solid #e7ebf1;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(30, 41, 59, 0.04);
}

.filter-panel {
  padding: 16px 18px 12px;
  margin-bottom: 18px;
}

.filter-row {
  gap: 12px;
  flex-wrap: wrap;
}

.search-field,
.filter-field {
  display: flex;
  align-items: center;
  min-height: 36px;
  border: 1px solid #d8dee8;
  border-radius: 6px;
  background: #fff;
}

.search-field {
  flex: 1 1 260px;
  position: relative;
  padding-left: 34px;
}

.search-field input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #1f2937;
  font-size: 13px;
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

.filter-field {
  padding: 0 10px;
  gap: 8px;
}

.filter-field span,
.filter-label {
  color: #64748b;
  font-size: 12px;
  white-space: nowrap;
}

.filter-field select,
.modal-field select,
.modal-field input,
.modal-field textarea {
  border: 0;
  outline: 0;
  color: #1f2937;
  background: transparent;
  font-size: 13px;
}

.filter-field select {
  min-width: 110px;
  height: 34px;
}

.status-filter,
.store-filter {
  gap: 10px;
}

.status-filter {
  display: flex;
  align-items: center;
}

.status-tabs,
.store-tabs,
.adjustment-types {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-tabs button,
.store-tabs button,
.adjustment-types button {
  border: 1px solid transparent;
  border-radius: 5px;
  color: #64748b;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  transition: 0.2s ease;
}

.status-tabs button,
.store-tabs button {
  padding: 7px 10px;
}

.status-tabs button:hover,
.store-tabs button:hover,
.adjustment-types button:hover {
  color: #1d4ed8;
  background: #eff6ff;
}

.status-tabs button.active,
.store-tabs button.active,
.adjustment-types button.active {
  color: #1d4ed8;
  background: #eff6ff;
  border-color: #bfdbfe;
  font-weight: 600;
}

.store-filter {
  display: flex;
  flex-wrap: wrap;
  padding-top: 14px;
  margin-top: 14px;
  border-top: 1px solid #eef1f5;
}

.filter-result {
  margin-left: auto;
  color: #94a3b8;
  font-size: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.stat-card {
  min-height: 110px;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid #e7ebf1;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(30, 41, 59, 0.04);
}

.stat-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #64748b;
  font-size: 13px;
}

.stat-card strong {
  display: block;
  margin: 10px 0 4px;
  color: #111827;
  font-size: 25px;
  font-weight: 700;
}

.stat-card small {
  color: #94a3b8;
  font-size: 11px;
}

.stat-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-size: 12px;
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
}

.table-toolbar {
  justify-content: space-between;
  gap: 16px;
  padding: 17px 18px;
  border-bottom: 1px solid #e7ebf1;
}

.table-toolbar h2 {
  margin: 0 0 4px;
  color: #1f2937;
  font-size: 16px;
}

.table-toolbar span {
  color: #94a3b8;
  font-size: 12px;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 10px;
  color: #64748b;
  border: 1px solid #d8dee8;
  border-radius: 5px;
  background: #fff;
  cursor: pointer;
}

.refresh-button:hover {
  color: #2563eb;
  border-color: #93c5fd;
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
  font-size: 13px;
}

.inventory-table th {
  padding: 12px 14px;
  color: #64748b;
  background: #f8fafc;
  border-bottom: 1px solid #e7ebf1;
  font-size: 12px;
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
}

.inventory-table td {
  padding: 13px 14px;
  color: #334155;
  border-bottom: 1px solid #eef1f5;
  white-space: nowrap;
}

.inventory-table tbody tr:hover {
  background: #fafcff;
}

.sortable {
  cursor: pointer;
}

.sortable:hover {
  color: #2563eb;
}

.sort-indicator {
  margin-left: 4px;
  color: #cbd5e1;
}

.sort-indicator.active {
  color: #2563eb;
}

.number-column {
  text-align: right !important;
}

.code-cell,
.muted-cell {
  color: #64748b !important;
}

.material-name {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.material-name strong {
  color: #1f2937;
  font-weight: 600;
}

.material-name small,
.max-stock {
  color: #94a3b8;
  font-size: 11px;
}

.category-tag {
  display: inline-block;
  padding: 4px 7px;
  color: #475569;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 11px;
}

.stock-number {
  font-size: 14px;
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
  padding: 5px 8px;
  border-radius: 5px;
  background: #f8fafc;
  font-size: 11px;
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
  padding: 5px 9px;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.table-action:hover {
  color: #fff;
  background: #2563eb;
}

.empty-state {
  padding: 58px 20px !important;
  color: #94a3b8 !important;
  text-align: center !important;
}

.empty-title {
  color: #64748b;
  font-weight: 600;
}

.empty-state p {
  margin: 7px 0 0;
  font-size: 12px;
}

.table-footer {
  justify-content: space-between;
  gap: 16px;
  padding: 13px 18px;
  color: #94a3b8;
  font-size: 12px;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination select,
.pagination button {
  min-height: 30px;
  padding: 0 9px;
  color: #64748b;
  background: #fff;
  border: 1px solid #d8dee8;
  border-radius: 4px;
  font-size: 12px;
}

.pagination button {
  cursor: pointer;
}

.pagination button:disabled {
  color: #cbd5e1;
  background: #f8fafc;
  cursor: not-allowed;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.42);
}

.adjustment-modal {
  width: min(520px, 100%);
  overflow: hidden;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.2);
}

.modal-header,
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 17px 20px;
}

.modal-header {
  border-bottom: 1px solid #e7ebf1;
}

.modal-header h2 {
  margin: 4px 0 0;
  color: #1f2937;
  font-size: 18px;
}

.modal-close {
  width: 30px;
  height: 30px;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
}

.modal-close:hover {
  background: #f1f5f9;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.modal-field > span {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.modal-field select,
.modal-field input,
.modal-field textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 10px;
  border: 1px solid #d8dee8;
  border-radius: 5px;
  background: #fff;
}

.modal-field textarea {
  resize: vertical;
}

.modal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.adjustment-types button {
  flex: 1;
  padding: 9px 12px;
  border-color: #d8dee8;
}

.current-stock-field strong {
  min-height: 36px;
  display: flex;
  align-items: center;
  color: #1f2937;
  font-size: 16px;
  font-weight: 700;
}

.modal-footer {
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid #e7ebf1;
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

  .modal-grid {
    grid-template-columns: 1fr;
  }
}
</style>
