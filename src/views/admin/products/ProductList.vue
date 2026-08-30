<template>
  <div class="product-list-page">
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

      <button class="btn-filter" @click="toggleFilter">
        <span class="icon">▼</span> 筛选
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
        <label>规格型号</label>
        <input
          v-model="filters.specification"
          type="text"
          placeholder="请输入规格型号"
          class="search-input"
        />
      </div>

      <div class="search-group checkbox-group">
        <input type="checkbox" id="showOnlyUsed" v-model="filters.showOnlyUsed" />
        <label for="showOnlyUsed">显示停用</label>
      </div>

      <div class="action-buttons">
        <button class="btn-new" @click="handleNew">新增</button>
        <button class="btn-batch-delete" @click="handleBatchDelete">批量删除</button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-container">
      <table class="product-table">
        <thead>
          <tr>
            <th class="col-checkbox">
              <input type="checkbox" v-model="selectAll" @change="handleSelectAll" />
            </th>
            <th class="col-name sortable" @click="handleSort('name')">
              商品名称
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-code sortable" @click="handleSort('code')">
              规格型号
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-stock">当前库存</th>
            <th class="col-unit sortable" @click="handleSort('unit')">
              单位
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-price sortable" @click="handleSort('price')">
              零售价格
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-category sortable" @click="handleSort('category')">
              商品分类
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-team">默认仓库</th>
            <th class="col-notes">备注信息</th>
            <th class="col-actions">相关操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in paginatedProducts" :key="product.id" :class="{ 'row-disabled': product.disabled }">
            <td class="col-checkbox">
              <input type="checkbox" v-model="product.selected" />
            </td>
            <td class="col-name">
              <a href="#" class="product-link" @click.prevent="handleView(product)">{{ product.name }}</a>
            </td>
            <td class="col-code">{{ product.specification || '-' }}</td>
            <td class="col-stock">{{ product.stock || '-' }}</td>
            <td class="col-unit">{{ product.unit || '-' }}</td>
            <td class="col-price">{{ product.price ? product.price.toFixed(2) : '0.00' }}</td>
            <td class="col-category">{{ product.category || '-' }}</td>
            <td class="col-team">{{ product.warehouse || '-' }}</td>
            <td class="col-notes">{{ product.notes || '-' }}</td>
            <td class="col-actions">
              <button class="btn-action btn-edit" @click="handleCopy(product)">修改</button>
              <button class="btn-action btn-copy" @click="handleCopyProduct(product)">复制</button>
            </td>
          </tr>

          <tr v-if="products.length === 0">
            <td colspan="10" class="empty-state">
              <div class="empty-content">
                <span class="empty-icon">📦</span>
                <p>暂无商品数据</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <div class="pagination-left">
        <button class="page-btn" :disabled="currentPage === 1" @click="goToPage(1)">1</button>
        <button class="page-btn" :disabled="currentPage === 1" @click="prevPage">2</button>
        <button class="page-btn next-btn" :disabled="currentPage >= totalPages" @click="nextPage">›</button>
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
        <span class="page-info">共 {{ totalProducts }} 条</span>
        <select v-model.number="pageSize" class="page-size-select" @change="handlePageSizeChange">
          <option :value="30">30 条/页</option>
          <option :value="50">50 条/页</option>
          <option :value="100">100 条/页</option>
        </select>
      </div>
    </div>

    <!-- 商品表单弹窗 -->
    <ProductFormModal ref="productFormModal" @save="handleSaveProduct" @refresh="loadProducts" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ProductFormModal from '@/components/admin/ProductFormModal.vue'
import request from '@/api/request'

// 筛选条件
const filters = ref({
  productName: '',
  productCode: '',
  specification: '',
  showOnlyUsed: false
})

const selectedStoreId = ref(null) // 选中的门店ID，null表示全部

// 数据
const products = ref([])
const allStores = ref([])
const allWarehouses = ref([])
const allUnits = ref([])
const selectAll = ref(false)
const currentPage = ref(1)
const pageSize = ref(30)
const jumpPage = ref(1)
const productFormModal = ref(null)

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
    if (response && Array.isArray(response)) {
      allUnits.value = response
    }
  } catch (error) {
    console.error('加载单位失败:', error)
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
      // 处理商品数据，添加显示所需的字段
      products.value = response.map(product => {
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
        const unitName = unit ? unit.name : '无'

        // 查找门店名称
        const storeNames = product.storeIds?.map(storeId => {
          const store = allStores.value.find(s => s.id === storeId)
          return store ? store.name : ''
        }).filter(name => name).join(', ') || '无'

        return {
          ...product,
          selected: false,
          warehouse: warehouseName,
          category: categoryName,
          unit: unitName,
          stores: storeNames,
          stock: 0, // 库存需要从库存表获取
          price: product.attributeCombinations?.[0]?.retailPrice || 0
        }
      })
    }
  } catch (error) {
    console.error('加载商品列表失败:', error)
  }
}

// 计算属性
const totalProducts = computed(() => filteredProducts.value.length)
const totalPages = computed(() => Math.ceil(totalProducts.value / pageSize.value))

