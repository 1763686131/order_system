<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- 弹窗头部 -->
      <div class="modal-header">
        <h3 class="modal-title">{{ isEdit ? '编辑商品' : '新增商品' }}</h3>
        <button class="btn-close" @click="handleClose">×</button>
      </div>

      <!-- Tab 选项卡 -->
      <div class="modal-tabs">
        <div
          v-for="(tab, index) in tabs"
          :key="index"
          :class="['tab-item', { active: currentTab === index }]"
          @click="currentTab = index"
        >
          {{ tab }}
        </div>
      </div>

      <!-- 弹窗内容 -->
      <div class="modal-body">
        <!-- Tab 0: 基本信息 -->
        <div v-show="currentTab === 0" class="tab-content">
          <!-- 第一行：门店 + 状态 -->
          <div class="form-row">
            <div class="form-group half">
              <label class="required">门店:</label>
              <div class="checkbox-group">
                <label v-for="store in stores" :key="store.id" class="checkbox-item">
                  <input
                    type="checkbox"
                    :value="store.id"
                    v-model="formData.storeIds"
                  />
                  <span class="checkbox-label">{{ store.name }}</span>
                </label>
              </div>
            </div>
            <div class="form-group half">
              <label>状态:</label>
              <ToggleSwitch v-model="formData.enabled" />
            </div>
          </div>

          <!-- 第二行：商品名称 + 编号 -->
          <div class="form-row">
            <div class="form-group half">
              <label class="required">商品名称:</label>
              <input
                v-model="formData.name"
                type="text"
                placeholder="请输入商品名称"
                class="form-input"
              />
            </div>
            <div class="form-group half">
              <label>编号:</label>
              <input
                v-model="formData.code"
                type="text"
                placeholder="请输入编号"
                class="form-input"
              />
            </div>
          </div>

          <!-- 第三行：分类 + 规格型号 -->
          <div class="form-row">
            <div class="form-group half">
              <label>分类:</label>
              <div class="input-with-link">
                <select v-model="formData.category" class="form-select">
                  <option value="">请选择商品分类</option>
                  <option value="成品">成品</option>
                  <option value="半成品">半成品</option>
                  <option value="原材料">原材料</option>
                  <option value="其他">其他</option>
                </select>
                <a href="#" class="link-new" @click.prevent="handleNewCategory">新增</a>
              </div>
            </div>
            <div class="form-group half">
              <label>规格型号:</label>
              <input
                v-model="formData.specification"
                type="text"
                placeholder="请输入规格型号"
                class="form-input"
              />
            </div>
          </div>

          <!-- 第四行：单位 + 仓库 -->
          <div class="form-row">
            <div class="form-group half">
              <label>单位:</label>
              <div class="unit-group">
                <select v-model="formData.unit" class="form-select">
                  <option value="">请选择单位</option>
                  <option value="公斤">公斤</option>
                  <option value="吨">吨</option>
                  <option value="米">米</option>
                  <option value="个">个</option>
                  <option value="件">件</option>
                  <option value="箱">箱</option>
                </select>
                <label class="checkbox-inline">
                  <input type="checkbox" v-model="formData.enableMultiUnit" />
                  <span>启用多单位</span>
                </label>
              </div>
            </div>
            <div class="form-group half">
              <label>仓库:</label>
              <select v-model="formData.warehouse" class="form-select">
                <option value="">请选择默认仓库</option>
                <option value="主仓库">主仓库</option>
                <option value="副仓库">副仓库</option>
                <option value="仓库A">仓库A</option>
                <option value="仓库B">仓库B</option>
              </select>
            </div>
          </div>

          <!-- 第五行：备注 -->
          <div class="form-row">
            <div class="form-group full">
              <label>备注:</label>
              <textarea
                v-model="formData.notes"
                placeholder="请输入备注"
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Tab 1: 属性 -->
        <div v-show="currentTab === 1" class="tab-content">
          <p class="empty-tip">属性设置</p>
        </div>

        <!-- Tab 2: 价格&条码 -->
        <div v-show="currentTab === 2" class="tab-content">
          <p class="empty-tip">价格和条码设置</p>
        </div>

        <!-- Tab 3: 库存设置 -->
        <div v-show="currentTab === 3" class="tab-content">
          <div class="warehouse-section">
            <div class="section-header">
              <div>
                <h4 class="section-title">仓库管理</h4>
                <p class="section-desc">管理仓库及其分类，为商品选择所属仓库及分类</p>
              </div>
              <button class="btn-add-warehouse" @click="handleAddWarehouse">
                <span>+</span> 新增仓库
              </button>
            </div>

            <div class="warehouse-list">
              <div v-for="warehouse in warehouses" :key="warehouse.id" class="warehouse-item">
                <div class="warehouse-header">
                  <label class="warehouse-checkbox">
                    <input
                      type="checkbox"
                      :value="warehouse.id"
                      @change="handleWarehouseChange(warehouse.id, $event.target.checked)"
                      :checked="isWarehouseSelected(warehouse.id)"
                    />
                    <span class="warehouse-name">{{ warehouse.name }}</span>
                  </label>
                  <div class="warehouse-actions">
                    <button class="btn-icon" @click="handleEditWarehouse(warehouse)" title="修改仓库">
                      <span>✏️</span>
                    </button>
                    <button class="btn-icon btn-danger" @click="handleDeleteWarehouse(warehouse.id)" title="删除仓库">
                      <span>🗑️</span>
                    </button>
                  </div>
                </div>

                <div v-if="isWarehouseSelected(warehouse.id)" class="category-section">
                  <div class="category-header">
                    <span class="category-title">分类列表</span>
                    <button class="btn-add-category" @click="handleAddCategory(warehouse.id)">
                      <span>+</span> 新增分类
                    </button>
                  </div>

                  <div class="category-list">
                    <div
                      v-for="category in warehouse.categories"
                      :key="category.id"
                      class="category-item"
                    >
                      <label class="category-checkbox">
                        <input
                          type="checkbox"
                          :value="category.id"
                          v-model="formData.warehouseCategories[warehouse.id]"
                        />
                        <span class="category-label">{{ category.name }}</span>
                      </label>
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
                </div>
              </div>

              <div v-if="warehouses.length === 0" class="empty-tip">
                暂无仓库，请点击"新增仓库"添加
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 弹窗底部 -->
      <div class="modal-footer">
        <button class="btn-cancel" @click="handleClose">取消</button>
        <button class="btn-save" @click="handleSave">保存</button>
        <button class="btn-save-continue" @click="handleSaveAndContinue">保存并继续新增</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '@/api/request'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'

