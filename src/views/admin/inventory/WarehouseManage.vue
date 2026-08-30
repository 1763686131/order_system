<template>
  <div class="warehouse-manage-page">
    <div class="page-header">
      <h2 class="page-title">仓库管理</h2>
      <div class="header-actions">
        <div class="store-filter">
          <label class="filter-label">选择门店：</label>
          <select v-model="selectedStoreId" @change="handleStoreChange" class="store-select">
            <option value="">全部门店</option>
            <option v-for="store in stores" :key="store.id" :value="store.id">
              {{ store.name }}
            </option>
          </select>
        </div>
        <button
          class="btn-add-warehouse"
          @click="handleAddWarehouse"
          :disabled="!selectedStoreId"
          :class="{ disabled: !selectedStoreId }"
        >
          <span>+</span> 新增仓库
        </button>
      </div>
    </div>

    <div class="warehouse-list">
      <div
        v-for="warehouse in filteredWarehouses"
        :key="warehouse.id"
        class="warehouse-card"
        :style="{
          backgroundColor: getStoreColor(warehouse.storeId),
          color: getStoreTextColor(warehouse.storeId)
        }"
      >
        <div class="warehouse-header">
          <div class="warehouse-info">
            <h3 class="warehouse-name">{{ warehouse.name }}</h3>
            <div class="warehouse-meta">
              <span class="warehouse-store">{{ getStoreName(warehouse.storeId) }}</span>
              <span class="warehouse-stats">{{ warehouse.categories.length }} 个分类</span>
            </div>
          </div>
          <div class="warehouse-actions">
            <button class="btn-icon" @click="handleEditWarehouse(warehouse)" title="修改仓库">
              <span>✏️</span>
            </button>
            <button class="btn-icon btn-danger" @click="handleDeleteWarehouse(warehouse.id)" title="删除仓库">
              <span>🗑️</span>
            </button>
          </div>
        </div>

        <div class="category-section">
          <div class="category-header">
            <span class="category-title">分类列表</span>
            <button class="btn-add-category" @click="handleAddCategory(warehouse.id)">
              <span>+</span> 新增分类
            </button>
          </div>

          <div v-if="warehouse.categories.length > 0" class="category-list">
            <div
              v-for="category in warehouse.categories"
              :key="category.id"
              class="category-item"
            >
              <span class="category-name">{{ category.name }}</span>
              <div class="category-actions">
                <button class="btn-icon-sm" @click="handleEditCategory(warehouse.id, category)" title="修改分类">
                  ✏️
                </button>
                <button class="btn-icon-sm btn-danger" @click="handleDeleteCategory(warehouse.id, category.id)" title="删除分类">
                  ×
                </button>
              </div>
            </div>
          </div>

          <div v-else class="empty-category">
            暂无分类，请点击"新增分类"添加
          </div>
        </div>
      </div>

      <div v-if="warehouses.length === 0" class="empty-warehouse">
        <p>暂无仓库数据</p>
        <p class="empty-tip">请选择门店后点击"新增仓库"按钮添加仓库</p>
      </div>
    </div>

    <!-- 新增/编辑仓库弹窗 -->
    <div v-if="showWarehouseModal" class="modal-overlay" @click="closeWarehouseModal">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">{{ isEditMode ? '编辑仓库' : '新增仓库' }}</h3>
          <button class="btn-close" @click="closeWarehouseModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">仓库ID:</label>
            <input
              v-model="warehouseForm.code"
              type="text"
              placeholder="请输入仓库ID"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">仓库名称:</label>
            <input
              v-model="warehouseForm.name"
              type="text"
              placeholder="请输入仓库名称"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">所属门店:</label>
            <input
              :value="getStoreName(selectedStoreId)"
              type="text"
              class="form-input"
              disabled
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeWarehouseModal">取消</button>
          <button class="btn-save" @click="saveWarehouse">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const selectedStoreId = ref('')
const stores = ref([])
const warehouses = ref([])
const showWarehouseModal = ref(false)
const isEditMode = ref(false)
const warehouseForm = ref({
  id: null,
  code: '',
  name: '',
  storeId: ''
})

