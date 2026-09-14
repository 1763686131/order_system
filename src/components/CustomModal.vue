<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="custom-modal-overlay"
        @click.self="handleCancel"
      >
        <div class="custom-modal" role="dialog" aria-modal="true">
          <!-- 头部 -->
          <header class="modal-header">
            <div
              class="modal-icon"
              :class="type"
              aria-hidden="true"
            >
              {{ iconText }}
            </div>
            <h3>{{ title }}</h3>
          </header>

          <!-- 内容 -->
          <div class="modal-body">
            <p>{{ message }}</p>
          </div>

          <!-- 按钮 -->
          <footer class="modal-footer">
            <button
              v-if="showCancel"
              type="button"
              class="btn-modal-cancel"
              @click="handleCancel"
            >
              {{ cancelText }}
            </button>
            <button
              type="button"
              class="btn-modal-confirm"
              :class="{ danger: isDanger }"
              @click="handleConfirm"
            >
              {{ confirmText }}
            </button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'warning',
    validator: (value) => ['success', 'error', 'warning'].includes(value)
  },
  title: {
    type: String,
    required: true
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  showCancel: {
    type: Boolean,
    default: true
  },
  danger: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['confirm', 'cancel', 'update:visible'])

const iconText = computed(() => {
  switch (props.type) {
    case 'success':
      return '✓'
    case 'error':
      return '✕'
    case 'warning':
      return '!'
    default:
      return '!'
  }
})

const isDanger = computed(() => {
  return props.danger || props.type === 'error'
})

const handleConfirm = () => {
  emit('confirm')
  emit('update:visible', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
}
</script>

<style scoped>
/* 遮罩层 */
.custom-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
}

/* 弹窗容器 */
.custom-modal {
  background: #ffffff;
  border-radius: 7px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
  width: 400px;
  max-width: 90%;
}

/* 弹窗头部 */
.modal-header {
  padding: 24px 24px 16px;
  text-align: center;
  border-bottom: 1px solid #e2e8f0;
}

/* 图标圆形 */
.modal-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  margin: 0 auto 12px;
}

/* 图标颜色语义 */
.modal-icon.success {
  background: #0f9f78;
  color: #ffffff;
}

.modal-icon.error {
  background: #ef4444;
  color: #ffffff;
}

.modal-icon.warning {
  background: #f59e0b;
  color: #ffffff;
}

/* 标题 */
.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 650;
  color: #172033;
}

/* 内容区 */
.modal-body {
  padding: 24px;
  text-align: center;
}

.modal-body p {
  margin: 0;
  font-size: 14px;
  color: #596579;
  line-height: 1.6;
  white-space: pre-line;
}

/* 按钮区 */
.modal-footer {
  padding: 16px 24px 24px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 取消按钮 */
.btn-modal-cancel {
  height: 38px;
  background: #ffffff;
  color: #596579;
  border: 1px solid #cbd5e1;
  padding: 0 32px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  min-width: 120px;
  transition: all 0.18s ease;
  cursor: pointer;
}

.btn-modal-cancel:hover {
  background: #e9f8f3;
  border-color: #a9e5d2;
  color: #08745a;
}

/* 确认按钮 */
.btn-modal-confirm {
  height: 38px;
  background: #0f9f78;
  color: #ffffff;
  border: 1px solid #0f9f78;
  padding: 0 32px;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  min-width: 120px;
  transition: all 0.18s ease;
  cursor: pointer;
}

.btn-modal-confirm:hover {
  background: #08745a;
  border-color: #08745a;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(15, 159, 120, 0.25);
}

/* 危险按钮 */
.btn-modal-confirm.danger {
  background: #ef4444;
  border-color: #ef4444;
}

.btn-modal-confirm.danger:hover {
  background: #dc2626;
  border-color: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
}

/* 动画 */
.modal-enter-active {
  animation: fadeIn 0.2s ease;
}

.modal-enter-active .custom-modal {
  animation: slideUp 0.25s ease;
}

.modal-leave-active {
  animation: fadeOut 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* 移动端适配 */
@media (max-width: 780px) {
  .custom-modal {
    width: calc(100vw - 32px);
    max-width: calc(100vw - 32px);
  }
}
</style>