const visible = ref(false)
const isEdit = ref(false)
const currentTab = ref(0)
const stores = ref([])
const warehouses = ref([
  {
    id: 1,
    name: 'A仓库',
    categories: [
      { id: 101, name: '原材料分类' },
      { id: 102, name: '半成品分类' },
      { id: 103, name: '成品分类' }
    ]
  },
  {
    id: 2,
    name: 'B仓库',
    categories: [
      { id: 201, name: '原材料分类' },
      { id: 202, name: '半成品分类' },
      { id: 203, name: '成品分类' }
    ]
  },
  {
    id: 3,
    name: 'C仓库',
    categories: [
      { id: 301, name: '原材料分类' },
      { id: 302, name: '半成品分类' }
    ]
  }
])

const tabs = ['基本信息', '仓库', '价格&条码', '库存设置']

const formData = reactive({
  code: '',
  name: '',
  specification: '',
  category: '',
  unit: '',
  enableMultiUnit: false,
  notes: '',
  enabled: true,
  warehouse: '',
  storeIds: [],
  warehouseCategories: {} // 格式: { 仓库ID: [分类ID数组] }
})

const emit = defineEmits(['save', 'refresh'])

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

onMounted(() => {
  loadStores()
})

// 打开弹窗
const open = (product = null) => {
  visible.value = true
  currentTab.value = 0

  if (product) {
    isEdit.value = true
    Object.assign(formData, product)
  } else {
    isEdit.value = false
    resetForm()
  }
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 点击遮罩层关闭
const handleOverlayClick = () => {
  handleClose()
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    code: '',
    name: '',
    specification: '',
    category: '',
    unit: '',
    enableMultiUnit: false,
    notes: '',
    enabled: true,
    warehouse: '',
    storeIds: [],
    warehouseCategories: {}
  })
}

// 新增分类
const handleNewCategory = () => {
  console.log('新增分类')
}

// 处理仓库选择
const handleWarehouseChange = (warehouseId, checked) => {
  if (checked) {
    // 选中仓库时，初始化为空数组
    if (!formData.warehouseCategories[warehouseId]) {
      formData.warehouseCategories[warehouseId] = []
    }
  } else {
    // 取消选中时，删除该仓库的分类数据
    delete formData.warehouseCategories[warehouseId]
  }
}

// 判断仓库是否被选中
const isWarehouseSelected = (warehouseId) => {
  return warehouseId in formData.warehouseCategories
}

// 新增仓库
const handleAddWarehouse = () => {
  const name = prompt('请输入仓库名称:')
  if (!name || !name.trim()) return

  const newId = Math.max(...warehouses.value.map(w => w.id), 0) + 1
  warehouses.value.push({
    id: newId,
    name: name.trim(),
    categories: []
  })
}

// 修改仓库
const handleEditWarehouse = (warehouse) => {
  const newName = prompt('请输入新的仓库名称:', warehouse.name)
  if (!newName || !newName.trim()) return

  warehouse.name = newName.trim()
}

// 删除仓库
const handleDeleteWarehouse = (warehouseId) => {
  if (!confirm('确定要删除该仓库吗？删除后将无法恢复。')) return

  const index = warehouses.value.findIndex(w => w.id === warehouseId)
  if (index > -1) {
    warehouses.value.splice(index, 1)
    // 同时删除该仓库的选择数据
    delete formData.warehouseCategories[warehouseId]
  }
}