// 加载门店数据
const loadStores = async () => {
  try {
    const response = await request({
      url: '/stores',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      stores.value = response.filter(s => s.status === 'active')
    }
  } catch (error) {
    console.error('加载门店失败:', error)
  }
}

// 加载仓库数据
const loadWarehouses = async () => {
  try {
    const params = selectedStoreId.value ? { storeId: selectedStoreId.value } : {}
    const response = await request({
      url: '/warehouses',
      method: 'GET',
      params
    })
    if (response && Array.isArray(response)) {
      warehouses.value = response
    }
  } catch (error) {
    console.error('加载仓库失败:', error)
  }
}

// 根据门店筛选仓库
const filteredWarehouses = computed(() => {
  if (!selectedStoreId.value) {
    return warehouses.value
  }
  return warehouses.value.filter(w => w.storeId === selectedStoreId.value)
})

// 获取门店名称
const getStoreName = (storeId) => {
  const store = stores.value.find(s => s.id === storeId)
  return store ? store.name : '未知门店'
}

// 获取门店背景颜色
const getStoreColor = (storeId) => {
  const store = stores.value.find(s => s.id === storeId)
  return store && store.color ? store.color : '#ffffff'
}

// 获取门店文字颜色
const getStoreTextColor = (storeId) => {
  const store = stores.value.find(s => s.id === storeId)
  return store && store.textColor ? store.textColor : '#333333'
}

// 处理门店切换
const handleStoreChange = () => {
  console.log('切换到门店:', selectedStoreId.value)
}

// 打开新增仓库弹窗
const handleAddWarehouse = () => {
  if (!selectedStoreId.value) {
    alert('请先选择门店')
    return
  }

  isEditMode.value = false
  warehouseForm.value = {
    id: null,
    code: '',
    name: '',
    storeId: selectedStoreId.value
  }
  showWarehouseModal.value = true
}

// 关闭弹窗
const closeWarehouseModal = () => {
  showWarehouseModal.value = false
}

// 保存仓库
const saveWarehouse = async () => {
  if (!warehouseForm.value.code || !warehouseForm.value.code.trim()) {
    alert('请输入仓库ID')
    return
  }

  if (!warehouseForm.value.name || !warehouseForm.value.name.trim()) {
    alert('请输入仓库名称')
    return
  }

  try {
    if (isEditMode.value) {
      // 编辑模式
      await request({
        url: `/warehouses/${warehouseForm.value.id}`,
        method: 'PUT',
        data: {
          code: warehouseForm.value.code.trim(),
          name: warehouseForm.value.name.trim(),
          storeId: warehouseForm.value.storeId
        }
      })
      alert('修改成功')
    } else {
      // 新增模式
      await request({
        url: '/warehouses',
        method: 'POST',
        data: {
          code: warehouseForm.value.code.trim(),
          name: warehouseForm.value.name.trim(),
          storeId: warehouseForm.value.storeId,
          remark: ''
        }
      })
      alert('新增成功')
    }

    closeWarehouseModal()
    loadWarehouses()
  } catch (error) {
    console.error('保存仓库失败:', error)
    alert(error.response?.data?.error || '保存失败')
  }
}

onMounted(() => {
  loadStores()
})

// 修改仓库
const handleEditWarehouse = (warehouse) => {
  isEditMode.value = true
  warehouseForm.value = {
    id: warehouse.id,
    code: warehouse.code || '',
    name: warehouse.name,
    storeId: warehouse.storeId
  }
  selectedStoreId.value = warehouse.storeId
  showWarehouseModal.value = true
}

// 删除仓库
const handleDeleteWarehouse = async (warehouseId) => {
  if (!confirm('确定要删除该仓库吗？删除后将无法恢复。')) return

  try {
    await request({
      url: `/warehouses/${warehouseId}`,
      method: 'DELETE'
    })
    alert('删除成功')
    loadWarehouses()
  } catch (error) {
    console.error('删除仓库失败:', error)
    alert(error.response?.data?.error || '删除失败')
  }
}

// 新增分类
const handleAddCategory = async (warehouseId) => {
  const name = prompt('请输入分类名称:')
  if (!name || !name.trim()) return

  try {
    await request({
      url: `/warehouses/${warehouseId}/categories`,
      method: 'POST',
      data: {
        name: name.trim()
      }
    })
    alert('新增成功')
    loadWarehouses()
  } catch (error) {
    console.error('新增分类失败:', error)
    alert(error.response?.data?.error || '新增失败')
  }
}

// 修改分类
const handleEditCategory = async (warehouseId, category) => {
  const newName = prompt('请输入新的分类名称:', category.name)
  if (!newName || !newName.trim()) return

  try {
    await request({
      url: `/warehouses/${warehouseId}/categories/${category.id}`,
      method: 'PUT',
      data: {
        name: newName.trim(),
        code: category.code
      }
    })
    alert('修改成功')
    loadWarehouses()
  } catch (error) {
    console.error('修改分类失败:', error)
    alert(error.response?.data?.error || '修改失败')
  }
}

// 删除分类
const handleDeleteCategory = async (warehouseId, categoryId) => {
  if (!confirm('确定要删除该分类吗？')) return

  try {
    await request({
      url: `/warehouses/${warehouseId}/categories/${categoryId}`,
      method: 'DELETE'
    })
    alert('删除成功')
    loadWarehouses()
  } catch (error) {
    console.error('删除分类失败:', error)
    alert(error.response?.data?.error || '删除失败')
  }
}
</script>

<style scoped>
.warehouse-manage-page {
  padding: 24px;
  background: #f9fafb;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.store-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.store-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 150px;
}

.store-select:hover {
  border-color: #10b981;
}

.store-select:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.btn-add-warehouse {
  padding: 10px 20px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
}

.btn-add-warehouse:hover {
  background: #059669;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-add-warehouse.disabled {
  background: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-add-warehouse.disabled:hover {
  background: #d1d5db;
  transform: none;
  box-shadow: none;
}

.btn-add-warehouse span {
  font-size: 18px;
}

.warehouse-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 20px;
}

.warehouse-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.warehouse-card:hover {
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
  transform: translateY(-2px);
}

.warehouse-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f3f4f6;
}

