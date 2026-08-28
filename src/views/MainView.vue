<template>
  <div id="mainSection">
    <!-- 顶部导航栏 -->
    <div class="nav-bar" :class="{ 'nav-bar-hidden': navBarHidden }">
      <div
        v-for="(tab, index) in tabs"
        :key="index"
        class="nav-item"
        :class="{ active: nomiStore.currentTab === index }"
        @click="switchTab(index)"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- Tab 0: 未完成订单 -->
    <div
      id="tab-0"
      class="tab-pane"
      :class="{ active: nomiStore.currentTab === 0 }"
    >
      <OrderList
        :orders="pendingOrders"
        status-type="pending"
        @complete="handleComplete"
        @edit="handleEdit"
        @copy="handleCopy"
      />
    </div>

    <!-- Tab 1: 已完成订单 -->
    <div
      id="tab-1"
      class="tab-pane"
      :class="{ active: nomiStore.currentTab === 1 }"
    >
      <OrderList
        :orders="completedOrders"
        status-type="completed"
        @uncomplete="handleUncomplete"
        @ship="handleShip"
        @delete="handleDelete"
        @copy="handleCopy"
      />
    </div>

    <!-- Tab 2: 已出库订单 -->
    <div
      id="tab-2"
      class="tab-pane"
      :class="{ active: nomiStore.currentTab === 2 }"
    >
      <ShippedOrderList
        :orders="shippedOrders"
        :filter-start="orderStore.nomiActiveFilterStart"
        :filter-end="orderStore.nomiActiveFilterEnd"
        @refresh="fetchOrders"
        @audit="handleAudit"
        @manage-receipt="handleManageReceipt"
        @view-receipt="handleViewReceipt"
      />
    </div>

    <!-- Tab 3: 原材料数据 -->
    <div
      id="tab-3"
      class="tab-pane"
      :class="{ active: nomiStore.currentTab === 3 }"
    >
      <div style="padding: 40px 20px;">
        <MaterialDisplay />
      </div>
    </div>

    <!-- 各种弹窗组件 -->
    <ConfirmModal ref="confirmModal" />
    <ShipOrderModal ref="shipOrderModal" />
    <ShippedOrderActionModal ref="shippedActionModal" />
    <OrderFormModal ref="orderFormModal" />
    <UploadMaterialModal ref="uploadMaterialModal" />
    <SearchOrderModal ref="searchOrderModal" />
    <SmartCalculator ref="smartCalculator" />

    <!-- 小圆智能助手 -->
    <NomiFloatingAI
      :user-role="userStore.role"
      @create-order="handleCreateOrder"
      @create-material="handleCreateMaterial"
      @search="handleSearchOrder"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useOrderStore } from '@/stores/order'
import { useUserStore } from '@/stores/user'
import { useNomiStore } from '@/stores/nomi'
import OrderList from '@/views/front/OrderList.vue'
import ShippedOrderList from '@/views/front/ShippedOrderList.vue'
import MaterialDisplay from '@/views/front/MaterialDisplay.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'
import ShippedOrderActionModal from '@/components/common/ShippedOrderActionModal.vue'
import SearchOrderModal from '@/components/common/SearchOrderModal.vue'
import SmartCalculator from '@/components/common/SmartCalculator.vue'
import ShipOrderModal from '@/components/front/ShipOrderModal.vue'
import OrderFormModal from '@/components/front/OrderFormModal.vue'
import UploadMaterialModal from '@/components/front/UploadMaterialModal.vue'
import UserManage from '@/views/admin/UserManage.vue'
import NomiFloatingAI from '@/components/common/NomiFloatingAI.vue'

const orderStore = useOrderStore()
const userStore = useUserStore()
const nomiStore = useNomiStore()

const navBarHidden = ref(false)

// 弹窗引用
const confirmModal = ref(null)
const shipOrderModal = ref(null)
const shippedActionModal = ref(null)
const orderFormModal = ref(null)
const uploadMaterialModal = ref(null)
const searchOrderModal = ref(null)
const userManageModal = ref(null)
const smartCalculator = ref(null)

const tabs = [
  { label: '未完成订单' },
  { label: '已完成订单' },
  { label: '已出库订单' },
  { label: '原材料数据' }
]

