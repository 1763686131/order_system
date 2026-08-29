<template>
  <teleport to="body">
    <!-- 顶部消息提示 -->
    <div
      v-if="messageVisible"
      :class="['top-message', `message-${messageType}`]"
    >
      {{ messageText }}
    </div>

    <div
      v-if="visible"
      id="shipOrderModal"
      class="modal-overlay"
      @click.self="handleClose"
    >
      <div class="modal-content" style="width: 450px;">
        <div class="modal-close" @click="handleClose">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1 1L13 13M13 1L1 13" stroke="#ff4d4f" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>

        <div class="modal-header">
          <div class="modal-title">完成订单发货</div>
          <div class="modal-subtitle">选择发货途径并录入凭证同步看板</div>
        </div>

        <div class="modal-body" style="padding: 24px 30px 32px 30px;">
          <div class="form-item" style="margin-bottom: 22px;">
            <label style="font-weight: bold; color: #555; margin-bottom: 10px; display: block;">发货方式:</label>

            <div style="display: flex; align-items: center; gap: 16px; font-size: 14px; white-space: nowrap; margin-bottom: 12px; width: 100%; box-sizing: border-box;">
              <label style="cursor: pointer; display: flex; align-items: center; gap: 5px;">
                <input type="radio" v-model="shippingMethod" value="0"> 物流
              </label>
              <label style="cursor: pointer; display: flex; align-items: center; gap: 5px;">
                <input type="radio" v-model="shippingMethod" value="1"> 零担快运
              </label>
              <label style="cursor: pointer; display: flex; align-items: center; gap: 5px;">
                <input type="radio" v-model="shippingMethod" value="2"> 快递
              </label>
              <label style="cursor: pointer; display: flex; align-items: center; gap: 5px;">
                <input type="radio" v-model="shippingMethod" value="3"> 专车
              </label>
            </div>

            <div style="display: flex; align-items: center; gap: 8px; font-size: 14px; background: #f9f9f9; padding: 10px 14px; border-radius: 8px; border: 1px solid #e8e8e8; box-sizing: border-box; width: 100%;">
              <label style="cursor: pointer; display: flex; align-items: center; gap: 5px; white-space: nowrap; font-weight: bold; color: #555;">
                <input type="radio" v-model="shippingMethod" value="4"> 其它:
              </label>
              <input
                v-model="customMethod"
                type="text"
                placeholder="请输入自定义发货途径（如：自提、车队随带...）"
                style="flex: 1; min-width: 0; padding: 6px 10px; font-size: 13px; border: 1px solid #ccc; border-radius: 6px; outline: none; background: #fff; height: 30px; box-sizing: border-box;"
                @focus="shippingMethod = '4'"
              />
            </div>
          </div>
        </div>

        <button
          class="modal-btn-confirm"
          style="background-color: #52c41a;"
          @click="handleSubmit"
          :disabled="loading"
        >
          {{ loading ? '提交中...' : '确认发货并完成出库' }}
        </button>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref } from 'vue'
import { useOrderStore } from '@/stores/order'

const emit = defineEmits(['refresh'])

const orderStore = useOrderStore()

const visible = ref(false)
const loading = ref(false)
const targetOrderId = ref(null)
const shippingMethod = ref('0')
const customMethod = ref('')

// 消息提示状态
const messageVisible = ref(false)
const messageText = ref('')
const messageType = ref('success')

// 显示顶部消息提示
const showMessage = (text, type = 'success') => {
  messageText.value = text
  messageType.value = type
  messageVisible.value = true

  setTimeout(() => {
    messageVisible.value = false
  }, 3000)
}

// 获取当前时间
const getCurrentDateTime = () => {
  const now = new Date()
  const Y = now.getFullYear()
  const M = String(now.getMonth() + 1).padStart(2, '0')
  const D = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  return `${Y}-${M}-${D} ${h}:${m}`
}

// 打开弹窗
const open = (orderId) => {
  targetOrderId.value = orderId
  shippingMethod.value = '0'
  customMethod.value = ''
  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 提交出库
const handleSubmit = async () => {
  const shippingMethodIdx = parseInt(shippingMethod.value)
  let customText = ''

  if (shippingMethodIdx === 4) {
    customText = customMethod.value.trim()
  }

  const currentDateTime = getCurrentDateTime()

  const payload = {
    status: 'shipped',
    shipping_method: shippingMethodIdx,
    shipping_custom: customText,
    logistics_no: '暂未录入单号',
    shipped_date: currentDateTime,
    completed_date: currentDateTime
  }

  loading.value = true

  try {
    await orderStore.updateOrderById(targetOrderId.value, payload)
    showMessage('✓ 出库成功！', 'success')
    handleClose()
    emit('refresh')

    // 同时触发全局刷新事件（兼容其他组件）
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
    showMessage('发货出库网络通讯失败', 'error')
  } finally {
    loading.value = false
  }
}

// 暴露方法
defineExpose({
  open
})
</script>

<style scoped>
/* 顶部消息提示样式 */
.top-message {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 10001;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideDown 0.3s ease;
}

.message-success {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #86efac;
}

.message-error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fca5a5;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}
</style>
