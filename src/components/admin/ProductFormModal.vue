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
          <div class="form-row">
            <div class="form-group half">
              <label>条码:</label>
              <div class="input-with-link">
                <input
                  v-model="formData.barcode"
                  type="text"
                  placeholder="请输入条码"
                  class="form-input"
                />
                <a href="#" class="link-auto" @click.prevent="handleAutoBarcode">自动</a>
              </div>
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
              <label>规格型号:</label>
              <input
                v-model="formData.specification"
                type="text"
                placeholder="请输入规格型号"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>分类:</label>
              <div class="input-with-link">
                <select v-model="formData.category" class="form-select">
                  <option value="">请选择商品分类</option>
                  <option value="成品分类">成品分类</option>
                  <option value="原材料分类">原材料分类</option>
                  <option value="其他">其他</option>
                </select>
                <a href="#" class="link-new" @click.prevent="handleNewCategory">新增</a>
              </div>
            </div>
            <div class="form-group half">
              <label>品牌:</label>
              <select v-model="formData.brand" class="form-select">
                <option value="">请选择品牌</option>
                <option value="品牌A">品牌A</option>
                <option value="品牌B">品牌B</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>单位:</label>
              <div class="unit-group">
                <select v-model="formData.unit" class="form-select">
                  <option value="">请选择单位</option>
                  <option value="公斤">公斤</option>
                  <option value="吨">吨</option>
                  <option value="件">件</option>
                  <option value="箱">箱</option>
                </select>
                <label class="checkbox-inline">
                  <input type="checkbox" v-model="formData.enableMultiUnit" />
                  启用多单位
                  <span class="help-icon" title="启用多单位功能">?</span>
                </label>
              </div>
            </div>
            <div class="form-group half">
              <label>备注:</label>
              <input
                v-model="formData.notes"
                type="text"
                placeholder="请输入备注"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>状态:</label>
              <div class="radio-group">
                <label class="radio-item">
                  <input type="radio" v-model="formData.status" value="enabled" />
                  <span class="radio-label">启用</span>
                </label>
                <label class="radio-item">
                  <input type="radio" v-model="formData.status" value="disabled" />
                  <span class="radio-label">停用</span>
                </label>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>默认仓库:</label>
              <div class="input-with-help">
                <select v-model="formData.warehouse" class="form-select">
                  <option value="">请选择默认仓库</option>
                  <option value="主仓库">主仓库</option>
                  <option value="副仓库">副仓库</option>
                </select>
                <span class="help-icon" title="选择默认仓库">?</span>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>货位:</label>
              <input
                v-model="formData.location"
                type="text"
                placeholder="请输入货位"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>库存预警:</label>
              <div class="input-with-help">
                <input
                  v-model.number="formData.stockWarning"
                  type="number"
                  placeholder="20"
                  class="form-input"
                />
                <span class="help-icon" title="库存低于此值时预警">?</span>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>零售名称:</label>
              <input
                v-model="formData.retailName"
                type="text"
                placeholder="请输入零售名称"
                class="form-input"
              />
            </div>
          </div>

          <div class="collapse-section">
            <div class="collapse-header" @click="toggleCollapse">
              <span>收起</span>
              <span class="collapse-icon">{{ isCollapsed ? '▲' : '▼' }}</span>
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
          <p class="empty-tip">库存设置</p>
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
import { ref, reactive } from 'vue'

const visible = ref(false)
const isEdit = ref(false)
const currentTab = ref(0)
const isCollapsed = ref(false)

const tabs = ['基本信息', '属性', '价格&条码', '库存设置']

const formData = reactive({
  barcode: '',
  code: '',
  name: '',
  specification: '',
  category: '',
  brand: '',
  unit: '',
  enableMultiUnit: false,
  notes: '',
  status: 'enabled',
  warehouse: '',
  location: '',
  stockWarning: 20,
  retailName: ''
})

const emit = defineEmits(['save', 'refresh'])

// 打开弹窗
const open = (product = null) => {
  visible.value = true
  currentTab.value = 0
  isCollapsed.value = false

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
    barcode: '',
    code: '',
    name: '',
    specification: '',
    category: '',
    brand: '',
    unit: '',
    enableMultiUnit: false,
    notes: '',
    status: 'enabled',
    warehouse: '',
    location: '',
    stockWarning: 20,
    retailName: ''
  })
}

// 自动生成条码
const handleAutoBarcode = () => {
  formData.barcode = 'AUTO' + Date.now()
}

// 新增分类
const handleNewCategory = () => {
  console.log('新增分类')
}

// 切换折叠
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 保存
const handleSave = () => {
  if (!formData.name) {
    alert('请输入商品名称')
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
  padding: 0 24px;
  background: #f9fafb;
}

.tab-item {
  padding: 12px 24px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
  position: relative;
  top: 1px;
}

.tab-item:hover {
  color: #1f2937;
}

.tab-item.active {
  color: #10b981;
  border-bottom-color: #10b981;
  background: white;
}

/* 内容区 */
.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.tab-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-group.half {
  flex: 1;
  min-width: 0;
}

.form-group label {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  min-width: 80px;
  text-align: right;
}

.form-group label.required::before {
  content: '*';
  color: #ef4444;
  margin-right: 4px;
}

.form-input,
.form-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.form-input:focus,
.form-select:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1);
}

.form-input::placeholder {
  color: #9ca3af;
}

.form-select {
  cursor: pointer;
}

.input-with-link {
  flex: 1;
  display: flex;
  gap: 8px;
  align-items: center;
}

.link-auto,
.link-new {
  color: #10b981;
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
  cursor: pointer;
}

.link-auto:hover,
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
}

.help-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: #e5e7eb;
  color: #6b7280;
  border-radius: 50%;
  font-size: 12px;
  cursor: help;
}

.input-with-help {
  flex: 1;
  display: flex;
  gap: 8px;
  align-items: center;
}

.radio-group {
  display: flex;
  gap: 24px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.radio-item input[type="radio"] {
  cursor: pointer;
}

.radio-label {
  font-size: 14px;
  color: #374151;
}

.collapse-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.collapse-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: #10b981;
  font-size: 14px;
  cursor: pointer;
  user-select: none;
}

.collapse-icon {
  font-size: 12px;
}

.empty-tip {
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
  padding: 40px 0;
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
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #d1d5db;
}

.btn-cancel {
  background: white;
  color: #374151;
}

.btn-cancel:hover {
  background: #f3f4f6;
}

.btn-save {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.btn-save:hover {
  background: #059669;
}

.btn-save-continue {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.btn-save-continue:hover {
  background: #2563eb;
}
</style>
