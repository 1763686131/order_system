<template>
  <div class="product-list-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <label class="search-field">
        <span class="sr-only">搜索商品</span>
        <span class="search-icon" aria-hidden="true"></span>
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

      <div class="checkbox-group">
        <input type="checkbox" id="showOnlyUsed" v-model="filters.showOnlyUsed" />
        <label for="showOnlyUsed">显示停用</label>
      </div>

      <div class="action-buttons">
        <button class="btn-new" @click="handleNew">新增</button>
        <button
          class="btn-batch-delete"
          :disabled="selectedCount === 0"
          @click="handleBatchDelete"
        >
          批量删除
        </button>
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
            <th class="col-id">ID</th>
            <th class="col-name sortable" @click="handleSort('name')">
              商品名称
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-spec sortable">
              规格型号
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-stock">当前库存</th>
            <th class="col-unit sortable" @click="handleSort('unit')">
              单位
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-code sortable" @click="handleSort('code')">
              编号
              <span class="sort-icon">⇅</span>
            </th>
            <th class="col-attributes">
              商品属性
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
            <td class="col-id">{{ product.id }}</td>
            <td class="col-name">
              <a href="#" class="product-link" @click.prevent="handleView(product)">{{ product.name }}</a>
            </td>
            <td class="col-spec">{{ product.specification || '-' }}</td>
            <td class="col-stock">{{ product.stock || '-' }}</td>
            <td class="col-unit">{{ product.unit || '-' }}</td>
            <td class="col-code">{{ product.code || '-' }}</td>
            <td class="col-attributes">
              <div v-if="product.enableAttributes && product.attributeCombinations && product.attributeCombinations.length > 0">
                <div v-for="(combo, index) in product.attributeCombinations" :key="index" class="attribute-row">
                  {{ combo.name }}
                </div>
              </div>
              <span v-else>-</span>
            </td>
            <td class="col-price">
              <div v-if="product.enableAttributes && product.attributeCombinations && product.attributeCombinations.length > 0">
                <div v-for="(combo, index) in product.attributeCombinations" :key="index" class="price-row">
                  {{ combo.retailPrice ? combo.retailPrice.toFixed(2) : '0.00' }} 元
                </div>
              </div>
              <span v-else>{{ product.price ? product.price.toFixed(2) : '0.00' }} 元</span>
            </td>
            <td class="col-category">{{ product.categoryName || '-' }}</td>
            <td class="col-team">{{ product.warehouseName || '-' }}</td>
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
    <ProductFormModal
      ref="productFormModal"
      mode="finished-product"
      @save="handleSaveProduct"
      @refresh="loadProducts"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ProductFormModal from '@/components/admin/ProductFormModal.vue'
import request from '@/api/request'
import { getMeasurementUnits } from '@/utils/unitHelper'

// 筛选条件
const filters = ref({
  productName: '',
  productCode: '',
  specification: '',
  categoryId: null,
  warehouseId: null,
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
    allUnits.value = getMeasurementUnits(response)
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
          warehouseName: warehouseName,  // 添加仓库名称字段
          categoryName: categoryName,    // 添加分类名称字段
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

// 选中商品数量
const selectedCount = computed(() => {
  return products.value.filter(p => p.selected).length
})

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

// 过滤后的商品列表
const filteredProducts = computed(() => {
  let result = products.value

  // 按商品名称筛选（同时搜索名称、编号、规格）
  if (filters.value.productName) {
    result = result.filter(p =>
      p.name.toLowerCase().includes(filters.value.productName.toLowerCase()) ||
      (p.code && p.code.toLowerCase().includes(filters.value.productName.toLowerCase())) ||
      (p.specification && p.specification.toLowerCase().includes(filters.value.productName.toLowerCase()))
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

  // 按分类筛选
  if (filters.value.categoryId) {
    result = result.filter(p =>
      p.categoryId === filters.value.categoryId || p.category === filters.value.categoryId
    )
  }

  // 按仓库筛选
  if (filters.value.warehouseId) {
    result = result.filter(p =>
      p.warehouseId === filters.value.warehouseId
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
  // 打开编辑弹窗，传入商品数据
  if (productFormModal.value) {
    // 需要将商品数据转换为表单需要的格式
    const formData = {
      id: product.id,
      code: product.code || '',
      name: product.name || '',
      specification: product.specification || '',
      warehouse: product.warehouseId || '',
      category: product.categoryId || product.category || '',
      unitId: product.unitId || null,
      notes: product.notes || '',
      enabled: product.enabled !== false,
      storeIds: product.storeIds || [],
      unitConversions: product.unitConversions || [],
      enableAttributes: product.enableAttributes || false,
      attributeCombinations: product.attributeCombinations || []
    }
    productFormModal.value.open(formData)
  }
}

const handleCopyProduct = (product) => {
  // 打开新增弹窗，填充商品数据（不包含ID）
  if (productFormModal.value) {
    // 复制商品数据，但不包含ID，这样保存时会作为新增
    const formData = {
      // 不传 id，这样会作为新增模式
      code: product.code || '',
      name: product.name || '',
      specification: product.specification || '',
      warehouse: product.warehouseId || '',
      category: product.categoryId || product.category || '',
      unitId: product.unitId || null,
      notes: product.notes || '',
      enabled: product.enabled !== false,
      storeIds: product.storeIds || [],
      unitConversions: product.unitConversions || [],
      enableAttributes: product.enableAttributes || false,
      attributeCombinations: product.attributeCombinations || []
    }
    productFormModal.value.open(formData)
  }
}

const handleDelete = async (product) => {
  if (!confirm(`确定要删除商品"${product.name}"吗？`)) {
    return
  }

  try {
    await request({
      url: `/products/${product.id}`,
      method: 'DELETE'
    })
    alert('删除成功')
    await loadProducts()
  } catch (error) {
    console.error('删除商品失败:', error)
    alert('删除失败：' + (error.response?.data?.message || error.message))
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

.store-tab {
  padding: 8px 16px;
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

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.checkbox-group input[type="checkbox"] {
  cursor: pointer;
}

.checkbox-group label {
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.btn-new {
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
}

.btn-new:hover {
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

.product-code {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.attribute-row {
  padding: 4px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  color: #374151;
}

.attribute-row:last-child {
  border-bottom: none;
}

.price-row {
  padding: 4px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.price-row:last-child {
  border-bottom: none;
}

.product-attributes {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.attribute-tag {
  display: inline-block;
  padding: 2px 8px;
  background: #dbeafe;
  color: #1e40af;
  font-size: 12px;
  border-radius: 4px;
  white-space: nowrap;
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
