<template>
  <div class="admin-container">
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
                <span class="nav-icon">{{ item.icon }}</span>
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
                  <span class="nav-icon">{{ item.icon }}</span>
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
          <h2 class="header-page-title">{{ currentMenuLabel }}</h2>
        </div>

        <div class="header-right">
          <div class="header-actions">
            <component v-if="headerActions" :is="headerActions"></component>
          </div>

          <div class="header-icons">
            <div class="icon-item notification">
              <i class="bell-icon">🔔</i>
              <span class="badge" v-if="notificationCount > 0">{{ notificationCount }}</span>
            </div>
            <div class="icon-item cart">
              <i class="cart-icon">🛒</i>
            </div>
            <button class="logout-btn" @click="logout">退出系统</button>
          </div>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </main>
    </div>

    <!-- 弹窗组件 -->
    <ShippedOrderActionModal ref="shippedActionModal" @refresh="handleRefresh" />
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import ShippedOrderActionModal from '@/components/common/ShippedOrderActionModal.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const notificationCount = ref(3)

// 弹窗引用
const shippedActionModal = ref(null)

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
})

// 处理刷新事件
const handleRefresh = () => {
  // 调用子组件的刷新方法
  if (window.refreshUnifiedOrderList) {
    window.refreshUnifiedOrderList()
  }
}

const menuItems = ref([
  {
    label: '首页',
    icon: '🏠',
    path: '/admin/dashboard'
  },
  {
    label: '商品',
    icon: '📦',
    children: [
      { label: '商品列表', path: '/admin/products' },
      { label: '商品分类', path: '/admin/categories' },
      { label: '商品库存', path: '/admin/inventory' }
    ]
  },
  {
    label: '订单',
    icon: '🛒',
    children: [
      { label: '订单列表', path: '/admin/orders' },
      { label: '物流订单列表', path: '/admin/orders/logistics' },
      { label: '已完成订单', path: '/admin/orders/completed' }
    ]
  },
  {
    label: '库存',
    icon: '📊',
    children: [
      { label: '库存管理', path: '/admin/stock' },
      { label: '入库记录', path: '/admin/stock/in' },
      { label: '出库记录', path: '/admin/stock/out' }
    ]
  },
  {
    label: '运营',
    icon: '📈',
    children: [
      { label: '数据统计', path: '/admin/analytics' },
      { label: '营销活动', path: '/admin/marketing' }
    ]
  },
  {
    label: '客户列表',
    icon: '👥',
    children: [
      { label: '客户管理', path: '/admin/customers' },
      { label: '客户分组', path: '/admin/customers/groups' }
    ]
  },
  {
    label: '财务',
    icon: '💰',
    children: [
      { label: '财务报表', path: '/admin/finance' },
      { label: '收支明细', path: '/admin/finance/transactions' }
    ]
  },
  {
    label: '设置',
    icon: '⚙️',
    children: [
      { label: '系统设置', path: '/admin/settings' },
      { label: '用户管理', path: '/admin/users' }
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

const currentMenuLabel = computed(() => {
  // 先尝试从子菜单中查找
  for (const item of menuItems.value) {
    if (item.children) {
      const child = item.children.find(c => c.path === currentPath.value)
      if (child) return child.label
    }
  }
  // 再尝试从主菜单中查找
  const item = menuItems.value.find(item => item.path === currentPath.value)
  return item ? item.label : '数据看板'
})

const navigateTo = (path) => {
  router.push(path)
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
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f5f7fa;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

/* 左侧边栏样式 */
.sidebar {
  width: 240px;
  background: #2c3e50;
  color: #fff;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  padding: 16px 20px;
  background: #1a252f;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.system-name {
  font-size: 18px;
  font-weight: bold;
  color: #fff;
}

.sidebar-nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item-group {
  margin-bottom: 4px;
}

.nav-item {
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s;
  color: #bdc3c7;
  font-size: 14px;
  border-left: 3px solid transparent;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.nav-item.has-children {
  justify-content: space-between;
}

.nav-icon {
  font-size: 18px;
  width: 20px;
  text-align: center;
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
  transition: transform 0.3s;
}

.nav-arrow svg {
  transition: transform 0.3s;
}

.nav-arrow svg.rotated {
  transform: rotate(180deg);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.nav-item.active {
  background: rgba(52, 211, 153, 0.1);
  color: #34d399;
  border-left-color: #34d399;
}

.nav-item.expanded {
  background: rgba(255, 255, 255, 0.05);
}

/* 子菜单 */
.nav-submenu {
  list-style: none;
  padding: 0;
  margin: 0;
  background: rgba(0, 0, 0, 0.1);
  animation: slideDown 0.3s ease;
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
  padding: 10px 20px 10px 52px;
  cursor: pointer;
  transition: all 0.3s;
  color: #95a5a6;
  font-size: 13px;
  border-left: 3px solid transparent;
}

.nav-subitem:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.nav-subitem.active {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  border-left-color: #34d399;
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
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-tab {
  padding: 8px 16px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
}

.header-tab:hover {
  background: #f3f4f6;
  color: #111827;
}

.header-tab.active {
  background: #34d399;
  color: #fff;
  font-weight: 500;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box input {
  width: 280px;
  height: 36px;
  padding: 0 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

.search-box input:focus {
  border-color: #34d399;
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.1);
}

.search-btn {
  height: 36px;
  padding: 0 20px;
  background: #34d399;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.search-btn:hover {
  background: #10b981;
}

.header-icons {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-item {
  position: relative;
  cursor: pointer;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.3s;
}

.icon-item:hover {
  background: #f3f4f6;
}

.icon-item i {
  font-size: 20px;
  font-style: normal;
}

.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: #ef4444;
  color: #fff;
  font-size: 10px;
  padding: 2px 5px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

.logout-btn {
  padding: 8px 16px;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: #dc2626;
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f5f7fa;
}
</style>
