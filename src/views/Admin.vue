<template>
  <div class="admin-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="system-name">后台管理系统</div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <ul class="nav-list">
            <template v-for="(item, index) in menuItems" :key="index">
              <!-- 没有子菜单的项 -->
              <li
                v-if="!item.children"
                :class="['nav-item', { active: currentPath === item.path }]"
                @click="navigateTo(item.path)"
              >
                <span class="nav-icon" v-html="item.icon"></span>
                <span class="nav-label">{{ item.label }}</span>
              </li>

              <!-- 有子菜单的项 -->
              <li v-else class="nav-item-group">
                <div
                  :class="['nav-item', 'has-children', {
                    expanded: isMenuExpanded(index),
                    active: isChildActive(item.children)
                  }]"
                  @click="toggleMenu(index)"
                >
                  <span class="nav-icon" v-html="item.icon"></span>
                  <span class="nav-label">{{ item.label }}</span>
                  <span class="nav-arrow">
                    <svg
                      :class="{ rotated: isMenuExpanded(index) }"
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="currentColor"
                    >
                      <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="2" fill="none"/>
                    </svg>
                  </span>
                </div>

                <!-- 子菜单 -->
                <ul
                  v-show="isMenuExpanded(index)"
                  class="nav-submenu"
                >
                  <li
                    v-for="child in item.children"
                    :key="child.path"
                    :class="['nav-subitem', { active: currentPath === child.path }]"
                    @click="navigateTo(child.path)"
                  >
                    <span v-if="child.icon" class="nav-subicon" v-html="child.icon"></span>
                    {{ child.label }}
                  </li>
                </ul>
              </li>
            </template>
          </ul>
        </div>
      </nav>
    </aside>

    <!-- 右侧主体区域 -->
    <div class="main-wrapper">
      <!-- 顶部栏 -->
      <header class="top-header">
        <div class="header-left">
          <button class="sidebar-toggle-btn" @click="toggleSidebar" :title="isSidebarCollapsed ? '展开菜单' : '收起菜单'">
            <span v-if="!isSidebarCollapsed" class="hamburger-icon">
              <span class="line"></span>
              <span class="line"></span>
              <span class="line"></span>
            </span>
            <span v-else class="arrow-icon">←</span>
          </button>
          <h2 class="header-page-title">{{ currentMenuLabel }}</h2>
        </div>

        <div class="header-right">
          <div class="header-actions">
            <button
              v-if="showOrderDraftShortcut"
              :class="['order-draft-shortcut', `is-${orderDraftStore.draftMode}`]"
              type="button"
              :title="`返回${orderDraftStore.draftTitle}`"
              :aria-label="`返回${orderDraftStore.draftTitle}`"
              @click="restoreOrderDraft"
            >
              <span class="order-draft-shortcut-mark" aria-hidden="true">
                {{ orderDraftStore.draftMark }}
              </span>
              <span class="order-draft-shortcut-label">
                {{ orderDraftStore.draftShortLabel }}
              </span>
            </button>
            <component v-if="headerActions" :is="headerActions"></component>
          </div>

          <div class="header-icons">
            <button class="icon-btn" title="系统公告">
              <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </button>
            <button class="icon-btn" title="审核通知">
              <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              <span class="badge" v-if="notificationCount > 0">{{ notificationCount }}</span>
            </button>
            <button class="icon-btn notification" title="留言消息">
              <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span class="badge" v-if="notificationCount > 0">{{ notificationCount }}</span>
            </button>
            <div class="user-info">
              <div class="user-avatar">
                <svg class="avatar-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <span class="user-name">{{ userStore.name || userStore.username || '用户' }}</span>
            </div>
            <button class="logout-btn" @click="logout">退出系统</button>
          </div>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <component
            :is="Component"
            ref="activeContentRef"
            @create="handleStockRecordCreate"
            @view-detail="handleStockRecordViewDetail"
            @red-flush="handleStockRecordRedFlush"
            @print="handleStockRecordPrint"
            @review="handleStockRecordReview"
            @reverse-audit="handleStockRecordReverseAudit"
            @restart="handleStockRecordRestart"
            @delete="handleStockRecordDelete"
          />
        </router-view>
      </main>
    </div>

    <!-- 弹窗组件 -->
    <ShippedOrderActionModal ref="shippedActionModal" @refresh="handleRefresh" />
    <ShipOrderModal ref="shipOrderModal" @refresh="handleRefresh" />
    <StockInOrderModal ref="stockRecordModal" @saved="handleStockRecordSaved" />
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useOrderDraftStore } from '@/stores/orderDraft'
import request from '@/api/request'
import ShippedOrderActionModal from '@/components/common/ShippedOrderActionModal.vue'
import ShipOrderModal from '@/components/front/ShipOrderModal.vue'
import StockInOrderModal from '@/components/common/StockInOrderModal.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const orderDraftStore = useOrderDraftStore()

