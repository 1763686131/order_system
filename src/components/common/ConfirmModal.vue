<template>
  <teleport to="body">
    <div
      v-if="visible"
      id="confirmModal"
      class="modal-overlay"
      @click.self="handleClose"
    >
      <div class="modal-content">
        <div class="modal-close" @click="handleClose">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1 1L13 13M13 1L1 13" stroke="#ff4d4f" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>

        <div class="modal-header">
          <div class="modal-title">{{ modalTitle }}</div>
          <div class="modal-subtitle" v-html="modalSubtitle"></div>
        </div>

        <div class="modal-body" v-html="modalBody"></div>

        <button
          class="modal-btn-confirm"
          :style="{
            backgroundColor: showSuccess ? '#52c41a' : confirmButtonColor,
            opacity: loading && !showSuccess ? 0.7 : 1,
            cursor: loading ? 'not-allowed' : 'pointer'
          }"
          :disabled="loading"
          @click="handleConfirm"
        >
          <span v-if="showSuccess" class="success-content">
            <svg class="success-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M4 10L8 14L16 6" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ successText }}
          </span>
          <span v-else-if="loading" class="loading-content">
            <svg class="loading-spinner" width="18" height="18" viewBox="0 0 50 50">
              <circle cx="25" cy="25" r="20" fill="none" stroke="white" stroke-width="5" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
            </svg>
            处理中...
          </span>
          <span v-else>{{ confirmButtonText }}</span>
        </button>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useOrderStore } from '@/stores/order'

const orderStore = useOrderStore()

const visible = ref(false)
const modalTitle = ref('')
const modalSubtitle = ref('')
const modalBody = ref('')
const confirmButtonText = ref('确定完成')
const confirmButtonColor = ref('#1890ff')
const successText = ref('上传成功')
const targetOrderId = ref(null)
const targetStatus = ref('completed')
const loading = ref(false)
const showSuccess = ref(false)

// 计算文本缩放
const calculateTextScale = (text, maxChars = 13.5, isHighlightMode = true) => {
  if (!text) return 1
  let len = 0

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    if (char.match(/[一-龥]/)) {
      len += 1
    } else if (isHighlightMode && char.match(/[a-zA-Z0-9.]/)) {
      if (char.match(/[A-Z]/)) len += 1.8
      else if (char.match(/[0-9]/)) len += 1.4
      else len += 1.1
    } else {
      if (char.match(/[A-Z]/)) len += 0.9
      else if (char.match(/[0-9]/)) len += 0.7
      else len += 0.55
    }
  }

  if (len <= maxChars) return 1
  const scale = maxChars / len
  return Math.max(scale, 0.35)
}

// 打开弹窗
const open = (order, status) => {
  targetOrderId.value = order.id
  targetStatus.value = status

  modalTitle.value = `${order.order_client || '未命名'}订单`
  modalSubtitle.value = `单据日期 &nbsp; ${order.date || '未知时间'}`

  const goodsLines = (order.goods_name || '').split('\n').filter(l => l.trim() !== '')

  const renderLine = (line) => {
    const lineScale = calculateTextScale(line, 13.5, true)
    const renderScale = Math.min(lineScale, 1.15)
    const formattedLine = line.replace(/([a-zA-Z0-9.]+)/g, `<span class="text-red-large" style="font-size: calc(30px * ${renderScale}); font-weight: bold;">$1</span>`)
    return `<div class="modal-product" style="font-size: calc(20px * ${renderScale}); font-weight: bold; white-space: nowrap; height: 40px; display: flex; align-items: center;">${formattedLine}</div>`
  }

  let goodsHtml = ''
  if (goodsLines.length === 0) {
    goodsHtml = '<div class="modal-product" style="color:#999; font-size: 18px;">无详细货物内容</div>'
  } else if (goodsLines.length > 7) {
    const half = Math.ceil(goodsLines.length / 2)
    const col1 = goodsLines.slice(0, half).map(renderLine).join('')
    const col2 = goodsLines.slice(half).map(renderLine).join('')
    goodsHtml = `
      <div style="display: flex; gap: 24px;">
        <div style="flex: 1; border-right: 1px dashed #d9d9d9; padding-right: 16px; overflow: hidden;">${col1}</div>
        <div style="flex: 1; overflow: hidden;">${col2}</div>
      </div>
    `
  } else {
    goodsHtml = goodsLines.map(renderLine).join('')
  }

  modalBody.value = goodsHtml

  if (status === 'pending') {
    confirmButtonText.value = '确认撤销至未完成状态'
    confirmButtonColor.value = '#ff4d4f'
    successText.value = '撤销成功'
  } else {
    confirmButtonText.value = '确定完成'
    confirmButtonColor.value = '#1890ff'
    successText.value = '上传成功'
  }

  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 确认操作
const handleConfirm = async () => {
  if (loading.value) return

  loading.value = true
  try {
    await orderStore.updateOrderById(targetOrderId.value, { status: targetStatus.value })
    showSuccess.value = true

    setTimeout(() => {
      showSuccess.value = false
      loading.value = false
      handleClose()
      window.dispatchEvent(new CustomEvent('refresh-orders'))
    }, 1500)
  } catch (error) {
    loading.value = false
    alert('流转操作异常')
  }
}

// 暴露方法
defineExpose({
  open
})

// 监听全局事件
onMounted(() => {
  window.addEventListener('trigger-status-confirm', (e) => {
    open(e.detail.order, e.detail.status)
  })
})
</script>

<style scoped>
.loading-content,
.success-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.success-icon {
  animation: scaleIn 0.3s ease-out;
}

@keyframes scaleIn {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.modal-btn-confirm {
  transition: all 0.3s ease;
}

.modal-btn-confirm:disabled {
  cursor: not-allowed;
}
</style>
