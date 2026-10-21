<template>
  <div
    ref="fabContainer"
    class="gugu-touch-tools"
    :style="position ? { left: `${position.x}px`, top: `${position.y}px` } : {}"
    @keydown.esc="closeTools"
  >
    <GuGuLauncher
      floating
      :expanded="nomiStore.isMenuActive"
      aria-controls="gugu-touch-menu"
      @pointerdown="handleDragStart"
      @pointermove="handleDrag"
      @pointerup="handleDragEnd"
      @pointercancel="handleDragEnd"
      @lostpointercapture="handleDragEnd"
      @click="handleClick"
    />

    <div
      v-if="nomiStore.isMenuActive"
      id="gugu-touch-menu"
      ref="menuRef"
      class="gugu-touch-menu"
      :style="menuPosition"
      role="menu"
      aria-label="固固助手工具"
      @keydown="handleMenuKeydown"
    >
      <button v-if="showAddMaterial" type="button" role="menuitem" @click="handleCreateMaterial">
        <PackagePlus :size="17" aria-hidden="true" />
        录入原材料出库
      </button>
      <button v-if="canFilter" type="button" role="menuitem" @click="openDateFilter">
        <CalendarRange :size="17" aria-hidden="true" />
        筛选
      </button>
      <button type="button" class="is-danger" role="menuitem" @click="handleLogout">
        <LogOut :size="17" aria-hidden="true" />
        退出登录
      </button>
    </div>

    <div
      v-if="nomiStore.showSpeechBubble"
      ref="speechBubble"
      class="gugu-touch-bubble"
      :style="bubblePosition"
      :role="nomiStore.speechBubbleType === 'text' ? 'status' : 'region'"
      aria-label="固固助手提示"
      @mouseenter="nomiStore.stopFilterTimer"
      @mouseleave="handleBubbleMouseLeave"
      @focusin="nomiStore.stopFilterTimer"
      @focusout="handleBubbleFocusOut"
    >
      <div v-if="nomiStore.speechBubbleType === 'text'">{{ nomiStore.speechBubbleContent }}</div>
      <div v-else-if="nomiStore.speechBubbleType === 'filter-prompt'">
        主人我可以帮你<button type="button" class="gugu-filter-link" @click="openDateFilter">筛选</button>哦
      </div>
      <form v-else-if="nomiStore.speechBubbleType === 'filter'" class="gugu-filter-form" @submit.prevent="handleConfirmFilter">
        <strong>{{ nomiStore.filterType === 'material' ? '原材料日期范围' : '物流订单日期范围' }}</strong>
        <div class="gugu-date-range">
          <label>
            <span>从</span>
            <input v-model="filterStartDate" type="date" aria-label="开始日期">
          </label>
          <label>
            <span>至</span>
            <input v-model="filterEndDate" type="date" aria-label="结束日期">
          </label>
        </div>
        <div class="gugu-filter-actions">
          <button type="button" @click="handlePastWeek">最近一周</button>
          <button type="button" @click="handleResetFilter">恢复默认</button>
          <button type="submit" class="is-primary">开始筛选</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { CalendarRange, LogOut, PackagePlus } from '@lucide/vue'
import { useNomiStore } from '@/stores/nomi'
import { useUserStore } from '@/stores/user'
import GuGuLauncher from './GuGuLauncher.vue'

const emit = defineEmits(['create-material', 'date-filter'])
const nomiStore = useNomiStore()
const userStore = useUserStore()
const showAddMaterial = computed(() => nomiStore.currentTab === 3 && userStore.hasPerm('touch.material.create'))
const canFilter = computed(() => nomiStore.currentTab === 2 || nomiStore.currentTab === 3)
const fabContainer = ref(null)
const menuRef = ref(null)
const speechBubble = ref(null)
const position = ref(null)
const menuPosition = ref({ left: '12px', top: '12px' })
const bubblePosition = ref({ left: '12px', top: '12px' })
const filterStartDate = ref('')
const filterEndDate = ref('')
let dragState
let hasDragged = false
let speechInterval

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(value, maximum))