const notificationCount = ref(3)
const shippedActionModal = ref(null)
const shipOrderModal = ref(null)
const stockRecordModal = ref(null)
const activeContentRef = ref(null)

// 侧边栏折叠状态
const isSidebarCollapsed = ref(false)

// 切换侧边栏
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

// 用于子组件注入的按钮操作
const headerActions = ref(null)

// 提供给子组件的方法
provide('setHeaderActions', (actions) => {
  headerActions.value = actions
})

// 注册全局方法供子组件调用
onMounted(() => {
  window.triggerShippedActionModal = (orderId, action) => {
    if (shippedActionModal.value) {
      shippedActionModal.value.open(orderId, action)
    }
  }

  window.triggerShipOrderModal = (orderId) => {
    if (shipOrderModal.value) {
      shipOrderModal.value.open(orderId)
    }
  }
})

// 处理刷新事件
const handleRefresh = () => {
  // 调用子组件的刷新方法
  if (window.refreshUnifiedOrderList) {
    window.refreshUnifiedOrderList()
  }
}

const handleStockRecordCreate = ({ mode } = {}) => {
  if (mode === 'OUTBOUND') {
    router.push('/admin/orders/create')
    return
  }
  stockRecordModal.value?.open({ type: 'raw-material' })
}

const handleStockRecordViewDetail = () => {
  // The reusable list owns its drawer; the event is available for page-level analytics.
}

const handleStockRecordSaved = () => {
  activeContentRef.value?.reload?.()
}

const handleStockRecordRedFlush = async record => {
  if (!record || record.status !== 'pending') return

  if (record.source?.status && record.source.status !== 'draft') {
    window.alert('当前单据不可直接作废，请从原业务单据处理。')
    return
  }

  if (record.source?.type && !['raw-material', 'finished-product'].includes(record.source.type)) {
    window.alert('出库单暂未提供红冲接口，请从销售订单处理。')
    return
  }

  if (!window.confirm(`确定将单据“${record.documentNo}”作废吗？`)) return

  try {
    await request({ url: `/stock-inbounds/${record.id}`, method: 'DELETE' })
    activeContentRef.value?.closeDrawer?.()
    await activeContentRef.value?.reload?.()
  } catch (error) {
    window.alert(error?.response?.data?.message || error?.message || '单据作废失败，请稍后重试。')
  }
}

const handleStockRecordPrint = () => {
  // StockRecordList triggers the browser print dialog after emitting this event.
}

// 审核相关动作目前由流水组件即时维护状态；这些监听器保留给后端补充独立审核接口时接入。
const handleStockRecordReview = () => {}
const handleStockRecordReverseAudit = () => {}
const handleStockRecordRestart = () => {}
const handleStockRecordDelete = () => {}

// 提供给子组件的 ship 方法
provide('handleShip', (orderId) => {
  if (shipOrderModal.value) {
    shipOrderModal.value.open(orderId)
  }
})

// SVG 图标定义
const icons = {
  home: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  package: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
  cart: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
  chart: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>',
  trending: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
  users: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  dollar: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
  briefcase: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
  settings: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24"/></svg>'
}

