<template>
  <div
    id="fabContainer"
    class="fab-container"
    :class="{ active: menuOpen }"
    :style="containerStyle"
  >
    <!-- 悬浮菜单 -->
    <div class="fab-menu">
      <div
        v-if="showMaterialButton"
        class="fab-item"
        @click="handleAction('addMaterial')"
      >
        录入原材料数据
      </div>
      <div
        v-if="showOrderButton"
        class="fab-item"
        @click="handleAction('addOrder')"
      >
        录入订单信息
      </div>
      <div class="fab-item" @click="handleAction('searchOrder')">
        搜索订单
      </div>
      <div
        v-if="userStore.hasPerm('system.user_manage')"
        class="fab-item"
        @click="handleAction('manageUsers')"
      >
        账户控制
      </div>
      <div class="fab-item" style="color: #ff4d4f;" @click="handleLogout">
        退出登录
      </div>
    </div>

    <!-- AI 气泡 -->
    <div
      id="aiSpeechBubble"
      class="ai-speech-bubble"
      :class="{ show: bubbleVisible }"
      v-html="bubbleContent"
    ></div>

    <!-- AI 小圆脸 -->
    <div
      id="fabMain"
      class="ai-face"
      @mousedown="dragStart"
      @touchstart="dragStart"
      @click="toggleMenu"
    >
      <div class="face-inner">
        <div class="eye left"></div>
        <div class="eye right"></div>
        <div class="mouth"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'

const router = useRouter()
const userStore = useUserStore()
const orderStore = useOrderStore()

const menuOpen = ref(false)
const bubbleVisible = ref(false)
const bubbleContent = ref('准备接入大模型...')

const isDragging = ref(false)
const hasDragged = ref(false)
const isMouseDownOnFab = ref(false)

const containerStyle = ref({
  right: '40px',
  bottom: '40px',
  left: 'auto',
  top: 'auto'
})

let startX = 0
let startY = 0
let initialX = 0
let initialY = 0
let filterTimeoutLock = null

// 计算是否显示按钮
const showOrderButton = computed(() => {
  return orderStore.currentTab === 0 && userStore.hasPerm('pending.add')
})

const showMaterialButton = computed(() => {
  return orderStore.currentTab === 3 && userStore.hasPerm('material.add')
})

// 切换菜单
const toggleMenu = () => {
  if (!hasDragged.value) {
    menuOpen.value = !menuOpen.value
  }
}

// 打开新建订单弹窗
const openCreateOrder = () => {
  menuOpen.value = false
  window.dispatchEvent(new CustomEvent('open-create-order-modal'))
}

// 打开上传原材料弹窗
const openUploadMaterial = () => {
  menuOpen.value = false
  window.dispatchEvent(new CustomEvent('open-upload-material-modal'))
}

// 拖拽开始
const dragStart = (e) => {
  if (e.type === 'touchstart') {
    startX = e.touches[0].clientX
    startY = e.touches[0].clientY
  } else {
    startX = e.clientX
    startY = e.clientY
  }

  const container = document.getElementById('fabContainer')
  if (container) {
    initialX = container.offsetLeft
    initialY = container.offsetTop
  }

  isDragging.value = true
  hasDragged.value = false
  isMouseDownOnFab.value = true
}

// 拖拽中
const drag = (e) => {
  if (!isDragging.value || !isMouseDownOnFab.value) return

  let clientX, clientY
  if (e.type === 'touchmove') {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    clientX = e.clientX
    clientY = e.clientY
  }

  const dx = clientX - startX
  const dy = clientY - startY

  if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
    hasDragged.value = true
  }

  if (hasDragged.value) {
    e.preventDefault()

    let newX = initialX + dx
    let newY = initialY + dy

    const maxX = window.innerWidth - 70
    const maxY = window.innerHeight - 70

    newX = Math.max(0, Math.min(newX, maxX))
    newY = Math.max(0, Math.min(newY, maxY))

    containerStyle.value = {
      left: newX + 'px',
      top: newY + 'px',
      right: 'auto',
      bottom: 'auto'
    }
  }
}

// 拖拽结束
const dragEnd = () => {
  if (!isDragging.value) return
  isDragging.value = false
  isMouseDownOnFab.value = false
}

// 处理按钮点击
const handleAction = (action) => {
  menuOpen.value = false

  switch (action) {
    case 'addMaterial':
      window.dispatchEvent(new CustomEvent('open-upload-material-modal'))
      break
    case 'addOrder':
      window.dispatchEvent(new CustomEvent('open-create-order-modal'))
      break
    case 'searchOrder':
      window.dispatchEvent(new CustomEvent('open-search-order-modal'))
      break
    case 'manageUsers':
      window.dispatchEvent(new CustomEvent('open-user-manage-modal'))
      break
  }
}