// 浮层使用视口坐标，机器人拖到边缘时菜单和筛选框仍留在屏幕内。
const updatePopoverPositions = async () => {
  await nextTick()
  if (!fabContainer.value) return
  const anchor = fabContainer.value.getBoundingClientRect()
  const viewportWidth = document.documentElement.clientWidth
  const viewportHeight = document.documentElement.clientHeight
  const place = (element, left, top) => {
    const rect = element.getBoundingClientRect()
    return {
      left: `${clamp(left(rect), 12, Math.max(12, viewportWidth - rect.width - 12))}px`,
      top: `${clamp(top(rect), 12, Math.max(12, viewportHeight - rect.height - 12))}px`
    }
  }
  if (menuRef.value) {
    menuPosition.value = place(menuRef.value, rect => anchor.right - rect.width, rect => (
      anchor.top >= rect.height + 24 ? anchor.top - rect.height - 12 : anchor.bottom + 12
    ))
  }
  if (speechBubble.value) {
    bubblePosition.value = place(speechBubble.value, rect => (
      anchor.left >= rect.width + 24 ? anchor.left - rect.width - 12 : anchor.right + 12
    ), rect => anchor.top + (anchor.height - rect.height) / 2)
  }
}

watch(() => nomiStore.filterType, () => {
  filterStartDate.value = ''
  filterEndDate.value = ''
})
watch([
  () => nomiStore.isMenuActive,
  () => nomiStore.showSpeechBubble,
  () => nomiStore.speechBubbleType,
  () => nomiStore.speechBubbleContent,
  position
], updatePopoverPositions)

const handleBubbleMouseLeave = () => {
  if (nomiStore.speechBubbleType !== 'text' && !speechBubble.value?.contains(document.activeElement)) {
    nomiStore.startFilterTimer()
  }
}
const handleBubbleFocusOut = event => {
  if (nomiStore.speechBubbleType !== 'text' && !speechBubble.value?.contains(event.relatedTarget)) {
    nomiStore.startFilterTimer()
  }
}

const handleDragStart = event => {
  if (!event.isPrimary || event.button !== 0 || !fabContainer.value) return
  const rect = fabContainer.value.getBoundingClientRect()
  dragState = {
    pointerId: event.pointerId,
    handle: event.currentTarget,
    x: event.clientX,
    y: event.clientY,
    left: rect.left,
    top: rect.top
  }
  hasDragged = false
  event.currentTarget.setPointerCapture(event.pointerId)
}
const handleDrag = event => {
  if (!dragState || event.pointerId !== dragState.pointerId) return
  const dx = event.clientX - dragState.x
  const dy = event.clientY - dragState.y
  if (Math.abs(dx) > 5 || Math.abs(dy) > 5) hasDragged = true
  if (!hasDragged) return
  event.preventDefault()
  position.value = {
    x: clamp(dragState.left + dx, 0, Math.max(0, window.innerWidth - fabContainer.value.offsetWidth)),
    y: clamp(dragState.top + dy, 0, Math.max(0, window.innerHeight - fabContainer.value.offsetHeight))
  }
}
const handleDragEnd = event => {
  if (!dragState || (event?.pointerId != null && event.pointerId !== dragState.pointerId)) return
  const { handle, pointerId } = dragState
  dragState = null
  if (handle.hasPointerCapture(pointerId)) handle.releasePointerCapture(pointerId)
}
const handleClick = event => {
  if (!hasDragged || event.detail === 0) nomiStore.toggleMenu()
}
const closeTools = () => {
  nomiStore.closeMenu()
  nomiStore.hideSpeechBubble()
}
const handleClickOutside = event => {
  if (!fabContainer.value?.contains(event.target)) closeTools()
}
const handleMenuKeydown = event => {
  const buttons = [...menuRef.value.querySelectorAll('button')]
  const current = buttons.indexOf(document.activeElement)
  let next
  if (event.key === 'ArrowDown') next = (current + 1) % buttons.length
  else if (event.key === 'ArrowUp') next = (current - 1 + buttons.length) % buttons.length
  else if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = buttons.length - 1
  else return
  event.preventDefault()
  buttons[next]?.focus()
}
const handleViewportResize = () => {
  handleDragEnd()
  if (position.value && fabContainer.value) {
    position.value = {
      x: clamp(position.value.x, 0, Math.max(0, window.innerWidth - fabContainer.value.offsetWidth)),
      y: clamp(position.value.y, 0, Math.max(0, window.innerHeight - fabContainer.value.offsetHeight))
    }
  }
  updatePopoverPositions()
}