// 计算属性：根据状态筛选订单
const pendingOrders = computed(() => {
  return orderStore.allOrders
    .filter(o => o.status === 'pending')
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
})

const completedOrders = computed(() => {
  return orderStore.allOrders
    .filter(o => o.status === 'completed')
    .sort((a, b) => (b.completed_date || '').localeCompare(a.completed_date || ''))
})

const shippedOrders = computed(() => {
  let orders = orderStore.allOrders.filter(o => o.status === 'shipped')

  // 日期筛选逻辑
  const { nomiActiveFilterStart, nomiActiveFilterEnd } = orderStore

  if (nomiActiveFilterStart && nomiActiveFilterEnd) {
    const startT = new Date(nomiActiveFilterStart.replace(/-/g, '/')).getTime()
    const endT = new Date(nomiActiveFilterEnd.replace(/-/g, '/')).getTime() + 86400000 - 1

    orders = orders.filter(o => {
      const dateStr = o.shipped_date || o.completed_date || ''
      if (!dateStr) return false
      const t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime()
      return t >= startT && t <= endT
    })
  } else {
    // 默认显示最近3天
    const now = new Date()
    const threeDaysAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2).getTime()

    orders = orders.filter(o => {
      const dateStr = o.shipped_date || o.completed_date || ''
      if (!dateStr) return false
      const t = new Date(dateStr.substring(0, 10).replace(/-/g, '/')).getTime()
      return t >= threeDaysAgo
    })
  }

  return orders
})

// 切换 Tab
const switchTab = (index) => {
  nomiStore.currentTab = index
  orderStore.setCurrentTab(index)

  if (index === 0 || index === 1 || index === 2) {
    fetchOrders()
  }

  // 自动触发日期筛选气泡
  if (index === 2) {
    setTimeout(() => {
      window.triggerDateFilterSpeech?.('shipped')
    }, 100)
  } else if (index === 3) {
    setTimeout(() => {
      window.triggerDateFilterSpeech?.('material')
    }, 100)
  }
}

// 获取订单数据
const fetchOrders = async () => {
  if (nomiStore.currentTab !== 0 && nomiStore.currentTab !== 1 && nomiStore.currentTab !== 2) return

  try {
    await orderStore.fetchOrders()
  } catch (error) {
    console.error('Failed to fetch orders:', error)
  }
}

// 处理完成订单
const handleComplete = (orderId) => {
  const order = orderStore.allOrders.find(o => o.id === orderId)
  if (order) {
    window.triggerStatusConfirm(order, 'completed')
  }
}

// 处理撤销完成
const handleUncomplete = (orderId) => {
  const order = orderStore.allOrders.find(o => o.id === orderId)
  if (order) {
    window.triggerStatusConfirm(order, 'pending')
  }
}

// 处理出库
const handleShip = (orderId) => {
  window.triggerShipModal(orderId)
}

// 处理编辑
const handleEdit = (orderId) => {
  window.openEditOrderModal(orderId)
}

// 处理删除
const handleDelete = (orderId) => {
  window.deleteOrder(orderId)
}

// 处理复制
const handleCopy = (orderId) => {
  window.copyOrderInfo(orderId)
}

// 处理审核（已出库订单）
const handleAudit = (orderId) => {
  window.triggerShippedActionModal(orderId, 'audit')
}

// 处理管理回单
const handleManageReceipt = (orderId) => {
  window.triggerShippedActionModal(orderId, 'receipt')
}

// 处理查看回单
const handleViewReceipt = (orderId) => {
  window.triggerShippedActionModal(orderId, 'view_receipt')
}

// 获取当前 Tab 名称（供小圆组件使用）
const getCurrentTabName = () => {
  const tabNames = ['pending', 'completed', 'shipped', 'materials']
  return tabNames[nomiStore.currentTab] || 'pending'
}

// 小圆组件：创建订单
const handleCreateOrder = () => {
  orderFormModal.value?.open()
}

// 小圆组件：创建原材料
const handleCreateMaterial = () => {
  uploadMaterialModal.value?.open()
}

// 小圆组件：搜索订单
const handleSearchOrder = () => {
  searchOrderModal.value?.open()
}

