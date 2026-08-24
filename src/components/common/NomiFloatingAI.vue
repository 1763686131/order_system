<template>
  <div
    ref="fabContainer"
    class="fab-container"
    :class="{ active: nomiStore.isMenuActive }"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
  >
    <!-- 主按钮 - 使用原始的 ai-face 结构 -->
    <div
      ref="fabMain"
      class="ai-face"
      @mousedown="handleDragStart"
      @touchstart="handleDragStart"
      @click="handleClick"
    >
      <div class="face-inner">
        <div class="eye left"></div>
        <div class="eye right"></div>
        <div class="mouth"></div>
      </div>
    </div>

    <!-- 菜单项 -->
    <div class="fab-menu">
      <div
        v-if="showAddMaterial"
        class="fab-item"
        @click="handleCreateMaterial"
      >
        录入原材料数据
      </div>

      <div
        v-if="showAddOrder"
        class="fab-item"
        @click="handleCreateOrder"
      >
        录入订单信息
      </div>

      <div
        class="fab-item"
        @click="handleSearch"
      >
        搜索订单
      </div>

      <div
        v-if="userStore.hasPerm('system.user_manage')"
        class="fab-item"
        @click="handleUserManage"
      >
        账户控制
      </div>

      <div
        class="fab-item"
        style="color: #ff4d4f;"
        @click="handleLogout"
      >
        退出登录
      </div>
    </div>

    <!-- 气泡提示 -->
    <div
      v-if="nomiStore.showSpeechBubble"
      id="aiSpeechBubble"
      ref="speechBubble"
      class="ai-speech-bubble show"
      @mouseenter="nomiStore.stopFilterTimer"
      @mouseleave="nomiStore.startFilterTimer"
    >
      <!-- 文字气泡 -->
      <div v-if="nomiStore.speechBubbleType === 'text'">
        {{ nomiStore.speechBubbleContent }}
      </div>

      <!-- 日期筛选气泡 -->
      <div v-else-if="nomiStore.speechBubbleType === 'filter'" class="nomi-filter-area">
        <span class="nomi-filter-title">
          {{ nomiStore.filterType === 'material' ? '主人，请选择要查看的【原材料】范围：' : '主人，请选择要查看的【出库单】范围：' }}
        </span>

        <div class="nomi-date-group">
          <div class="nomi-date-pill">
            <span class="nomi-date-label">从</span>
            <input v-model="filterStartDate" type="date" class="nomi-date-input">
          </div>

          <div class="nomi-date-pill">
            <span class="nomi-date-label">至</span>
            <input v-model="filterEndDate" type="date" class="nomi-date-input">
          </div>
        </div>

        <div class="nomi-btn-group">
          <button class="nomi-btn-secondary" @click="handlePastWeek">最近一周</button>
          <button class="nomi-btn-confirm" @click="handleConfirmFilter">开始筛选</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNomiStore } from '@/stores/nomi'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  userRole: {
    type: String,
    default: ''
  },
  hasUserManagePerm: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'create-order',
  'create-material',
  'search',
  'user-manage'
])

const router = useRouter()
const route = useRoute()
const nomiStore = useNomiStore()
const userStore = useUserStore()

// 根据权限和当前tab控制菜单项显示
const showAddOrder = computed(() => {
  // 在原材料页面隐藏（防止用户点错，不分权限）
  // Tab 3: 原材料数据
  if (nomiStore.currentTab === 3) return false

  // 其他页面根据权限显示
  return userStore.hasPerm('pending.add')
})

const showAddMaterial = computed(() => {
  // 在订单页面（未完成、已完成、已出库）隐藏（防止用户点错，不分权限）
  // Tab 0: 未完成订单, Tab 1: 已完成订单, Tab 2: 已出库订单
  if (nomiStore.currentTab === 0 || nomiStore.currentTab === 1 || nomiStore.currentTab === 2) return false

  // 其他页面根据权限显示
  return userStore.hasPerm('material.add')
})

// 拖拽相关状态
const fabContainer = ref(null)
const fabMain = ref(null)
const speechBubble = ref(null)

const position = ref({ x: null, y: null })
const isDragging = ref(false)
const hasDragged = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const initialPos = ref({ x: 0, y: 0 })

// 日期筛选
const filterStartDate = ref('')
const filterEndDate = ref('')

// 拖拽开始
const handleDragStart = (e) => {
  const clientX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX
  const clientY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY

  dragStart.value = { x: clientX, y: clientY }
  initialPos.value = {
    x: fabContainer.value.offsetLeft,
    y: fabContainer.value.offsetTop
  }

  isDragging.value = true
  hasDragged.value = false

  if (fabMain.value) {
    fabMain.value.style.transition = 'none'
  }
}