// 过滤后的商品列表
const filteredProducts = computed(() => {
  let result = products.value

  // 按商品名称筛选
  if (filters.value.productName) {
    result = result.filter(p =>
      p.name.toLowerCase().includes(filters.value.productName.toLowerCase())
    )
  }

  // 按商品编号筛选
  if (filters.value.productCode) {
    result = result.filter(p =>
      p.code && p.code.toLowerCase().includes(filters.value.productCode.toLowerCase())
    )
  }

  // 按规格型号筛选
  if (filters.value.specification) {
    result = result.filter(p =>
      p.specification && p.specification.toLowerCase().includes(filters.value.specification.toLowerCase())
    )
  }

  // 按门店筛选（单选）
  if (selectedStoreId.value !== null) {
    result = result.filter(p =>
      p.storeIds && p.storeIds.includes(selectedStoreId.value)
    )
  }

  // 按状态筛选
  if (!filters.value.showOnlyUsed) {
    result = result.filter(p => p.enabled !== false)
  }

  return result
})

// 分页后的商品列表
const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredProducts.value.slice(start, end)
})

// 切换门店选择
const toggleStoreSelection = (storeId) => {
  const index = selectedStoreIds.value.indexOf(storeId)
  if (index > -1) {
    selectedStoreIds.value.splice(index, 1)
  } else {
    selectedStoreIds.value.push(storeId)
  }
}

// 方法
const handleSearch = () => {
  currentPage.value = 1 // 重置到第一页
}

const toggleFilter = () => {
  console.log('筛选')
}

const handleBatch = () => {
  console.log('批量操作')
}

const handleBatchDelete = async () => {
  const selectedProducts = products.value.filter(p => p.selected)
  if (selectedProducts.length === 0) {
    alert('请先选择要删除的商品')
    return
  }

  if (!confirm(`确定要删除选中的 ${selectedProducts.length} 个商品吗？`)) {
    return
  }

  try {
    // 批量删除
    const deletePromises = selectedProducts.map(product =>
      request({
        url: `/products/${product.id}`,
        method: 'DELETE'
      })
    )

    await Promise.all(deletePromises)
    alert('删除成功')
    await loadProducts()
  } catch (error) {
    alert('删除失败：' + (error.response?.data?.message || error.message))
  }
}

const handleSelectAll = () => {
  paginatedProducts.value.forEach(p => {
    p.selected = selectAll.value
  })
}

const handleNew = () => {
  if (productFormModal.value) {
    productFormModal.value.open()
  }
}

const handleSaveProduct = async (productData) => {
  // 商品已通过表单API保存，这里只需要刷新列表
  await loadProducts()
}

const handleSettings = () => {
  console.log('设置')
}

const handleSort = (field) => {
  console.log('排序', field)
}

const handleView = (product) => {
  console.log('查看', product)
}

const handleCopy = (product) => {
  console.log('修改', product)
}

const handleCopyProduct = (product) => {
  console.log('复制', product)
}

const handleDelete = (product) => {
  console.log('删除', product)
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
  // 加载基础数据
  await loadStores()
  await loadWarehouses()
  await loadUnits()
  // 加载商品列表
  await loadProducts()
})
</script>

<style scoped>
.product-list-page {
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

.search-input {
  width: 160px;
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.search-input::placeholder {
  color: #9ca3af;
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

.btn-search,
.btn-filter,
.btn-batch,
.btn-new,
.btn-import,
.btn-export {
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

.btn-new {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.btn-new:hover {
  background: #059669;
}

.btn-batch-delete {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fca5a5;
  color: white;
}

.btn-batch-delete:hover {
  background: #f87171;
}

/* 门店滑块样式 */
.store-slider {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.store-slider > label {
  font-size: 14px;
  color: #6b7280;
  white-space: nowrap;
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

.btn-search {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.btn-search:hover {
  background: #2563eb;
}

.btn-filter:hover,
.btn-batch:hover {
  background: #f3f4f6;
}

.btn-new {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.btn-new:hover {
  background: #059669;
}

.btn-import,
.btn-export {
  color: #374151;
}

.btn-import:hover,
.btn-export:hover {
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

/* 设置行 */
.settings-row {
  padding: 8px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
}

.btn-settings {
  padding: 4px 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

.btn-settings:hover {
  background: #e5e7eb;
  border-radius: 4px;
}

/* 表格 */
.table-container {
  background: white;
  overflow-x: auto;
}

.product-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.product-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.product-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}

.product-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.product-table th.sortable:hover {
  background: #f3f4f6;
}

.sort-icon {
  margin-left: 4px;
  color: #9ca3af;
  font-size: 12px;
}

.product-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
}

.product-table tbody tr:hover {
  background: #f9fafb;
}

.product-table tbody tr.row-disabled {
  opacity: 0.6;
  background: #f3f4f6;
}

/* 列宽 */
.col-checkbox {
  width: 40px;
  text-align: center;
}

.col-name {
  min-width: 100px;
  max-width: 150px;
}

.col-code {
  width: 120px;
}

.col-stock {
  width: 100px;
  text-align: center;
}

.col-unit {
  width: 80px;
  text-align: center;
}

.col-price {
  width: 100px;
  text-align: right;
}

.col-category {
  width: 120px;
}

.col-team {
  width: 100px;
}

.col-notes {
  width: 120px;
}

.col-actions {
  width: 180px;
}

.product-link {
  color: #3b82f6;
  text-decoration: none;
}

.product-link:hover {
  text-decoration: underline;
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

.btn-action.btn-copy {
  color: #3b82f6;
  border-color: #3b82f6;
}

.btn-action.btn-copy:hover {
  background: #3b82f6;
  color: white;
}

.btn-action.btn-delete {
  color: #6b7280;
  border-color: #d1d5db;
}

.btn-action.btn-delete:hover {
  background: #f3f4f6;
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
  border-top: 1px solid #e5e7eb;
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

.page-btn.next-btn {
  font-size: 18px;
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
</style>
