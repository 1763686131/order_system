<template>
  <div class="product-list-page">
    <!-- 搜索栏 -->
    <div class="search-bar">
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

      <button class="btn-search" @click="handleSearch">
        <span class="icon">🔍</span> 搜索
      </button>

      <button class="btn-filter" @click="toggleFilter">
        <span class="icon">▼</span> 筛选
      </button>

      <div class="search-group checkbox-group">
        <input type="checkbox" id="showOnlyUsed" v-model="filters.showOnlyUsed" />
        <label for="showOnlyUsed">显示停用</label>
      </div>

      <div class="action-buttons">
        <button class="btn-batch" @click="handleBatch">批量 ▼</button>
        <button class="btn-new" @click="handleNew">新增</button>
        <button class="btn-import" @click="handleImport">导入</button>
        <button class="btn-export" @click="handleExport">导出</button>
      </div>
    </div>

    <!-- 设置按钮 -->
    <div class="settings-row">
      <button class="btn-settings" @click="handleSettings">⚙️</button>
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
            <td class="col-code">{{ product.code || '-' }}</td>
            <td class="col-stock">{{ product.stock || '-' }}</td>
            <td class="col-unit">{{ product.unit || '-' }}</td>
            <td class="col-price">{{ product.price ? product.price.toFixed(2) : '0.00' }}</td>
            <td class="col-category">{{ product.category || '-' }}</td>
            <td class="col-team">{{ product.warehouse || '无' }}</td>
            <td class="col-notes">{{ product.notes || '-' }}</td>
            <td class="col-actions">
              <button class="btn-action btn-copy" @click="handleCopy(product)">修改</button>
              <button class="btn-action btn-copy" @click="handleCopyProduct(product)">复制</button>
              <button class="btn-action btn-delete" @click="handleDelete(product)">删除</button>
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

// 筛选条件
const filters = ref({
  productName: '',
  productCode: '',
  specification: '',
  showOnlyUsed: false
})

// 数据
const products = ref([])
const selectAll = ref(false)
const currentPage = ref(1)
const pageSize = ref(30)
const jumpPage = ref(1)
const productFormModal = ref(null)

// 模拟数据
const mockProducts = [
  { id: 1, name: '阴极', code: 'DE101', stock: -20000, unit: '公斤', price: 0.00, category: '成品分类', warehouse: '无', notes: '-', selected: false },
  { id: 2, name: '洗涤硫酸', code: '', stock: -4400, unit: '无', price: 0.00, category: '无', warehouse: '无', notes: '-', selected: false },
  { id: 3, name: '阴极 B110', code: '', stock: -500, unit: '公斤', price: 0.00, category: '无', warehouse: '无', notes: '-', selected: false },
  { id: 4, name: '固化剂', code: '2103-18', stock: -72, unit: '公斤', price: 0.00, category: '成品分类', warehouse: '无', notes: '-', selected: false },
  { id: 5, name: '阴极', code: '2103-1A', stock: -80, unit: '公斤', price: 0.00, category: '成品分类', warehouse: '无', notes: '-', selected: false },
  { id: 6, name: '固化剂', code: '1106B', stock: -4000, unit: '无', price: 0.00, category: '成品分类', warehouse: '无', notes: '-', selected: false },
  { id: 7, name: '阴极', code: '1106A', stock: -4000, unit: '公斤', price: 0.00, category: '成品分类', warehouse: '无', notes: '-', selected: false },
  { id: 8, name: '阴素B026', code: '', stock: -6000, unit: '公斤', price: 0.00, category: '成品分类', warehouse: '无', notes: '-', selected: false },
]

// 计算属性
const totalProducts = computed(() => products.value.length)
const totalPages = computed(() => Math.ceil(totalProducts.value / pageSize.value))
const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return products.value.slice(start, end)
})

// 方法
const handleSearch = () => {
  console.log('搜索', filters.value)
}

const toggleFilter = () => {
  console.log('筛选')
}

const handleBatch = () => {
  console.log('批量操作')
}

const handleNew = () => {
  if (productFormModal.value) {
    productFormModal.value.open()
  }
}

const handleImport = () => {
  console.log('导入')
}

const handleExport = () => {
  console.log('导出')
}

const handleSaveProduct = (productData) => {
  // 保存商品数据
  const newProduct = {
    id: products.value.length + 1,
    name: productData.name,
    code: productData.specification,
    stock: 0,
    unit: productData.unit,
    price: 0,
    category: productData.category,
    warehouse: productData.warehouse || '无',
    notes: productData.notes || '-',
    selected: false,
    disabled: productData.status === 'disabled'
  }

  products.value.unshift(newProduct)
  console.log('商品已保存', newProduct)
}

const loadProducts = () => {
  // 重新加载商品列表
  console.log('重新加载商品列表')
}

const handleSettings = () => {
  console.log('设置')
}

const handleSort = (field) => {
  console.log('排序', field)
}

const handleSelectAll = () => {
  products.value.forEach(p => p.selected = selectAll.value)
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

onMounted(() => {
  products.value = [...mockProducts]
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
  min-width: 150px;
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