// 拖拽中
const handleDrag = (e) => {
  if (!isDragging.value) return

  const clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX
  const clientY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY

  const dx = clientX - dragStart.value.x
  const dy = clientY - dragStart.value.y

  if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
    hasDragged.value = true
  }

  if (hasDragged.value) {
    e.preventDefault()

    let newX = initialPos.value.x + dx
    let newY = initialPos.value.y + dy

    const maxX = window.innerWidth - fabContainer.value.offsetWidth
    const maxY = window.innerHeight - fabContainer.value.offsetHeight

    newX = Math.max(0, Math.min(newX, maxX))
    newY = Math.max(0, Math.min(newY, maxY))

    position.value = { x: newX, y: newY }
  }
}

// 拖拽结束
const handleDragEnd = () => {
  if (!isDragging.value) return

  isDragging.value = false

  if (fabMain.value) {
    fabMain.value.style.transition = 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)'
  }
}

// 点击事件
const handleClick = () => {
  if (!hasDragged.value) {
    nomiStore.toggleMenu()
  }
}

// 点击外部关闭
const handleClickOutside = (e) => {
  if (fabContainer.value && !fabContainer.value.contains(e.target)) {
    nomiStore.closeMenu()

    if (nomiStore.showSpeechBubble && speechBubble.value && !speechBubble.value.contains(e.target)) {
      nomiStore.hideSpeechBubble()
    }
  }
}

// 录入原材料
const handleCreateMaterial = () => {
  nomiStore.closeMenu()
  emit('create-material')
}

// 录入订单
const handleCreateOrder = () => {
  nomiStore.closeMenu()
  emit('create-order')
}

// 搜索
const handleSearch = () => {
  nomiStore.closeMenu()
  emit('search')
}

// 账户管理
const handleUserManage = () => {
  nomiStore.closeMenu()
  emit('user-manage')
}

// 退出登录
const handleLogout = () => {
  nomiStore.closeMenu()
  if (confirm('确定要退出登录吗？')) {
    userStore.logout()
    window.location.reload()
  }
}

// 格式化日期
const formatDate = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// 最近一周
const handlePastWeek = () => {
  const today = new Date()
  const sevenDaysAgo = new Date()
  sevenDaysAgo.setDate(today.getDate() - 6)

  filterStartDate.value = formatDate(sevenDaysAgo)
  filterEndDate.value = formatDate(today)

  executeFilter()
}

// 确认筛选
const handleConfirmFilter = () => {
  if (!filterStartDate.value || !filterEndDate.value) {
    alert('请完整选择开始和结束日期哦！')
    return
  }

  if (filterStartDate.value > filterEndDate.value) {
    alert('开始日期不能晚于结束日期！')
    return
  }

  executeFilter()
}

// 执行筛选
const executeFilter = () => {
  window.dispatchEvent(new CustomEvent('date-filter', {
    detail: {
      type: nomiStore.filterType,
      startDate: filterStartDate.value,
      endDate: filterEndDate.value
    }
  }))
  nomiStore.hideSpeechBubble()
}

// 随机语音定时器
let speechInterval = null

onMounted(() => {
  // 设置初始位置
  if (position.value.x === null) {
    position.value = {
      x: window.innerWidth - 80,
      y: window.innerHeight - 200
    }
  }

  // 绑定事件
  document.addEventListener('mousemove', handleDrag, { passive: false })
  document.addEventListener('mouseup', handleDragEnd)
  document.addEventListener('touchmove', handleDrag, { passive: false })
  document.addEventListener('touchend', handleDragEnd)
  document.addEventListener('mousedown', handleClickOutside)
  document.addEventListener('touchstart', handleClickOutside, { passive: true })

  // 启动随机语音
  speechInterval = setInterval(() => {
    if (!hasDragged.value && !isDragging.value) {
      nomiStore.showRandomSpeech()
    }
  }, 30000)
})

onUnmounted(() => {
  // 清理事件
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', handleDragEnd)
  document.removeEventListener('touchmove', handleDrag)
  document.removeEventListener('touchend', handleDragEnd)
  document.removeEventListener('mousedown', handleClickOutside)
  document.removeEventListener('touchstart', handleClickOutside)

  if (speechInterval) {
    clearInterval(speechInterval)
  }
})
</script>

<style scoped>
/* 照搬原始 nomi.css 样式 */
.fab-container {
  position: fixed;
  right: 40px;
  bottom: 40px;
  width: 70px;
  height: 70px;
  z-index: 10000;
}

