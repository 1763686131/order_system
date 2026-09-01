<template>
  <div class="inventory-list-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <div class="search-group store-slider">
        <label>门店</label>
        <div class="store-tabs">
          <div
            :class="['store-tab', { active: selectedStoreId === null }]"
            @click="selectedStoreId = null"
          >
            全部
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
      </div>

      <button class="btn-search" @click="handleSearch">
        <span class="icon">🔍</span> 搜索
      </button>

      <div class="search-group">
        <label>商品名称</label>
        <input
          v-model="filters.productName"
          type="text"
          placeholder="请输入商品名称"
          class="search-input"
        />
      </div>

      <div class="search-group">
        <label>商品编号</label>
        <input
          v-model="filters.productCode"
          type="text"
          placeholder="请输入商品编号"
          class="search-input"
        />
      </div>

      <div class="search-group">
        <label>仓库</label>
        <select v-model="filters.warehouseId" class="search-select">
          <option :value="null">全部仓库</option>
          <option v-for="warehouse in allWarehouses" :key="warehouse.id" :value="warehouse.id">
            {{ warehouse.name }}
          </option>
        </select>
      </div>

      <div class="search-group checkbox-group">
        <input type="checkbox" id="lowStock" v-model="filters.lowStockOnly" />
        <label for="lowStock">仅显示低库存</label>
      </div>

      <div class="action-buttons">
        <button class="btn-new" @click="handleAddInventory">录入库存</button>
        <button class="btn-export" @click="handleExport">导出</button>
        <button class="btn-refresh" @click="handleRefresh">刷新</button>
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
            <th class="col-id">ID</th>
            <th class="col-code sortable" @click="handleSort('code')">
              商品编号
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-name sortable" @click="handleSort('name')">
              商品名称
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-spec">规格型号</th>
            <th class="col-warehouse">仓库</th>
            <th class="col-category">分类</th>
            <th class="col-stock sortable" @click="handleSort('stock')">
              当前库存
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-unit">单位</th>
            <th class="col-min-stock">最低库存</th>
            <th class="col-max-stock">最高库存</th>
            <th class="col-status">库存状态</th>
            <th class="col-update-time sortable" @click="handleSort('updateTime')">
              更新时间
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in paginatedInventory" :key="item.id">
            <td class="col-id">{{ item.id }}</td>
            <td class="col-code">{{ item.productCode || '-' }}</td>
            <td class="col-name">
              <a href="#" class="product-link" @click.prevent="handleView(item)">
                {{ item.productName }}
              </a>
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
            <td class="col-min-stock">{{ item.minStock || '-' }}</td>
            <td class="col-max-stock">{{ item.maxStock || '-' }}</td>
            <td class="col-status">
              <span :class="['status-badge', getStockStatusClass(item)]">
                {{ getStockStatusText(item) }}
              </span>
            </td>
            <td class="col-update-time">{{ formatDateTime(item.updateTime) }}</td>
            <td class="col-actions">
              <button class="btn-action btn-edit" @click="handleEdit(item)">编辑</button>
            </td>
          </tr>

          <tr v-if="filteredInventory.length === 0">
            <td colspan="13" class="empty-state">
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

    <!-- 库存编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ isEditMode ? '编辑库存' : '录入库存' }}</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>

        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>商品名称 <span class="required">*</span></label>
              <select v-model="formData.productId" class="form-input" :disabled="isEditMode">
                <option :value="null">请选择商品</option>
                <option v-for="product in allProducts" :key="product.id" :value="product.id">
                  {{ product.name }} {{ product.code ? `(${product.code})` : '' }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>当前库存 <span class="required">*</span></label>
              <input
                v-model.number="formData.stock"
                type="number"
                min="0"
                class="form-input"
                placeholder="请输入当前库存"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>最低库存</label>
              <input
                v-model.number="formData.minStock"
                type="number"
                min="0"
                class="form-input"
                placeholder="请输入最低库存"
              />
            </div>

            <div class="form-group">
              <label>最高库存</label>
              <input
                v-model.number="formData.maxStock"
                type="number"
                min="0"
                class="form-input"
                placeholder="请输入最高库存"
              />
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-save" @click="handleSave">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

// 筛选条件
const filters = ref({
  productName: '',
  productCode: '',
  warehouseId: null,
  lowStockOnly: false
})

const selectedStoreId = ref(null)

// 数据
const inventory = ref([])
const allStores = ref([])
const allWarehouses = ref([])
const allProducts = ref([])
const allUnits = ref([])
const currentPage = ref(1)
const pageSize = ref(30)
const jumpPage = ref(1)

// 弹窗相关
const showModal = ref(false)
const isEditMode = ref(false)
const formData = ref({
  productId: null,
  stock: 0,
  minStock: 0,
  maxStock: 0
})

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

// 加载商品列表
const loadProducts = async () => {
  try {
    const response = await request({
      url: '/products',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      allProducts.value = response
    }
  } catch (error) {
    console.error('加载商品列表失败:', error)
  }
}

// 加载单位数据
const loadUnits = async () => {
  try {
    const response = await request({
      url: '/products/units',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      allUnits.value = response
    }
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
          id: product.id,
          productId: product.id,
          productCode: product.code || '',
          productName: product.name || '',
          specification: product.specification || '',
          warehouseId: product.warehouseId,
          warehouseName: warehouseName,
          categoryName: categoryName,
          stock: product.stock || 0,
          unit: unitName,
          minStock: product.minStock || 0,
          maxStock: product.maxStock || 0,
          storeIds: product.storeIds || [],
          updateTime: product.inventoryUpdatedAt || product.createdAt || new Date().toISOString()
        }
      })
    }
  } catch (error) {
    console.error('加载库存数据失败:', error)
  }
}

