<template>
  <div id="app">
    <!-- 登录页面 -->
    <div v-if="!userStore.isLoggedIn" id="loginSection" class="login-overlay">
      <div class="login-box">
        <h2>系统登录</h2>
        <input
          v-model="loginForm.username"
          placeholder="请输入账号ID"
          @keyup.enter="handleLogin"
        />
        <input
          v-model="loginForm.password"
          type="password"
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
        />
        <button
          class="btn-primary"
          @click="handleLogin"
          style="width: 100%; border-radius: 6px; padding: 12px; border: none; font-weight: bold; cursor: pointer;"
        >
          登 录
        </button>
      </div>
    </div>

    <!-- 主界面 -->
    <div v-else id="mainSection">
      <!-- 顶部导航栏 -->
      <div class="nav-bar" :class="{ 'nav-bar-hidden': navBarHidden }">
        <div
          v-for="(tab, index) in tabs"
          :key="index"
          class="nav-item"
          :class="{ active: currentTab === index }"
          @click="switchTab(index)"
        >
          {{ tab.label }}
        </div>
      </div>

      <!-- Tab 0: 未完成订单 -->
      <div
        id="tab-0"
        class="tab-pane"
        :class="{ active: currentTab === 0 }"
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
        :class="{ active: currentTab === 1 }"
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
        :class="{ active: currentTab === 2 }"
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
        :class="{ active: currentTab === 3 }"
      >
        <MaterialTimeline
          :filter-start="orderStore.nomiMaterialFilterStart"
          :filter-end="orderStore.nomiMaterialFilterEnd"
        />
      </div>

      <!-- AI 悬浮小圆脸 -->
      <NomiFloatingAI />

      <!-- 各种弹窗组件 -->
      <ConfirmModal ref="confirmModal" />
      <ShipOrderModal ref="shipOrderModal" />
      <ShippedOrderActionModal ref="shippedActionModal" />
      <CreateOrderModal ref="createOrderModal" />
      <EditOrderModal ref="editOrderModal" />
      <UploadMaterialModal ref="uploadMaterialModal" />
      <SearchOrderModal ref="searchOrderModal" />
      <UserManage ref="userManageModal" />
      <SmartCalculator ref="smartCalculator" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useOrderStore } from '@/stores/order'
import OrderList from '@/views/front/OrderList.vue'
import ShippedOrderList from '@/views/front/ShippedOrderList.vue'
import MaterialTimeline from '@/components/material/MaterialTimeline.vue'
import NomiFloatingAI from '@/components/layout/NomiFloatingAI.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'
import ShippedOrderActionModal from '@/components/common/ShippedOrderActionModal.vue'
import SearchOrderModal from '@/components/common/SearchOrderModal.vue'
import SmartCalculator from '@/components/common/SmartCalculator.vue'
import ShipOrderModal from '@/components/front/ShipOrderModal.vue'
import CreateOrderModal from '@/components/front/CreateOrderModal.vue'
import EditOrderModal from '@/components/front/EditOrderModal.vue'
import UploadMaterialModal from '@/components/front/UploadMaterialModal.vue'
import UserManage from '@/views/admin/UserManage.vue'

const userStore = useUserStore()
const orderStore = useOrderStore()

const loginForm = ref({
  username: '',
  password: ''
})

const currentTab = ref(0)
const navBarHidden = ref(false)

// 弹窗引用
const confirmModal = ref(null)
const shipOrderModal = ref(null)
const shippedActionModal = ref(null)
const createOrderModal = ref(null)
const editOrderModal = ref(null)
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
  return orderStore.allOrders.filter(o => o.status === 'pending')
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

// 登录处理
const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    alert('请填入账号密码！')
    return
  }

  try {
    const resData = await userStore.login(loginForm.value.username, loginForm.value.password)

    if (resData.success) {
      // 清空 tab 数据缓存
      const tabPanes = document.querySelectorAll('.tab-pane')
      tabPanes.forEach(el => {
        if (el.dataset) el.dataset.hash = ''
      })

      // 加载订单数据
      fetchOrders()

      // 显示欢迎气泡
      setTimeout(() => {
        const speechBubble = document.getElementById('aiSpeechBubble')
        if (speechBubble) {
          speechBubble.textContent = `欢迎回来，${userStore.name || userStore.username} 主人！`
          speechBubble.classList.add('show')
          setTimeout(() => speechBubble.classList.remove('show'), 4000)
        }
      }, 1000)
    } else {
      alert(resData.message || '凭证错误，登录失败')
    }
  } catch (error) {
    console.error('Login error:', error)
    alert('本地服务端连接失败，请检查系统。')
  }
}

// 切换 Tab
const switchTab = (index) => {
  currentTab.value = index
  orderStore.setCurrentTab(index)

  if (index === 0 || index === 1 || index === 2) {
    fetchOrders()
  }
}

// 获取订单数据
const fetchOrders = async () => {
  if (currentTab.value !== 0 && currentTab.value !== 1 && currentTab.value !== 2) return

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
  // 尝试从 localStorage 恢复登录状态
  const savedUser = localStorage.getItem('local_user')
  if (savedUser) {
    try {
      const userData = JSON.parse(savedUser)
      userStore.setUser(userData)
      fetchOrders()
    } catch (e) {
      console.error('Failed to parse user data:', e)
    }
  }

  // 监听滚动事件
  window.addEventListener('scroll', handleScroll, { passive: true })

  // 监听刷新事件
  window.addEventListener('refresh-orders', fetchOrders)
  window.addEventListener('refresh-materials', () => {
    if (currentTab.value === 3) {
      window.location.reload()
    }
  })

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
  window.openEditOrderModal = (orderId) => {
    editOrderModal.value?.open(orderId)
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

  // 复制订单信息到剪贴板
  window.copyOrderInfo = (orderId) => {
    const order = orderStore.allOrders.find(o => o.id === orderId)
    if (!order) return

    let copyText = `订单归属: ${order.order_client || '未命名'}\n`
    copyText += `订单日期: ${order.date || '未知'}\n`
    copyText += `收货人: ${order.receiver_name || '未填'}\n`
    copyText += `电话: ${order.receiver_phone || '未填'}\n`
    copyText += `地址: ${order.receiver_address || '未填'}\n`
    copyText += `货物:\n${order.goods_name || '无'}\n`
    copyText += `包装: ${order.goods_packaging || '无'}\n`
    copyText += `重量: ${order.goods_weight || '无'}\n`
    copyText += `件数: ${order.goods_quantity || '无'}\n`
    copyText += `备注: ${order.remark || '无'}`

    navigator.clipboard.writeText(copyText).then(() => {
      alert('订单信息已复制到剪贴板！')
    }).catch(() => {
      alert('复制失败，请手动复制')
    })
  }

  // 删除订单
  window.deleteOrder = async (orderId) => {
    if (!confirm('安全警告：您确定要彻底物理删除这条订单记录吗？此操作无法撤销！')) {
      return
    }

    try {
      await orderStore.deleteOrderById(orderId)
    } catch (error) {
      alert('网络异常，删除失败')
    }
  }
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style>
/* 全局样式已在 main.css 中导入 */
</style>