.fab-menu {
  position: absolute;
  bottom: 85px;
  left: 50%;
  transform: translateX(-50%) translateY(20px) scale(0.5);
  transform-origin: bottom center;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  width: max-content;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.fab-container.active .fab-menu {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(0) scale(1);
  pointer-events: auto;
}

.fab-item {
  background: #ffffff;
  padding: 12px 24px;
  border-radius: 24px;
  color: #1890ff;
  font-size: 16px;
  font-weight: bold;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  border: 1px solid #e6f7ff;
}

.fab-item:hover {
  background: #e6f7ff;
  transform: translateY(-2px);
}

.ai-speech-bubble {
  position: absolute;
  right: 85px;
  bottom: 12px;
  background: #ffffff;
  padding: 18px 20px;
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  font-size: 15px;
  font-weight: bold;
  color: #1A4B84;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transform: translateX(15px);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  min-width: 360px;
}

.ai-speech-bubble::after {
  content: '';
  position: absolute;
  right: -8px;
  bottom: 0;
  width: 0;
  height: 0;
  border-bottom: 12px solid #ffffff;
  border-right: 12px solid transparent;
}

.ai-speech-bubble.show {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
  pointer-events: auto;
}

.ai-face {
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 30% 30%, #2a3b5c, #0f172a);
  border-radius: 50%;
  box-shadow: inset -4px -4px 10px rgba(0,0,0,0.6), inset 2px 2px 8px rgba(255,255,255,0.2), 0 6px 20px rgba(24, 144, 255, 0.4);
  position: relative;
  cursor: grab;
  user-select: none;
  overflow: hidden;
  opacity: 0.5;
  transition: opacity 0.3s ease, transform 0.2s, background 0.4s, box-shadow 0.4s;
}

.fab-container.active .ai-face,
.ai-face:hover {
  opacity: 1;
}

.fab-container.active .ai-face {
  background: radial-gradient(circle at 30% 30%, #5c2a33, #1f0f15);
  box-shadow: inset -4px -4px 10px rgba(0,0,0,0.6), inset 2px 2px 8px rgba(255,255,255,0.2), 0 6px 25px rgba(255, 77, 79, 0.5);
}

.ai-face:active {
  cursor: grabbing;
  transform: scale(0.9);
}

.face-inner {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  animation: floatFace 4s ease-in-out infinite;
}

@keyframes floatFace {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.eye {
  position: absolute;
  top: 22px;
  width: 10px;
  height: 14px;
  background: #00e5ff;
  border-radius: 6px;
  animation: blink 4s infinite;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.eye.left { left: 18px; }
.eye.right { right: 18px; }

@keyframes blink {
  0%, 94%, 98%, 100% { transform: scaleY(1); }
  96% { transform: scaleY(0.1); }
}

.mouth {
  position: absolute;
  top: 42px;
  left: 24px;
  width: 22px;
  height: 10px;
  border: 3px solid #00e5ff;
  border-top: none;
  border-radius: 0 0 20px 20px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.fab-container.active .face-inner {
  animation: jitter 0.15s infinite;
}

.fab-container.active .eye {
  width: 14px;
  height: 14px;
  top: 20px;
  background: transparent;
  border: 3px solid #ff4d4f;
  border-radius: 50%;
  animation: none;
}

.fab-container.active .eye.left { left: 16px; }
.fab-container.active .eye.right { right: 16px; }

.fab-container.active .mouth {
  width: 16px;
  height: 18px;
  top: 42px;
  left: 27px;
  border: 3px solid #ff4d4f;
  border-radius: 50%;
}

@keyframes jitter {
  0%, 100% { transform: translate(0, 0); }
  25% { transform: translate(-1px, 1px); }
  50% { transform: translate(1px, -1px); }
  75% { transform: translate(-1px, -1px); }
}

/* 筛选气泡样式 */
.nomi-filter-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 14px;
  text-align: left;
  pointer-events: auto;
  width: 100%;
  max-width: 340px;
}

.nomi-filter-title {
  font-weight: bold;
  color: #333;
  font-size: 14px;
}

.nomi-date-group {
  display: flex;
  flex-direction: row;
  gap: 8px;
  width: 100%;
}

.nomi-date-pill {
  display: flex;
  align-items: center;
  background: #f0f2f5;
  border-radius: 20px;
  padding: 6px 10px;
  flex: 1;
  min-width: 0;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.nomi-date-pill:hover,
.nomi-date-pill:focus-within {
  background: #e6f7ff;
  border-color: #1890ff;
}

.nomi-date-label {
  color: #888;
  font-size: 12px;
  font-weight: bold;
  margin-right: 6px;
  flex-shrink: 0;
}

.nomi-date-input {
  border: none;
  background: transparent;
  font-size: 12px;
  color: #333;
  outline: none;
  flex: 1;
  min-width: 0;
  font-family: inherit;
  font-weight: bold;
  cursor: pointer;
}

.nomi-btn-group {
  display: flex;
  gap: 8px;
  width: 100%;
  margin-top: 4px;
  align-items: center;
}

.nomi-btn-group button {
  margin: 0;
  height: 36px;
  line-height: 36px;
  padding: 0;
}

.nomi-btn-secondary {
  flex: 1;
  border-radius: 20px;
  background: #E2E9F3;
  color: #5A738E;
  border: none;
  padding: 10px 0;
  font-size: 13px;
  font-weight: bold;
  cursor: pointer;
  outline: none;
  box-shadow: none;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.nomi-btn-secondary:hover {
  background: #d0dae9;
  transform: scale(1.02);
}

.nomi-btn-confirm {
  flex: 1;
  border-radius: 20px;
  background: #D5EFE3;
  color: #4CBCA0;
  border: none;
  padding: 10px 0;
  font-size: 13px;
  font-weight: bold;
  cursor: pointer;
  outline: none;
  box-shadow: none;
  margin-top: 0;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.nomi-btn-confirm:hover {
  background: #bee5d3;
  transform: scale(1.02);
}
</style>