.warehouse-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.warehouse-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.warehouse-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.warehouse-store {
  font-size: 13px;
  color: #10b981;
  font-weight: 500;
  padding: 2px 8px;
  background: #d1fae5;
  border-radius: 4px;
}

.warehouse-stats {
  font-size: 13px;
  color: #6b7280;
}

.warehouse-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  padding: 8px 12px;
  background: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.btn-icon:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
  transform: scale(1.05);
}

.btn-icon.btn-danger:hover {
  background: #fee2e2;
  border-color: #ef4444;
}

.category-section {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.category-title {
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
}

.btn-add-category {
  padding: 6px 14px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.btn-add-category:hover {
  background: #2563eb;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.2s;
}

.category-item:hover {
  border-color: #10b981;
  background: #f0fdf4;
}

.category-name {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.category-actions {
  display: flex;
  gap: 6px;
}

.btn-icon-sm {
  padding: 4px 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-icon-sm:hover {
  background: #e5e7eb;
  color: #374151;
}

.btn-icon-sm.btn-danger {
  font-size: 18px;
  font-weight: bold;
}

.btn-icon-sm.btn-danger:hover {
  background: #fee2e2;
  color: #ef4444;
}

.empty-category {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
  font-size: 14px;
}

.empty-warehouse {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  background: white;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
}

.empty-warehouse p {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #6b7280;
}

.empty-tip {
  font-size: 14px;
  color: #9ca3af;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-container {
  width: 90%;
  max-width: 500px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.btn-close {
  font-size: 28px;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.btn-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  transition: all 0.3s;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.form-input:disabled {
  background: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
}

.form-input::placeholder {
  color: #9ca3af;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.btn-cancel,
.btn-save {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel {
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.btn-cancel:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.btn-save {
  background: #10b981;
  color: white;
}

.btn-save:hover {
  background: #059669;
}
</style>