// 新增分类
const handleAddCategory = (warehouseId) => {
  const name = prompt('请输入分类名称:')
  if (!name || !name.trim()) return

  const warehouse = warehouses.value.find(w => w.id === warehouseId)
  if (!warehouse) return

  const newId = Math.max(...warehouse.categories.map(c => c.id), warehouseId * 100) + 1
  warehouse.categories.push({
    id: newId,
    name: name.trim()
  })
}

// 修改分类
const handleEditCategory = (warehouseId, category) => {
  const newName = prompt('请输入新的分类名称:', category.name)
  if (!newName || !newName.trim()) return

  category.name = newName.trim()
}

// 删除分类
const handleDeleteCategory = (warehouseId, categoryId) => {
  if (!confirm('确定要删除该分类吗？')) return

  const warehouse = warehouses.value.find(w => w.id === warehouseId)
  if (!warehouse) return

  const index = warehouse.categories.findIndex(c => c.id === categoryId)
  if (index > -1) {
    warehouse.categories.splice(index, 1)
    // 如果该分类被选中，从选择中移除
    if (formData.warehouseCategories[warehouseId]) {
      const catIndex = formData.warehouseCategories[warehouseId].indexOf(categoryId)
      if (catIndex > -1) {
        formData.warehouseCategories[warehouseId].splice(catIndex, 1)
      }
    }
  }
}

// 保存
const handleSave = () => {
  if (!formData.name) {
    alert('请输入商品名称')
    return
  }

  if (!formData.storeIds || formData.storeIds.length === 0) {
    alert('请至少选择一个门店')
    return
  }

  emit('save', { ...formData })
  handleClose()
}

// 保存并继续新增
const handleSaveAndContinue = () => {
  if (!formData.name) {
    alert('请输入商品名称')
    return
  }

  if (!formData.storeIds || formData.storeIds.length === 0) {
    alert('请至少选择一个门店')
    return
  }

  emit('save', { ...formData })
  resetForm()
}

defineExpose({
  open
})
</script>

<style scoped>
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
  max-width: 960px;
  max-height: 90vh;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

/* 头部 */
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

/* Tab 选项卡 */
.modal-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.tab-item {
  flex: 1;
  padding: 12px 16px;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.tab-item:hover {
  color: #10b981;
  background: #f3f4f6;
}

.tab-item.active {
  color: #10b981;
  border-bottom-color: #10b981;
  font-weight: 600;
  background: white;
}

/* 内容区 */
.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.form-group.half {
  flex: 1;
}

.form-group.full {
  flex: 1;
  width: 100%;
}

.form-group label {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  min-width: 80px;
  text-align: right;
  padding-top: 8px;
}

.form-group label.required::before {
  content: '*';
  color: #ef4444;
  margin-right: 4px;
}

.form-input,
.form-select,
.form-textarea {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  font-family: inherit;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #9ca3af;
}

.form-select {
  cursor: pointer;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

/* 复选框组 */
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 8px 0;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  user-select: none;
}

.checkbox-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #10b981;
}

.checkbox-label {
  cursor: pointer;
}

.checkbox-item:hover .checkbox-label {
  color: #10b981;
}

.input-with-link {
  flex: 1;
  display: flex;
  gap: 8px;
  align-items: center;
}

.link-new {
  color: #10b981;
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
  cursor: pointer;
}

.link-new:hover {
  text-decoration: underline;
}

.unit-group {
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: center;
}

.checkbox-inline {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  white-space: nowrap;
}

.checkbox-inline input[type="checkbox"] {
  cursor: pointer;
  accent-color: #10b981;
}

.empty-tip {
  text-align: center;
  color: #9ca3af;
  padding: 40px 0;
  font-size: 14px;
}

/* 仓库分类设置 */
.warehouse-section {
  padding: 16px 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.section-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.btn-add-warehouse {
  padding: 8px 16px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
  font-weight: 500;
}

.btn-add-warehouse:hover {
  background: #059669;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.btn-add-warehouse span {
  font-size: 18px;
}

.warehouse-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.warehouse-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  background: #f9fafb;
  transition: all 0.3s;
}

.warehouse-item:hover {
  border-color: #10b981;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
}

.warehouse-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.warehouse-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.warehouse-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #10b981;
}

.warehouse-name {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.warehouse-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  padding: 6px 10px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
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
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.category-title {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.btn-add-category {
  padding: 4px 12px;
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
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
  background: #f9fafb;
}

.category-item:hover {
  background: #f3f4f6;
  border-color: #10b981;
}

.category-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  flex: 1;
}

.category-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #10b981;
}

.category-label {
  font-size: 14px;
  color: #374151;
}

.category-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.btn-icon-sm {
  padding: 2px 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
  border-radius: 3px;
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

/* 底部 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.btn-cancel,
.btn-save,
.btn-save-continue {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
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

.btn-save-continue {
  background: #3b82f6;
  color: white;
}

.btn-save-continue:hover {
  background: #2563eb;
}
</style>