const menuItems = ref([
  {
    label: '首页',
    icon: icons.home,
    path: '/admin/dashboard'
  },
  {
    label: '商品',
    icon: icons.package,
    children: [
      { label: '商品列表', path: '/admin/products' },
      { label: '原材料列表', path: '/admin/materials' }
    ]
  },
  {
    label: '订单',
    icon: icons.cart,
    children: [
      { label: '销售订单', path: '/admin/orders' },
      { label: '物流列表', path: '/admin/orders/logistics' },
      { label: '退货订单', path: '/admin/orders/completed' }
    ]
  },
  {
    label: '库存',
    icon: icons.chart,
    children: [
      { label: '成品库存', path: '/admin/inventory' },
      { label: '原材料库存', path: '/admin/inventory/materials' },
      { label: '入库记录', path: '/admin/stock/in' },
      { label: '出库记录', path: '/admin/stock/out' },
      { label: '供应商管理', path: '/admin/suppliers' },
      { label: '仓库管理', path: '/admin/inventory/warehouse' }
    ]
  },
  {
    label: '运营',
    icon: icons.trending,
    children: [
      { label: '数据统计', path: '/admin/analytics' },
      { label: '营销活动', path: '/admin/marketing' }
    ]
  },
  {
    label: '客户',
    icon: icons.users,
    children: [
      { label: '客户列表', path: '/admin/customers' },
      { label: '客户分组', path: '/admin/customers/groups' }
    ]
  },
  {
    label: '财务',
    icon: icons.dollar,
    children: [
      { label: '应收欠款', path: '/admin/finance/receivables' },
      { label: '收款历史', path: '/admin/finance/payment-history' },
      { label: '物流/专车对账', path: '/admin/finance/logistics-truck' },
      { label: '快运/快递对账', path: '/admin/finance/express-courier' }
    ]
  },
  {
    label: '人事行政',
    icon: icons.briefcase,
    children: [
      { label: '员工管理', path: '/admin/hr/employees' },
      { label: '公司资料', path: '/admin/hr/company' },
      { label: '检测报告', path: '/admin/hr/reports' }
    ]
  },
  {
    label: '设置',
    icon: icons.settings,
    children: [
      { label: '门店管理', path: '/admin/stores' },
      { label: '系统设置', path: '/admin/settings' },
      { label: '用户管理', path: '/admin/users' },
      { label: '角色管理', path: '/admin/roles' }
    ]
  }
])

const expandedMenus = ref([])

const toggleMenu = (index) => {
  const idx = expandedMenus.value.indexOf(index)
  if (idx > -1) {
    expandedMenus.value.splice(idx, 1)
  } else {
    expandedMenus.value.push(index)
  }
}

const isMenuExpanded = (index) => {
  return expandedMenus.value.includes(index)
}

const isChildActive = (children) => {
  if (!children) return false
  return children.some(child => child.path === currentPath.value)
}

const currentPath = computed(() => route.path)
const showOrderDraftShortcut = computed(() => {
  const isOrderFormRoute = route.name === 'admin-orders-create' || route.name === 'admin-orders-edit'
  return orderDraftStore.hasDraft && !isOrderFormRoute
})

const currentMenuLabel = computed(() => {
  // 特殊路由处理
  if (currentPath.value === '/admin/orders/create') {
    return '订单/新增订单'
  }
  if (currentPath.value.startsWith('/admin/orders/edit/')) {
    return '订单/修改订单'
  }

  // 先尝试从子菜单中查找
  for (const item of menuItems.value) {
    if (item.children) {
      const child = item.children.find(c => c.path === currentPath.value)
      if (child) return `${item.label}/${child.label}`
    }
  }
  // 再尝试从主菜单中查找
  const item = menuItems.value.find(item => item.path === currentPath.value)
  return item ? item.label : '数据看板'
})

const navigateTo = (path) => {
  router.push(path)
}

const restoreOrderDraft = () => {
  if (orderDraftStore.draftPath) {
    router.push(orderDraftStore.draftPath)
  }
}