// 退出登录
const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    userStore.logout()
    window.location.reload()
  }
}

// 显示欢迎气泡
const showWelcomeBubble = () => {
  bubbleContent.value = `欢迎回来，${userStore.name || userStore.username} 主人！`
  bubbleVisible.value = true
  setTimeout(() => {
    bubbleVisible.value = false
  }, 4000)
}

// 触发日期筛选气泡
const triggerDateFilter = (filterType) => {
  const tipText = filterType === 'material'
    ? '主人，请选择要查看的【原材料】范围：'
    : '主人，请选择要查看的【出库单】范围：'

  bubbleContent.value = `
    <div id="nomiFilterArea" class="nomi-filter-area">
      <span class="nomi-filter-title">${tipText}</span>

      <div class="nomi-date-group">
        <div class="nomi-date-pill">
          <span class="nomi-date-label">从</span>
          <input type="date" id="nomiFilterStart" class="nomi-date-input">
        </div>

        <div class="nomi-date-pill">
          <span class="nomi-date-label">至</span>
          <input type="date" id="nomiFilterEnd" class="nomi-date-input">
        </div>
      </div>

      <div class="nomi-btn-group">
        <button id="btnNomiPastWeek" class="nomi-btn-secondary">最近一周</button>
        <button id="btnNomiDateConfirm" class="nomi-btn-confirm">开始筛选</button>
      </div>
    </div>
  `

  bubbleVisible.value = true

  setTimeout(() => {
    const btnConfirm = document.getElementById('btnNomiDateConfirm')
    const btnPastWeek = document.getElementById('btnNomiPastWeek')
    const dateStart = document.getElementById('nomiFilterStart')
    const dateEnd = document.getElementById('nomiFilterEnd')

    const executeFilter = (startVal, endVal) => {
      if (filterType === 'material') {
        orderStore.setMaterialDateFilter(startVal, endVal)
      } else {
        orderStore.setDateFilter(startVal, endVal)
      }
      bubbleVisible.value = false
    }

    if (btnConfirm && dateStart && dateEnd) {
      btnConfirm.addEventListener('click', () => {
        const startVal = dateStart.value
        const endVal = dateEnd.value

        if (!startVal || !endVal) {
          alert('请完整选择开始和结束日期哦！')
          return
        }
        if (startVal > endVal) {
          alert('开始日期不能晚于结束日期！')
          return
        }

        executeFilter(startVal, endVal)
      })
    }

    if (btnPastWeek) {
      btnPastWeek.addEventListener('click', () => {
        const today = new Date()
        const sevenDaysAgo = new Date()
        sevenDaysAgo.setDate(today.getDate() - 6)

        const formatDate = (d) => {
          const y = d.getFullYear()
          const m = String(d.getMonth() + 1).padStart(2, '0')
          const date = String(d.getDate()).padStart(2, '0')
          return `${y}-${m}-${date}`
        }

        executeFilter(formatDate(sevenDaysAgo), formatDate(today))
      })
    }
  }, 50)
}

// 全局点击关闭菜单
const handleGlobalClick = (e) => {
  const container = document.getElementById('fabContainer')
  if (container && menuOpen.value && !container.contains(e.target)) {
    menuOpen.value = false
  }

  const bubble = document.getElementById('aiSpeechBubble')
  if (bubble && bubbleVisible.value && !bubble.contains(e.target)) {
    bubbleVisible.value = false
  }
}

onMounted(() => {
  // 监听全局拖拽事件
  document.addEventListener('mousemove', drag)
  document.addEventListener('mouseup', dragEnd)
  document.addEventListener('touchmove', drag, { passive: false })
  document.addEventListener('touchend', dragEnd)

  // 监听全局点击
  document.addEventListener('mousedown', handleGlobalClick)
  document.addEventListener('touchstart', handleGlobalClick, { passive: true })

  // 暴露给全局的函数
  window.triggerDateFilterSpeech = triggerDateFilter

  // 延迟显示欢迎气泡
  if (userStore.isLoggedIn) {
    setTimeout(showWelcomeBubble, 1000)
  }
})

onUnmounted(() => {
  document.removeEventListener('mousemove', drag)
  document.removeEventListener('mouseup', dragEnd)
  document.removeEventListener('touchmove', drag)
  document.removeEventListener('touchend', dragEnd)
  document.removeEventListener('mousedown', handleGlobalClick)
  document.removeEventListener('touchstart', handleGlobalClick)

  delete window.triggerDateFilterSpeech
})

// 监听 tab 切换更新按钮显示
watch(() => orderStore.currentTab, () => {
  // Tab 切换时自动关闭菜单
  menuOpen.value = false
})
</script>

<style scoped>
/* 样式已在全局 CSS 中定义 */
</style>
