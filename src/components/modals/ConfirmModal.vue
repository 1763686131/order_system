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
          :style="{ backgroundColor: confirmButtonColor }"
          @click="handleConfirm"
        >
          {{ confirmButtonText }}
        </button>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { updateOrderStatus } from '@/api/orders'

const visible = ref(false)
const modalTitle = ref('')
const modalSubtitle = ref('')
const modalBody = ref('')
const confirmButtonText = ref('确定完成')
const confirmButtonColor = ref('#1890ff')
const targetOrderId = ref(null)
const targetStatus = ref('completed')

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
  } else {
    confirmButtonText.value = '确定完成'
    confirmButtonColor.value = '#1890ff'
  }

  visible.value = true
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 确认操作
const handleConfirm = async () => {
  try {
    await updateOrderStatus(targetOrderId.value, targetStatus.value)
    handleClose()
    window.dispatchEvent(new CustomEvent('refresh-orders'))
  } catch (error) {
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
/* 样式已在全局 CSS 中定义 */
</style>