// 小圆组件：日期筛选
const handleDateFilter = ({ type, startDate, endDate }) => {
  if (type === 'shipped') {
    orderStore.nomiActiveFilterStart = startDate
    orderStore.nomiActiveFilterEnd = endDate
  } else if (type === 'material') {
    // 触发原材料日期筛选事件
    window.dispatchEvent(new CustomEvent('filter-material-date', {
      detail: { startDate, endDate }
    }))
  }
}

// 小圆组件：账户管理
const handleUserManage = () => {
  userManageModal.value?.open()
}

// 移动端导航栏隐藏逻辑
let lastScrollY = 0
let ticking = false

const handleScroll = () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      const currentScrollY = window.scrollY || document.documentElement.scrollTop

      if (window.innerWidth <= 768) {
        if (currentScrollY > lastScrollY && currentScrollY > 100) {
          navBarHidden.value = true
        } else {
          navBarHidden.value = false
        }
      } else {
        navBarHidden.value = false
      }

      lastScrollY = currentScrollY
      ticking = false
    })
    ticking = true
  }
}

onMounted(() => {
  // 加载订单数据
  fetchOrders()

  // 3秒自动轮询
  const pollingInterval = setInterval(() => {
    fetchOrders()
  }, 3000)

  // 监听滚动事件
  window.addEventListener('scroll', handleScroll, { passive: true })

  // 🖱️ 鼠标滚轮横向滚动 (Tab 0 和 Tab 1)
  const tab0 = document.getElementById('tab-0')
  const tab1 = document.getElementById('tab-1')

  const handleHorizontalScroll = (e) => {
    if (e.deltaY !== 0) {
      e.preventDefault()
      e.currentTarget.scrollLeft += e.deltaY
    }
  }

  if (tab0) {
    tab0.addEventListener('wheel', handleHorizontalScroll, { passive: false })
  }
  if (tab1) {
    tab1.addEventListener('wheel', handleHorizontalScroll, { passive: false })
  }

  // 监听刷新事件
  window.addEventListener('refresh-orders', fetchOrders)

  // 监听切换 tab 事件
  window.addEventListener('switch-tab', (e) => {
    if (e.detail && e.detail.index !== undefined) {
      switchTab(e.detail.index)
    }
  })

  // 挂载全局函数（供子组件和原始逻辑调用）
  window.triggerStatusConfirm = (order, status) => {
    confirmModal.value?.open(order, status)
  }
  window.triggerShipModal = (orderId) => {
    shipOrderModal.value?.open(orderId)
  }
  window.triggerShippedActionModal = (orderId, mode) => {
    shippedActionModal.value?.open(orderId, mode)
  }
  window.openShippedOrderActionModal = (orderId, mode, imgUrl) => {
    shippedActionModal.value?.open(orderId, mode)
  }
  window.openEditOrderModal = (orderId) => {
    orderFormModal.value?.openEdit(orderId)
  }
  window.openUploadMaterialModal = () => {
    uploadMaterialModal.value?.open()
  }
  window.openSearchOrderModal = () => {
    searchOrderModal.value?.open()
  }
  window.openUserManageModal = () => {
    userManageModal.value?.open()
  }
  window.toggleSmartCalculator = () => {
    smartCalculator.value?.toggle()
  }

  // 日期筛选气泡触发
  window.triggerDateFilterSpeech = (filterType) => {
    const nomiStore = useNomiStore()
    nomiStore.showDateFilterBubble(filterType)
  }

  // 复制订单信息到剪贴板
  window.copyOrderInfo = (orderId) => {
    const order = orderStore.allOrders.find(o => o.id === orderId)
    if (!order) return

    // 判断是否是员工角色
    const isEmployee = userStore.role === 'employee' || userStore.role === 'operator'

    // 订单类型文本
    const typeText = (order.type == 1) ? '绝缘订单' : '中固订单'

    // 名称字符数量限制
    let nameLimit = (order.type == 1) ? 8 : 9
    let shortGoodsName = (order.goods_name || '').replace(/\n/g, '').trim().substring(0, nameLimit)

    // 构建复制文本（原生格式）
    let clipText = `【${typeText}】\n`
    if (order.receiver_name) clipText += `姓名：${order.receiver_name}\n`
    if (!isEmployee && order.receiver_phone) clipText += `电话：${order.receiver_phone}\n`
    if (order.receiver_address) clipText += `地址：${order.receiver_address}\n`
    if (shortGoodsName) clipText += `名称：${shortGoodsName}\n`
    if (order.goods_weight) clipText += `重量：${order.goods_weight}\n`
    if (order.goods_quantity) clipText += `件数：${order.goods_quantity}\n`
    if (order.goods_packaging) clipText += `包装：${order.goods_packaging}\n`
    if (!isEmployee && order.logistics_service) clipText += `服务：${order.logistics_service}\n`
    if (order.remark) clipText += `备注：${order.remark}\n`

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(clipText).then(() => {
        alert('✅ 极简物流信息已成功复制！')
      }).catch(() => {
        fallbackCopyTextToClipboard(clipText)
      })
    } else {
      fallbackCopyTextToClipboard(clipText)
    }
  }

  // 降级复制方案
  const fallbackCopyTextToClipboard = (text) => {
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.top = '0'
    textArea.style.left = '0'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    try {
      document.execCommand('copy')
      alert('✅ 极简物流信息已成功复制！')
    } catch (err) {
      alert('复制失败，请手动复制')
    }
    document.body.removeChild(textArea)
  }

  // 删除订单
  window.deleteOrder = async (orderId) => {
    if (!confirm('严重安全警告：您确定要彻底物理删除这条订单记录吗？此操作无法撤销！')) {
      return
    }

    try {
      await orderStore.deleteOrderById(orderId)
      fetchOrders()
    } catch (error) {
      alert('网络异常，删除失败')
    }
  }

  // 清理函数
  onUnmounted(() => {
    clearInterval(pollingInterval)
    window.removeEventListener('scroll', handleScroll)
  })
})
</script>