const handleCreateMaterial = () => {
  nomiStore.closeMenu()
  emit('create-material')
}
const openDateFilter = () => {
  if (!canFilter.value) return
  nomiStore.closeMenu()
  nomiStore.showDateFilterBubble(nomiStore.currentTab === 2 ? 'shipped' : 'material')
}
const handleLogout = async () => {
  nomiStore.closeMenu()
  if (confirm('确定要退出登录吗？')) {
    await userStore.logout()
    window.location.reload()
  }
}
const formatDate = date => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
const executeFilter = () => {
  emit('date-filter', {
    type: nomiStore.filterType,
    startDate: filterStartDate.value,
    endDate: filterEndDate.value
  })
  nomiStore.hideSpeechBubble()
}
const handlePastWeek = () => {
  const today = new Date()
  const start = new Date(today)
  start.setDate(today.getDate() - 6)
  filterStartDate.value = formatDate(start)
  filterEndDate.value = formatDate(today)
  executeFilter()
}
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
const handleResetFilter = () => {
  filterStartDate.value = ''
  filterEndDate.value = ''
  executeFilter()
}

onMounted(() => {
  position.value = {
    x: Math.max(12, window.innerWidth - (fabContainer.value?.offsetWidth || 70) - 40),
    y: Math.max(12, window.innerHeight - 200)
  }
  document.addEventListener('pointerdown', handleClickOutside)
  window.addEventListener('resize', handleViewportResize)
  window.addEventListener('blur', handleDragEnd)
  speechInterval = setInterval(() => {
    if (!dragState && !nomiStore.isMenuActive) nomiStore.showRandomSpeech()
  }, 30000)
})

onUnmounted(() => {
  handleDragEnd()
  document.removeEventListener('pointerdown', handleClickOutside)
  window.removeEventListener('resize', handleViewportResize)
  window.removeEventListener('blur', handleDragEnd)
  clearInterval(speechInterval)
  closeTools()
})
</script>

<style scoped>
.gugu-touch-tools {
  position: fixed;
  right: 40px;
  bottom: 40px;
  z-index: 10000;
  width: 70px;
  height: 70px;
  color: #172033;
  font-size: 14px;
  line-height: 1.5;
  letter-spacing: 0;
}

.gugu-touch-menu,
.gugu-touch-bubble {
  position: fixed;
  box-sizing: border-box;
  max-width: calc(100vw - 24px);
  max-height: calc(100dvh - 24px);
  overflow-y: auto;
  border: 1px solid #dbe3eb;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14);
  white-space: normal;
  overscroll-behavior: contain;
}

.gugu-touch-menu {
  z-index: 2;
  display: flex;
  width: 210px;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
}

.gugu-touch-menu button {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: #596579;
  font: inherit;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.gugu-touch-menu button:hover {
  background: #e9f8f3;
  color: #08745a;
}

.gugu-touch-menu button.is-danger {
  color: #b4232f;
}

.gugu-touch-menu button.is-danger:hover {
  background: #fff1f2;
}

.gugu-touch-menu svg {
  flex-shrink: 0;
}

.gugu-touch-bubble {
  width: max-content;
  max-width: min(360px, calc(100vw - 24px));
  padding: 16px;
  color: #596579;
  font-size: 14px;
  overflow-wrap: anywhere;
}

.gugu-filter-link {
  padding: 0 3px;
  border: 0;
  background: transparent;
  color: #08745a;
  font: inherit;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}

.gugu-filter-form {
  display: flex;
  width: 326px;
  max-width: 100%;
  flex-direction: column;
  gap: 12px;
}

.gugu-filter-form strong {
  color: #172033;
  font-size: 14px;
}

.gugu-date-range {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.gugu-date-range label {
  display: flex;
  min-width: 0;
  min-height: 40px;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  background: #fff;
  color: #596579;
  font-size: 12px;
}

.gugu-date-range label:focus-within {
  border-color: #0f9f78;
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.1);
}

.gugu-date-range input {
  min-width: 0;
  width: 100%;
  flex: 1;
  padding: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: #172033;
  font: inherit;
  font-variant-numeric: tabular-nums;
  color-scheme: light;
}

.gugu-filter-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.gugu-filter-actions button {
  min-width: 0;
  min-height: 40px;
  padding: 6px;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  background: #fff;
  color: #596579;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.gugu-filter-actions button:hover {
  border-color: #a9e5d2;
  background: #e9f8f3;
  color: #08745a;
}

.gugu-filter-actions .is-primary {
  border-color: #0f9f78;
  background: #0f9f78;
  color: #fff;
}

.gugu-filter-actions .is-primary:hover {
  border-color: #08745a;
  background: #08745a;
  color: #fff;
}

.gugu-touch-tools button:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

@media (max-width: 360px) {
  .gugu-date-range {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