const logout = () => {
  if (confirm('确定要退出系统吗？')) {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.admin-container {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --page-bg: #f4f7f8;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;

  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--page-bg);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  color: var(--text);
  font-size: 14px;
}

/* 侧边栏折叠状态 */
.admin-container.sidebar-collapsed .sidebar {
  width: 0;
  overflow: hidden;
}

.admin-container.sidebar-collapsed .main-wrapper {
  margin-left: 0;
}

/* 左侧边栏样式 */
.sidebar {
  width: 240px;
  background: #0f172a;
  color: #f8fafc;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(15, 23, 42, 0.08);
  transition: width 0.3s ease;
}

.sidebar-header {
  padding: 20px;
  background: #0B0E14;
  border-bottom: 1px solid rgba(248, 250, 252, 0.08);
}

.system-name {
  font-size: 18px;
  font-weight: 650;
  color: #f8fafc;
  letter-spacing: 0.3px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item-group {
  margin-bottom: 2px;
}

.nav-item {
  padding: 11px 14px;
  cursor: pointer;
  transition: all 0.18s ease;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  border-radius: 7px;
  display: flex;
  align-items: center;
  gap: 11px;
  position: relative;
  margin-bottom: 2px;
}

.nav-item.has-children {
  justify-content: space-between;
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
}

.nav-arrow {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.nav-arrow svg {
  transition: transform 0.2s ease;
}

.nav-arrow svg.rotated {
  transform: rotate(180deg);
}

.nav-item:hover {
  background: rgba(15, 159, 120, 0.12);
  color: #e2e8f0;
}

.nav-item.active {
  background: var(--accent);
  color: #ffffff;
}

.nav-item.expanded {
  background: rgba(248, 250, 252, 0.05);
  color: #e2e8f0;
}

/* 子菜单 */
.nav-submenu {
  list-style: none;
  padding: 4px 0;
  margin: 0;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

.nav-subitem {
  padding: 9px 14px 9px 45px;
  cursor: pointer;
  transition: all 0.18s ease;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 2px;
}

.nav-subicon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.nav-subitem:hover {
  background: rgba(15, 159, 120, 0.1);
  color: #e2e8f0;
}

.nav-subitem.active {
  background: rgba(15, 159, 120, 0.2);
  color: #4FD1C5;
  font-weight: 600;
}

/* 右侧主体区域 */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏样式 */
.top-header {
  height: 62px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.sidebar-toggle-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.18s ease;
  padding: 0;
  color: var(--text-secondary);
}

.sidebar-toggle-btn:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

.sidebar-toggle-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.hamburger-icon {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 16px;
}

.hamburger-icon .line {
  width: 100%;
  height: 2px;
  background-color: currentColor;
  border-radius: 2px;
  transition: all 0.18s ease;
}

.arrow-icon {
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
}

.header-page-title {
  font-size: 18px;
  font-weight: 650;
  color: var(--text);
  margin: 0;
  letter-spacing: 0.2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.order-draft-shortcut {
  height: 36px;
  padding: 0 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.18s ease;
}

.order-draft-shortcut:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}

.order-draft-shortcut:focus-visible {
  outline: 2px solid #dc2626;
  outline-offset: 2px;
}

.order-draft-shortcut.is-edit {
  background: #fff7ed;
  color: #d97706;
  border: 1px solid #fdba74;
}

.order-draft-shortcut.is-edit:hover {
  background: #ffedd5;
  border-color: #fbbf24;
  color: #b45309;
}

.order-draft-shortcut-mark {
  display: none;
}

.order-draft-shortcut-label {
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.header-icons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-btn {
  position: relative;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.18s ease;
  padding: 0;
  color: var(--text-secondary);
}

.icon-btn:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

.icon-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.icon-svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 999px;
  min-width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.3);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 10px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-icon {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: var(--accent-dark);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.logout-btn {
  height: 36px;
  padding: 0 14px;
  background: var(--panel-bg);
  color: var(--text);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.logout-btn:hover {
  background: #fef2f2;
  border-color: #fecaca;
  color: #dc2626;
}

.logout-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: var(--page-bg);
}

/* 响应式 */
@media (max-width: 1280px) {
  .header-page-title {
    font-size: 16px;
  }

  .header-actions {
    gap: 8px;
  }
}

@media (max-width: 780px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
  }

  .admin-container.sidebar-collapsed .sidebar {
    width: 0;
  }

  .main-wrapper {
    margin-left: 0;
  }

  .top-header {
    padding: 0 12px;
    gap: 10px;
  }

  .header-left {
    gap: 12px;
  }

  .header-page-title {
    font-size: 15px;
  }

  .user-name {
    display: none;
  }

  .main-content {
    padding: 12px;
  }
}
</style>