<style>
/* 全局body样式重置 */
body {
  background-color: #EDF5FC !important;
  overflow-x: hidden !important;
  padding: 160px 60px 80px 60px !important;
  font-size: 18px !important;
}

/* 电脑端横向滚动 */
@media screen and (min-width: 769px) {
  body {
    min-width: 1920px !important;
    overflow: hidden !important;
  }
}

/* 移动端padding调整 */
@media (max-width: 768px) {
  body {
    padding: 160px 16px 20px 16px !important;
    font-size: 15px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
  }
}
</style>

<style scoped>
#mainSection {
  width: 100%;
  min-height: 100vh;
  background: #EDF5FC;
  margin: -160px -60px -80px -60px;
  padding: 160px 60px 80px 60px;
}

.tab-pane {
  display: none;
}

.tab-pane.active {
  display: flex;
  gap: 48px;
  align-items: flex-start;
  justify-content: flex-start;
}

/* Tab 0 和 Tab 1 横向滚动布局 */
#tab-0, #tab-1 {
  flex-wrap: nowrap;
  overflow-x: auto;
  overflow-y: hidden;
  height: calc(100vh - 280px);
  align-items: stretch;
  padding-top: 15px;
  padding-bottom: 32px;
  gap: 64px;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

#tab-0::-webkit-scrollbar,
#tab-1::-webkit-scrollbar {
  display: none;
}

/* 电脑端横向滚动增强 */
@media screen and (min-width: 769px) {
  #tab-0.active, #tab-1.active {
    display: flex !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    gap: 30px !important;
    width: 100vw !important;
    margin-left: -60px !important;
    padding: 0 20px 20px 20px !important;
    box-sizing: border-box !important;
    height: calc(100vh - 260px) !important;
    align-items: stretch !important;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  #tab-0.active::-webkit-scrollbar,
  #tab-1.active::-webkit-scrollbar {
    display: none !important;
  }

  /* 右侧隐形卡片留白 */
  #tab-0.active::after,
  #tab-1.active::after {
    content: "" !important;
    display: block !important;
    flex: 0 0 20px !important;
    height: 100% !important;
    pointer-events: none !important;
  }
}

/* Tab 2 和 Tab 3 保持默认布局 */
#tab-2, #tab-3 {
  flex-wrap: wrap;
  height: auto;
  overflow: visible;
  gap: 32px;
}

/* 移动端响应 */
@media (max-width: 768px) {
  #tab-0, #tab-1 {
    height: auto !important;
    flex-wrap: wrap !important;
    overflow: visible !important;
    padding-bottom: 0 !important;
    gap: 24px !important;
  }
}
</style>
