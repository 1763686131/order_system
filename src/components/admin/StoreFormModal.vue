<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- 弹窗头部 -->
      <div class="modal-header">
        <h3 class="modal-title">{{ isEdit ? '编辑门店' : '新增门店' }}</h3>
        <button class="btn-close" @click="handleClose">×</button>
      </div>

      <!-- 弹窗内容 -->
      <div class="modal-body">
        <div class="form-group">
          <label class="required">门店编码:</label>
          <input
            v-model="formData.code"
            type="text"
            placeholder="请输入门店编码（如：insulation）"
            class="form-input"
            :disabled="isEdit"
          />
          <span class="form-tip">编码用于系统识别，创建后不可修改</span>
        </div>

        <div class="form-group">
          <label class="required">门店名称:</label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="请输入门店名称（如：绝缘）"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label>状态:</label>
          <div class="radio-group">
            <label class="radio-item">
              <input type="radio" v-model="formData.status" value="active" />
              <span class="radio-label">启用</span>
            </label>
            <label class="radio-item">
              <input type="radio" v-model="formData.status" value="inactive" />
              <span class="radio-label">停用</span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>备注:</label>
          <textarea
            v-model="formData.remark"
            placeholder="请输入备注信息"
            class="form-textarea"
            rows="3"
          ></textarea>
        </div>
      </div>

      <!-- 弹窗底部 -->
      <div class="modal-footer">
        <button class="btn-cancel" @click="handleClose">取消</button>
        <button class="btn-save" @click="handleSave">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const visible = ref(false)
const isEdit = ref(false)

const formData = reactive({
  id: null,
  code: '',
  name: '',
  status: 'active',
  remark: ''
})

const emit = defineEmits(['save'])

// 打开弹窗
const open = (store = null) => {
  visible.value = true

  if (store) {
    isEdit.value = true
    Object.assign(formData, store)
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
    id: null,
    code: '',
    name: '',
    status: 'active',
    remark: ''
  })
}

// 保存
const handleSave = () => {
  // 验证
  if (!formData.code || !formData.code.trim()) {
    alert('请输入门店编码')
    return
  }

  if (!formData.name || !formData.name.trim()) {
    alert('请输入门店名称')
    return
  }

  // 编码格式验证（只允许字母、数字、下划线）
  if (!/^[a-zA-Z0-9_]+$/.test(formData.code)) {
    alert('门店编码只能包含字母、数字和下划线')
    return
  }

  const saveData = {
    ...formData,
    created_at: formData.created_at || new Date().toISOString().split('T')[0]
  }

  emit('save', saveData)
  handleClose()
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
  max-width: 600px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
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

/* 内容区 */
.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: #374151;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group label.required::before {
  content: '*';
  color: #ef4444;
  margin-right: 4px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
  box-sizing: border-box;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1);
}

.form-input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
  color: #6b7280;
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #9ca3af;
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.form-tip {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-top: 6px;
}

.radio-group {
  display: flex;
  gap: 24px;
  margin-top: 8px;
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
.btn-save {
  padding: 8px 24px;
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
</style>