// 计算属性
const totalInventory = computed(() => filteredInventory.value.length)
const totalPages = computed(() => Math.ceil(totalInventory.value / pageSize.value))

// 库存统计
const totalProducts = computed(() => inventory.value.length)
const normalStockCount = computed(() =>
  inventory.value.filter(item => item.stock >= item.minStock && item.stock <= item.maxStock).length
)
const lowStockCount = computed(() =>
  inventory.value.filter(item => item.stock < item.minStock && item.stock > 0).length
)
const outOfStockCount = computed(() =>
  inventory.value.filter(item => item.stock === 0).length
)

// 过滤后的库存列表
const filteredInventory = computed(() => {
  let result = inventory.value

  // 按商品名称筛选
  if (filters.value.productName) {
    result = result.filter(item =>
      item.productName.toLowerCase().includes(filters.value.productName.toLowerCase())
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

  // 按门店筛选
  if (selectedStoreId.value !== null) {
    result = result.filter(item =>
      item.storeIds && item.storeIds.includes(selectedStoreId.value)
    )
  }

  // 仅显示低库存
  if (filters.value.lowStockOnly) {
    result = result.filter(item => item.stock < item.minStock)
  }

  return result
})

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
  if (item.stock > item.maxStock) return 'over-stock'
  return 'normal-stock'
}

const getStockStatusClass = (item) => {
  if (item.stock === 0) return 'status-danger'
  if (item.stock < item.minStock) return 'status-warning'
  if (item.stock > item.maxStock) return 'status-info'
  return 'status-success'
}

const getStockStatusText = (item) => {
  if (item.stock === 0) return '缺货'
  if (item.stock < item.minStock) return '库存不足'
  if (item.stock > item.maxStock) return '库存过高'
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
const handleSearch = () => {
  currentPage.value = 1
}

const handleExport = () => {
  alert('导出功能开发中...')
}

const handleRefresh = async () => {
  await loadInventory()
  alert('刷新成功')
}

const handleSort = (field) => {
  console.log('排序', field)
}

const handleView = (item) => {
  console.log('查看详情', item)
}

// 打开新增弹窗
const handleAddInventory = () => {
  isEditMode.value = false
  formData.value = {
    productId: null,
    stock: 0,
    minStock: 0,
    maxStock: 0
  }
  showModal.value = true
}

// 打开编辑弹窗
const handleEdit = (item) => {
  isEditMode.value = true
  formData.value = {
    productId: item.productId,
    stock: item.stock,
    minStock: item.minStock,
    maxStock: item.maxStock
  }
  showModal.value = true
}

// 关闭弹窗
const closeModal = () => {
  showModal.value = false
  formData.value = {
    productId: null,
    stock: 0,
    minStock: 0,
    maxStock: 0
  }
}

// 保存库存
const handleSave = async () => {
  // 验证
  if (!formData.value.productId) {
    alert('请选择商品')
    return
  }

  try {
    if (isEditMode.value) {
      // 更新库存
      await request({
        url: `/products/inventory/${formData.value.productId}`,
        method: 'PUT',
        data: {
          stock: formData.value.stock || 0,
          minStock: formData.value.minStock || 0,
          maxStock: formData.value.maxStock || 0
        }
      })
      alert('更新成功')
    } else {
      // 新增库存（实际上也是更新）
      await request({
        url: `/products/inventory/${formData.value.productId}`,
        method: 'PUT',
        data: {
          stock: formData.value.stock || 0,
          minStock: formData.value.minStock || 0,
          maxStock: formData.value.maxStock || 0
        }
      })
      alert('录入成功')
    }

    closeModal()
    await loadInventory()
  } catch (error) {
    alert('保存失败：' + (error.response?.data?.message || error.message))
  }
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

onMounted(async () => {
  await loadStores()
  await loadWarehouses()
  await loadProducts()
  await loadUnits()
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
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  flex-wrap: wrap;
}

.search-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-group label {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
}

.search-input,
.search-select {
  width: 160px;
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.search-input:focus,
.search-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.checkbox-group {
  gap: 6px;
}

.checkbox-group input[type="checkbox"] {
  cursor: pointer;
}

.checkbox-group label {
  cursor: pointer;
}

/* 门店滑块 */
.store-slider {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.store-tabs {
  display: flex;
  gap: 8px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}

.store-tab {
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
  white-space: nowrap;
  user-select: none;
}

.store-tab:hover {
  background: #e5e7eb;
  color: #374151;
}

.store-tab.active {
  background: #34d399;
  color: #fff;
  box-shadow: 0 2px 4px rgba(52, 211, 153, 0.3);
}

.btn-search,
.btn-new,
.btn-export,
.btn-refresh {
  padding: 6px 16px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn-search {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.btn-search:hover {
  background: #2563eb;
}

.btn-new {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.btn-new:hover {
  background: #059669;
}

.btn-export:hover,
.btn-refresh:hover {
  background: #f3f4f6;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.icon {
  font-size: 12px;
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

/* 列宽 */
.col-id {
  width: 60px;
}

.col-code {
  width: 120px;
}

.col-name {
  min-width: 150px;
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
  width: 100px;
}

.col-update-time {
  width: 140px;
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
}

.pagination-left {
  display: flex;
  align-items: center;
  gap: 8px;
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

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  background: white;
  border-radius: 8px;
  width: 600px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #111827;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.required {
  color: #ef4444;
}

.form-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.form-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel,
.btn-save {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-save {
  background: #10b981;
  color: white;
}

.btn-save:hover {
  background: #059669;
}

.col-actions {
  width: 100px;
}

.btn-action {
  padding: 4px 12px;
  margin-right: 4px;
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
</style>
