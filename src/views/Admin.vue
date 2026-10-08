<template>
  <div class="admin-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- 左侧边栏 -->
    <aside id="admin-sidebar" class="sidebar">
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

    <button
      v-if="isMobileViewport && !isSidebarCollapsed"
      class="sidebar-backdrop"
      type="button"
      aria-label="关闭菜单"
      @click="closeSidebar"
    ></button>

    <!-- 右侧主体区域 -->
    <div class="main-wrapper">
      <!-- 顶部栏 -->
      <header class="top-header" :class="{ 'is-document-docking': Boolean(dockingDocument) }">
        <div class="header-left">
          <button
            class="sidebar-toggle-btn"
            type="button"
            aria-controls="admin-sidebar"
            :aria-expanded="!isSidebarCollapsed"
            @click="toggleSidebar"
            :title="isSidebarCollapsed ? '展开菜单' : '收起菜单'"
          >
            <span v-if="!isSidebarCollapsed" class="hamburger-icon">
              <span class="line"></span>
              <span class="line"></span>
              <span class="line"></span>
            </span>
            <span v-else class="arrow-icon">→</span>
          </button>
          <h2 class="header-page-title">{{ currentMenuLabel }}</h2>
        </div>

        <div class="header-right">
          <TransitionGroup name="document-dock" tag="div" class="header-actions">
            <button v-for="draft in dockedDocuments" :key="draft.type" :data-dock-type="draft.type" :class="['document-dock-shortcut', `is-${draft.type}`, { 'is-docking': dockingDocument?.type === draft.type, 'is-arriving': receivedDockType === draft.type }]" type="button" :disabled="Boolean(dockingDocument)" :title="`返回${draft.title}`" :aria-label="`返回${draft.title}`" @click="restoreDockedDocument(draft)">
              <FilePenLine v-if="draft.type === 'edit'" class="document-dock-icon" :size="18" :stroke-width="1.7" aria-hidden="true" />
              <FilePlus2 v-else-if="['sale', 'purchase-order'].includes(draft.type)" class="document-dock-icon" :size="18" :stroke-width="1.7" aria-hidden="true" />
              <RotateCcw v-else-if="['sale-return', 'purchase-return'].includes(draft.type)" class="document-dock-icon" :size="18" :stroke-width="1.7" aria-hidden="true" />
              <PackageCheck v-else class="document-dock-icon" :size="18" :stroke-width="1.7" aria-hidden="true" />
              <span class="document-dock-dot" aria-hidden="true"></span>
              <span v-if="dockingDocument?.type === draft.type || receivedDockType === draft.type" class="document-dock-feedback" role="status">{{ dockingDocument?.type === draft.type ? '收起到这里' : '已收起 · 点击继续' }}</span>
            </button>
          </TransitionGroup>

          <div class="header-icons">
            <button v-if="!isMobileViewport" class="icon-btn" title="系统公告">
              <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </button>
            <button
              v-if="canOpenLogisticsCopySettings && !isMobileViewport"
              class="icon-btn"
              type="button"
              title="物流复制字段设置"
              aria-label="打开物流复制字段设置"
              @click="openLogisticsCopySettings"
            >
              <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M4 7h10M18 7h2M4 17h2M10 17h10"></path>
                <circle cx="16" cy="7" r="2"></circle>
                <circle cx="8" cy="17" r="2"></circle>
              </svg>
            </button>
            <MessageInbox
              ref="notificationInboxRef"
              mode="notifications"
              @open-change="handleNotificationInboxOpenChange"
              @open-notification="openNotification"
            />
            <MessageInbox
              ref="messageInboxRef"
              mode="messages"
              @open-change="handleMessageInboxOpenChange"
              @open-chat="openChat"
            />

            <DirectoryPanel
              ref="directoryPanelRef"
              class="mobile-directory-menu"
              @open-change="handleDirectoryOpenChange"
              @open-chat="openChat"
            />

            <div class="user-profile">
              <button
                class="user-info"
                type="button"
                aria-label="查看个人详细信息"
              >
                <div class="user-avatar">
                  <img
                    v-if="userStore.avatarUrl && !avatarLoadFailed"
                    :src="userStore.avatarUrl"
                    alt=""
                    @error="handleAvatarError"
                  >
                  <svg v-else class="avatar-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>
                <span class="user-name">{{ userDisplayName }}</span>
              </button>

              <section class="user-detail-card" aria-label="个人详细信息">
                <div class="detail-avatar">
                  <img
                    v-if="userStore.avatarUrl && !avatarLoadFailed"
                    :src="userStore.avatarUrl"
                    :alt="`${userDisplayName}的头像`"
                    @error="handleAvatarError"
                  >
                  <svg v-else class="detail-avatar-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>

                <strong class="detail-name">{{ userDisplayName }}</strong>

                <div class="detail-contact">
                  <div class="detail-field">
                    <span>电话</span>
                    <strong>{{ userStore.phone || '未填写' }}</strong>
                  </div>
                  <div class="detail-field">
                    <span>职位</span>
                    <strong>{{ userStore.position || '未设置' }}</strong>
                  </div>
                </div>

                <div class="detail-permission">
                  <span>权限信息</span>
                  <strong>{{ permissionSummary }}</strong>
                </div>
              </section>
            </div>

            <div
              ref="accountMenuRef"
              class="account-menu"
              @keydown.esc="closeAccountMenu"
            >
              <button
                class="icon-btn account-menu-trigger"
                type="button"
                title="账户菜单"
                aria-label="打开账户菜单"
                aria-controls="account-action-menu"
                :aria-expanded="accountMenuOpen"
                @click.stop="toggleAccountMenu"
              >
                <svg class="icon-svg account-menu-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="5" r="1.6" fill="currentColor" stroke="none"/>
                  <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/>
                  <circle cx="12" cy="19" r="1.6" fill="currentColor" stroke="none"/>
                </svg>
              </button>

              <Transition name="account-menu">
                <div
                  v-if="accountMenuOpen"
                  id="account-action-menu"
                  class="account-menu-panel"
                  role="menu"
                  aria-label="账户操作"
                >
                  <template v-if="isMobileViewport">
                    <button
                      class="account-menu-item account-menu-mobile-action"
                      type="button"
                      role="menuitem"
                      @click="closeAccountMenu"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M12 3v18M3 12h18"/>
                        <path d="M5 5h14v14H5z"/>
                      </svg>
                      <span>系统公告</span>
                    </button>

                    <button
                      v-if="canOpenLogisticsCopySettings"
                      class="account-menu-item account-menu-mobile-action"
                      type="button"
                      role="menuitem"
                      @click="openLogisticsCopySettings"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M4 7h10M18 7h2M4 17h2M10 17h10"></path>
                        <circle cx="16" cy="7" r="2"></circle>
                        <circle cx="8" cy="17" r="2"></circle>
                      </svg>
                      <span>物流复制字段设置</span>
                    </button>

                    <button
                      class="account-menu-item account-menu-mobile-action"
                      type="button"
                      role="menuitem"
                      @click="directoryPanelRef?.open?.(); closeAccountMenu()"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M7 3h11a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/>
                        <path d="M5 8H3M5 12H3M5 16H3"/>
                        <circle cx="13" cy="9" r="2.2"/>
                        <path d="M9.5 17c.5-2.1 1.7-3.2 3.5-3.2s3 1.1 3.5 3.2"/>
                      </svg>
                      <span>通讯录</span>
                    </button>
                  </template>

                  <button
                    class="account-menu-item account-menu-logout"
                    type="button"
                    role="menuitem"
                    @click="logout"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M10 17l5-5-5-5"/>
                      <path d="M15 12H3"/>
                      <path d="M15 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/>
                    </svg>
                    <span>退出系统</span>
                  </button>
                </div>
              </Transition>
            </div>
          </div>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="main-content" :class="{ 'purchase-list-content': route.meta.documentForm || ['/admin/purchase/suppliers', '/admin/purchase/orders', '/admin/purchase/inbound'].includes(route.path) }">
        <router-view v-slot="{ Component }">
          <component
            :is="Component"
            :key="route.meta.documentForm ? route.fullPath : undefined"
            ref="activeContentRef"
            @close="handleDocumentClose"
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
    <StockInOrderModal ref="stockRecordModal" @saved="handleStockRecordSaved" />
    <LogisticsCopySettingsDialog
      v-if="canOpenLogisticsCopySettings"
      :visible="logisticsCopySettingsVisible"
      @close="closeLogisticsCopySettings"
    />
    <ChatWindow
      v-model="chatWindowOpen"
      :contact="activeChatContact"
      @message-sent="messageInboxRef?.refresh()"
      @open-contact="openChat"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { FilePenLine, FilePlus2, PackageCheck, RotateCcw } from '@lucide/vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useOrderDraftStore } from '@/stores/orderDraft'
import { useDocumentDraftStore } from '@/stores/documentDraft'
import { animateDocumentDock, cancelDocumentDockAnimations, waitForDocumentReady } from '@/utils/documentDockAnimation'
import request from '@/api/request'
import {
  ADMIN_ROUTE_BRANCH_PERMISSIONS,
  ADMIN_ROUTE_PERMISSIONS
} from '@/utils/adminAccess'
import {
  ADMIN_DEPARTMENT_PERMISSIONS,
  ADMIN_EMPLOYEE_PERMISSIONS,
  ADMIN_LOGISTICS_COPY_PERMISSIONS
} from '@/utils/accessControl'
import ChatWindow from '@/components/admin/ChatWindow.vue'
import DirectoryPanel from '@/components/admin/DirectoryPanel.vue'
import MessageInbox from '@/components/admin/MessageInbox.vue'
import ShippedOrderActionModal from '@/components/common/ShippedOrderActionModal.vue'
import StockInOrderModal from '@/components/common/StockInOrderModal.vue'
import LogisticsCopySettingsDialog from '@/components/admin/LogisticsCopySettingsDialog.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const orderDraftStore = useOrderDraftStore()
const documentDraftStore = useDocumentDraftStore()
let removeDocumentDockGuard = () => {}
let removeDocumentDockAfterHook = () => {}
let releaseDockedForm = null
let dockTransitionId = 0
let dockFeedbackTimer
const dockingDocument = ref(null)
const dockDestinationPath = ref('')
const receivedDockType = ref('')

const shippedActionModal = ref(null)
const stockRecordModal = ref(null)
const activeContentRef = ref(null)
const avatarLoadFailed = ref(false)
const accountMenuRef = ref(null)
const accountMenuOpen = ref(false)
const directoryPanelRef = ref(null)
const messageInboxRef = ref(null)
const notificationInboxRef = ref(null)
const chatWindowOpen = ref(false)
const activeChatContact = ref(null)
const logisticsCopySettingsVisible = ref(false)
const canOpenLogisticsCopySettings = computed(() =>
  userStore.canAccessAdmin &&
  userStore.hasPerm(ADMIN_LOGISTICS_COPY_PERMISSIONS.ENTRY) &&
  userStore.hasPerm(ADMIN_LOGISTICS_COPY_PERMISSIONS.READ)
)

watch(canOpenLogisticsCopySettings, allowed => {
  if (!allowed) logisticsCopySettingsVisible.value = false
})

const userDisplayName = computed(() => {
  return userStore.name || userStore.username || '用户'
})

const permissionSummary = computed(() => {
  const roleNames = userStore.roles
    .map(role => role?.name)
    .filter(Boolean)
  const permissionCount = userStore.permissions.length

  if (userStore.isSuperAdmin) return '超级管理员 · 全部权限'
  if (roleNames.length && permissionCount) {
    return `${roleNames.join('、')} · ${permissionCount} 项权限`
  }
  if (roleNames.length) return roleNames.join('、')
  if (permissionCount) return `已授权 ${permissionCount} 项权限`
  if (userStore.canAccessAdmin) return '后台管理权限'
  return '普通账号'
})

const handleAvatarError = () => {
  avatarLoadFailed.value = true
}

const openLogisticsCopySettings = () => {
  if (!canOpenLogisticsCopySettings.value) return
  closeAccountMenu()
  directoryPanelRef.value?.close()
  messageInboxRef.value?.close()
  notificationInboxRef.value?.close()
  logisticsCopySettingsVisible.value = true
}

const closeLogisticsCopySettings = () => {
  logisticsCopySettingsVisible.value = false
}

const openChat = contact => {
  activeChatContact.value = {
    id: contact?.id || `contact-${Date.now()}`,
    displayName: contact?.displayName || contact?.name || '通讯录好友',
    phone: contact?.phone || '',
    position: contact?.position || '',
    avatarUrl: contact?.avatarUrl || '',
    online: Boolean(contact?.online)
  }
  directoryPanelRef.value?.close()
  messageInboxRef.value?.close()
  closeAccountMenu()
  chatWindowOpen.value = true
}

const openNotification = notification => {
  notificationInboxRef.value?.close()
  messageInboxRef.value?.close()
  directoryPanelRef.value?.close()
  closeAccountMenu()
  chatWindowOpen.value = false

  if (notification?.target) {
    router.push(notification.target)
  }
}

const handleDirectoryOpenChange = isOpen => {
  if (isOpen) {
    closeAccountMenu()
    messageInboxRef.value?.close()
    notificationInboxRef.value?.close()
  }
}

const handleMessageInboxOpenChange = isOpen => {
  if (isOpen) {
    closeAccountMenu()
    directoryPanelRef.value?.close()
    notificationInboxRef.value?.close()
  }
}

const handleNotificationInboxOpenChange = isOpen => {
  if (isOpen) {
    closeAccountMenu()
    directoryPanelRef.value?.close()
    messageInboxRef.value?.close()
  }
}

const toggleAccountMenu = () => {
  directoryPanelRef.value?.close()
  messageInboxRef.value?.close()
  notificationInboxRef.value?.close()
  accountMenuOpen.value = !accountMenuOpen.value
}

const closeAccountMenu = () => {
  accountMenuOpen.value = false
}

const handleAccountMenuClickOutside = event => {
  if (!accountMenuRef.value?.contains(event.target)) {
    closeAccountMenu()
  }
}

// 侧边栏折叠状态
const sidebarMediaQuery = '(max-width: 780px)'
const isMobileViewport = ref(
  typeof window !== 'undefined' && window.matchMedia(sidebarMediaQuery).matches
)
const isSidebarCollapsed = ref(isMobileViewport.value)
let sidebarMediaQueryList = null

// 切换侧边栏
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

const closeSidebar = () => {
  isSidebarCollapsed.value = true
}

const syncSidebarWithViewport = event => {
  const isMobile = typeof event?.matches === 'boolean'
    ? event.matches
    : window.matchMedia(sidebarMediaQuery).matches

  isMobileViewport.value = isMobile
  isSidebarCollapsed.value = isMobile
}

// 注册全局方法供子组件调用
onMounted(() => {
  document.addEventListener('pointerdown', handleAccountMenuClickOutside)
  sidebarMediaQueryList = window.matchMedia(sidebarMediaQuery)
  if (typeof sidebarMediaQueryList.addEventListener === 'function') {
    sidebarMediaQueryList.addEventListener('change', syncSidebarWithViewport)
  } else {
    sidebarMediaQueryList.addListener?.(syncSidebarWithViewport)
  }
  syncSidebarWithViewport(sidebarMediaQueryList)

  window.triggerShippedActionModal = (orderId, action) => {
    if (shippedActionModal.value) {
      shippedActionModal.value.open(orderId, action)
    }
  }

})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleAccountMenuClickOutside)
  if (typeof sidebarMediaQueryList?.removeEventListener === 'function') {
    sidebarMediaQueryList.removeEventListener('change', syncSidebarWithViewport)
  } else {
    sidebarMediaQueryList?.removeListener?.(syncSidebarWithViewport)
  }
  removeDocumentDockGuard()
  removeDocumentDockAfterHook()
  clearTimeout(dockFeedbackTimer)
  cancelDocumentDockAnimations()
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
    router.push('/admin/sales/create')
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
  settings: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M10 2h4l.5 2.5 1.8.75 2.1-1.4 2.8 2.8-1.4 2.1.75 1.8L22 10v4l-2.5.5-.75 1.8 1.4 2.1-2.8 2.8-2.1-1.4-1.8.75L14 22h-4l-.5-2.5-1.8-.75-2.1 1.4-2.8-2.8 1.4-2.1-.75-1.8L2 14v-4l2.5-.5.75-1.8-1.4-2.1 2.8-2.8 2.1 1.4 1.8-.75z"/><circle cx="12" cy="12" r="3"/></svg>',
  truck: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>'
}

const allMenuItems = [
  {
    label: '首页',
    icon: icons.home,
    path: '/admin/dashboard',
    permission: ADMIN_ROUTE_PERMISSIONS.DASHBOARD
  },
  {
    label: '采购',
    icon: icons.cart,
    children: [
      {
        label: '采购订单',
        path: '/admin/purchase/orders',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.ORDERS
      },
      {
        label: '供应商管理',
        path: '/admin/purchase/suppliers',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.SUPPLIERS
      },
      {
        label: '采购入库申请',
        path: '/admin/purchase/inbound',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.INBOUND
      },
      {
        label: '采购退货',
        path: '/admin/purchase/returns',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.RETURNS
      },
      {
        label: '采购发票登记',
        path: '/admin/purchase/invoices',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.INVOICES
      }
    ]
  },
  {
    label: '商品',
    icon: icons.package,
    children: [
      {
        label: '商品列表',
        path: '/admin/products',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.LIST
      },
      {
        label: '原材料列表',
        path: '/admin/materials',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.PRODUCTS.MATERIALS
      }
    ]
  },
  {
    label: '库存',
    icon: icons.chart,
    children: [
      {
        label: '成品库存',
        path: '/admin/inventory',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.PRODUCTS
      },
      {
        label: '原材料库存',
        path: '/admin/inventory/materials',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIALS
      },
      {
        label: '原材料出库',
        path: '/admin/inventory/material-outbounds',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.MATERIAL_OUTBOUNDS
      },
      {
        label: '入库记录',
        path: '/admin/stock/in',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.STOCK_IN
      },
      {
        label: '出库记录',
        path: '/admin/stock/out',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.STOCK_OUT
      },
      {
        label: '仓库管理',
        path: '/admin/inventory/warehouse',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.INVENTORY.WAREHOUSE
      }
    ]
  },
  {
    label: '销售',
    icon: icons.truck,
    children: [
      {
        label: '销售订单',
        path: '/admin/sales',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS
      },
      {
        label: '物流列表',
        path: '/admin/sales/logistics',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.LOGISTICS
      },
      {
        label: '退货订单',
        path: '/admin/sales/returns',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.RETURNS
      },
      {
        label: '客户列表',
        path: '/admin/sales/customers',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.CUSTOMERS
      }
    ]
  },
  {
    label: '财务',
    icon: icons.dollar,
    children: [
      {
        label: '供应商应付',
        path: '/admin/finance/payables',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.PAYABLES
      },
      {
        label: '供应商付款',
        path: '/admin/finance/supplier-payments',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.SUPPLIER_PAYMENTS
      },
      {
        label: '供应商退款',
        path: '/admin/finance/supplier-refunds',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.SUPPLIER_REFUNDS
      },
      {
        label: '供应商正式对账',
        path: '/admin/finance/supplier-reconciliations',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.SUPPLIER_RECONCILIATIONS
      },
      {
        label: '员工费用原型',
        path: '/admin/finance/employee-expenses',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.EMPLOYEE_EXPENSES
      },
      {
        label: '应收欠款',
        path: '/admin/finance/receivables',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.RECEIVABLES
      },
      {
        label: '收款历史',
        path: '/admin/finance/payment-history',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.PAYMENT_HISTORY
      },
      {
        label: '银行账户',
        path: '/admin/finance/bank-accounts',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.BANK_ACCOUNTS
      },
      {
        label: '物流/专车对账',
        path: '/admin/finance/logistics-truck',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.LOGISTICS_TRUCK
      },
      {
        label: '快运/快递对账',
        path: '/admin/finance/express-courier',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.FINANCE.EXPRESS_COURIER
      }
    ]
  },
  {
    label: '人事行政',
    icon: icons.users,
    children: [
      {
        label: '员工管理',
        path: '/admin/hr/employees',
        permission: ADMIN_EMPLOYEE_PERMISSIONS.READ
      },
      {
        label: '部门管理',
        path: '/admin/hr/departments',
        permission: ADMIN_DEPARTMENT_PERMISSIONS.READ
      },
      {
        label: '公司资料',
        path: '/admin/hr/company',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.COMPANY
      },
      {
        label: '检测报告',
        path: '/admin/hr/reports',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.HR.REPORTS
      }
    ]
  },
  {
    label: '设置',
    icon: icons.settings,
    children: [
      {
        label: '门店管理',
        path: '/admin/stores',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.STORES
      },
      {
        label: '系统设置',
        path: '/admin/settings',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.SETTINGS
      },
      {
        label: '权限管理',
        path: '/admin/roles',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.ROLES
      },
      {
        label: '打印模板',
        path: '/admin/system/print-template',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.PRINT_TEMPLATE
      },
      {
        label: '操作日志',
        path: '/admin/system/operation-logs',
        permission: ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.OPERATION_LOGS
      }
    ]
  }
]

const menuItems = computed(() =>
  allMenuItems
    .map(item => {
      const children = item.children?.filter(child =>
        !child.permission || userStore.hasPerm(child.permission)
      )
      return {
        ...item,
        ...(item.children ? { children } : {})
      }
    })
    .filter(item =>
      item.children
        ? item.children.length > 0
        : userStore.hasPerm(item.permission)
    )
)

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
const dockedDocuments = computed(() => {
  const documents = []
  const currentFullPath = route.fullPath
  const add = (document) => {
    if (document.path && document.path !== currentFullPath && document.path !== dockDestinationPath.value) documents.push(document)
  }

  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.ORDERS) && orderDraftStore.hasDraft) {
    add({
      type: orderDraftStore.draftMode === 'edit' ? 'edit' : 'sale',
      title: orderDraftStore.draftTitle,
      path: orderDraftStore.draftPath
    })
  }
  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SALES.RETURNS)) {
    const draft = documentDraftStore.drafts['sale-return']
    add({ type: 'sale-return', title: '销售退货单', path: draft?.path })
  }
  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.INBOUND)) {
    const draft = documentDraftStore.drafts.purchase
    add({ type: 'purchase', title: '采购入库单', path: draft?.path })
  }
  const purchaseOrderDraft = documentDraftStore.drafts['purchase-order']
  const warehouseApplicationDraft = purchaseOrderDraft?.path?.startsWith('/admin/purchase/inbound/application/')
  if (userStore.hasPerm(warehouseApplicationDraft
    ? ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.INBOUND
    : ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.ORDERS)) {
    const draft = purchaseOrderDraft
    add({ type: 'purchase-order', title: draft?.action === 'audit' ? '采购申请审核' : '采购申请', path: draft?.path })
  }
  if (userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.PURCHASE.RETURNS)) {
    const draft = documentDraftStore.drafts['purchase-return']
    add({ type: 'purchase-return', title: '采购退货单', path: draft?.path })
  }
  if (dockingDocument.value) {
    const existingIndex = documents.findIndex(document => document.type === dockingDocument.value.type)
    if (existingIndex !== -1) documents.splice(existingIndex, 1)
    documents.push(dockingDocument.value)
  }
  const order = ['sale', 'edit', 'sale-return', 'purchase-order', 'purchase', 'purchase-return']
  return documents.sort((left, right) => order.indexOf(left.type) - order.indexOf(right.type))
})

const currentMenuLabel = computed(() => {
  if (currentPath.value.startsWith('/admin/purchase/orders/')) {
    const action = {
      'admin-purchase-order-create': '新增', 'admin-purchase-order-edit': '修改',
      'admin-purchase-order-audit': '审核', 'admin-purchase-order-view': '查看'
    }[route.name] || '查看'
    return `采购/${action}采购申请`
  }
  if (currentPath.value.startsWith('/admin/purchase/inbound/')) {
    if (route.name === 'admin-purchase-inbound-application-create') return '采购/新增采购申请'
    if (route.name === 'admin-purchase-inbound-application-edit') return '采购/修改采购申请'
    return `采购/${route.name === 'admin-purchase-inbound-create' ? '新增' : route.name === 'admin-purchase-inbound-edit' ? '修改' : '查看'}进货单`
  }
  if (currentPath.value.startsWith('/admin/purchase/returns/')) {
    const action = route.name === 'admin-purchase-return-create' ? '新增' : route.name === 'admin-purchase-return-edit' ? '修改' : '查看'
    return `采购/${action}采购退货单`
  }
  if (currentPath.value.startsWith('/admin/sales/returns/edit/')) {
    return route.query.productType === 'raw-material'
      ? '销售/修改原材料退货单'
      : '销售/修改退货单'
  }
  // 特殊路由处理
  if (currentPath.value === '/admin/sales/create') {
    return '销售/新增订单'
  }
  if (currentPath.value.startsWith('/admin/sales/edit/')) {
    return '销售/修改订单'
  }
  if (currentPath.value === '/admin/sales/returns/create') {
    return route.query.productType === 'raw-material'
      ? '销售/录入原材料退货单'
      : '销售/录入退货单'
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

const getDockDocument = (form, path) => {
  const type = form.dataset.documentType === 'sale'
    ? (form.dataset.documentAction === 'edit' ? 'edit' : 'sale')
    : form.dataset.documentType
  const draftPath = ['sale', 'edit'].includes(type)
    ? orderDraftStore.draftPath
    : documentDraftStore.drafts[type]?.path
  // Explicitly closed/discarded and read-only documents have no dock destination.
  if (draftPath !== path || activeContentRef.value?.ui?.readOnly) return null
  return { type, path, title: form.querySelector('h2')?.textContent || '单据' }
}

removeDocumentDockGuard = router.beforeEach(async (to, from) => {
  const transitionId = ++dockTransitionId
  cancelDocumentDockAnimations()
  releaseDockedForm = null
  dockingDocument.value = null
  dockDestinationPath.value = ''
  receivedDockType.value = ''
  clearTimeout(dockFeedbackTimer)
  const sameDocumentComponent = to.meta.documentForm && to.name === from.name &&
    String(to.params.id || 'new') === String(from.params.id || 'new')
  if (!from.meta.documentForm || sameDocumentComponent || to.fullPath === from.fullPath) return true
  const form = document.querySelector('.business-document-form')
  if (!form) return true
  const dockDocument = getDockDocument(form, from.fullPath)
  if (!dockDocument) return true
  dockingDocument.value = dockDocument
  dockDestinationPath.value = to.fullPath
  await nextTick()
  if (transitionId !== dockTransitionId) return true
  // Reserve and measure the real destination, including the final flex layout.
  const shortcut = document.querySelector(`.document-dock-shortcut[data-dock-type="${dockDocument.type}"]`)
  const release = await animateDocumentDock(form, shortcut?.getBoundingClientRect(), false)
  if (transitionId === dockTransitionId) releaseDockedForm = release
  else release?.()
  return true
})

removeDocumentDockAfterHook = router.afterEach(async (to, from, failure) => {
  if (dockDestinationPath.value && dockDestinationPath.value !== to.fullPath) return
  const release = releaseDockedForm
  releaseDockedForm = null
  if (!failure && release && dockingDocument.value) {
    receivedDockType.value = dockingDocument.value.type
    dockFeedbackTimer = setTimeout(() => { receivedDockType.value = '' }, 1500)
  }
  dockingDocument.value = null
  dockDestinationPath.value = ''
  await nextTick()
  release?.()
})

const navigateTo = (path) => {
  if (isMobileViewport.value) closeSidebar()
  return router.push(path)
}

const documentListPath = (type) => {
  if (type === 'purchase-order') return '/admin/purchase/orders'
  if (type === 'purchase') return '/admin/purchase/inbound'
  if (type === 'purchase-return') return '/admin/purchase/returns'
  if (type === 'sale-return') return '/admin/sales/returns'
  return '/admin/sales'
}

const handleDocumentClose = () => {
  if (['admin-purchase-inbound-application-create', 'admin-purchase-inbound-application-edit'].includes(route.name)) return router.push('/admin/purchase/inbound')
  const type = document.querySelector('.business-document-form')?.dataset.documentType
  return router.push(documentListPath(type))
}

const restoreDockedDocument = async (draft) => {
  if (!draft?.path || draft.path === route.fullPath || dockingDocument.value) return
  const shortcut = document.querySelector(`.document-dock-shortcut[data-dock-type="${draft.type}"]`)
  const sourceRect = shortcut?.getBoundingClientRect()
  cancelDocumentDockAnimations()
  await router.push(draft.path)
  if (route.fullPath !== draft.path) return
  await nextTick()
  const form = document.querySelector('.business-document-form')
  if (!form) return
  if (!sourceRect) return
  const previousVisibility = form.style.visibility
  form.style.visibility = 'hidden'
  try {
    await waitForDocumentReady(form)
    if (!form.isConnected || route.fullPath !== draft.path) return
    await animateDocumentDock(form, sourceRect, true)
  } finally {
    if (form.isConnected) form.style.visibility = previousVisibility
  }
}

const logout = async () => {
  closeAccountMenu()
  await userStore.logout()
  await router.push('/login')
}
</script>

<style scoped>
.admin-container {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
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

/* 移动端侧边栏展开时的遮罩 */
.sidebar-backdrop {
  display: none;
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
  min-width: 0;
  min-height: 0;
  overflow: visible;
}

/* 顶部栏样式 */
.top-header {
  position: relative;
  z-index: 100;
  flex: 0 0 62px;
  height: 62px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.top-header.is-document-docking {
  z-index: 3100;
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
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}

.document-dock-shortcut {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #0f766e;
  background: #f0fdfa;
  border: 1px solid #99f6e4;
  border-radius: 5px;
  cursor: pointer;
  transition: color .18s ease, background .18s ease, border-color .18s ease, transform .18s ease;
}

.document-dock-shortcut:hover {
  color: #115e59;
  background: #ccfbf1;
  border-color: #5eead4;
  transform: translateY(-1px);
}

.document-dock-shortcut:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.document-dock-shortcut.is-docking {
  cursor: default;
}

.document-dock-shortcut.is-docking .document-dock-dot {
  opacity: 0;
  animation: none;
}

.document-dock-shortcut.is-docking::after,
.document-dock-shortcut.is-arriving::after {
  content: '';
  position: absolute;
  inset: -5px;
  border: 2px solid currentColor;
  border-radius: 8px;
  pointer-events: none;
}

.document-dock-shortcut.is-docking::after {
  animation: dockTargetPulse .65s ease-in-out infinite;
}

.document-dock-shortcut.is-arriving {
  animation: dockReceive .46s ease-out both;
}

.document-dock-shortcut.is-arriving::after {
  animation: dockReceiveRing .6s ease-out forwards;
}

.document-dock-feedback {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  z-index: 1;
  padding: 6px 9px;
  border: 1px solid currentColor;
  border-radius: 5px;
  color: inherit;
  background: #fff;
  box-shadow: 0 4px 12px rgba(15, 23, 42, .1);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  pointer-events: none;
}

.document-dock-enter-active,
.document-dock-leave-active,
.document-dock-move {
  transition: opacity .24s ease, transform .3s ease;
}

.document-dock-enter-from,
.document-dock-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(.8);
}

.document-dock-leave-active {
  position: absolute;
}

/* A reserved receiving slot must stay at its measured, full-size coordinates. */
.document-dock-shortcut.is-docking.document-dock-enter-from {
  opacity: 1;
  transform: none;
}

@keyframes dockTargetPulse {
  0%, 100% { opacity: .35; transform: scale(1); }
  50% { opacity: .8; transform: scale(1.1); }
}

@keyframes dockReceive {
  0% { transform: scale(1); }
  28% { transform: translateY(3px) scale(.9); }
  62% { transform: translateY(-2px) scale(1.12); }
  100% { transform: scale(1); }
}

@keyframes dockReceiveRing {
  0% { opacity: .7; transform: scale(1); }
  100% { opacity: 0; transform: scale(1.65); }
}

.document-dock-shortcut.is-sale,
.document-dock-shortcut.is-edit {
  color: #2563eb;
  background: #eff6ff;
  border-color: #bfdbfe;
}

.document-dock-shortcut.is-sale-return {
  color: #c2410c;
  background: #fff7ed;
  border-color: #fed7aa;
}

.document-dock-shortcut.is-purchase,
.document-dock-shortcut.is-purchase-order {
  color: #0f766e;
  background: #f0fdfa;
  border-color: #99f6e4;
}

.document-dock-icon {
  flex-shrink: 0;
}

.document-dock-dot {
  position: absolute;
  top: -3px;
  right: -3px;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border: 2px solid var(--panel-bg);
  border-radius: 50%;
  animation: dockDotPulse 1.8s ease-in-out infinite;
}

@keyframes dockDotPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.25); opacity: .72; }
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

.user-profile {
  position: relative;
  z-index: 20;
}

.user-info {
  display: flex;
  height: 38px;
  align-items: center;
  gap: 10px;
  padding: 0 10px 0 6px;
  color: var(--text);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font: inherit;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.user-info:hover,
.user-profile:focus-within .user-info {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.user-info:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
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

.user-avatar img,
.detail-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
  white-space: nowrap;
}

.user-detail-card {
  position: absolute;
  z-index: 2000;
  top: calc(100% + 10px);
  right: 0;
  width: 320px;
  padding: 18px;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
  box-sizing: border-box;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translateY(-6px);
  transform-origin: top right;
  transition: opacity 0.18s ease, transform 0.18s ease, visibility 0.18s ease;
}

.user-detail-card::before,
.user-detail-card::after {
  position: absolute;
  right: 22px;
  width: 0;
  height: 0;
  content: "";
  pointer-events: none;
}

.user-detail-card::before {
  top: -8px;
  border-right: 8px solid transparent;
  border-bottom: 8px solid #dfe5ec;
  border-left: 8px solid transparent;
}

.user-detail-card::after {
  top: -7px;
  right: 23px;
  border-right: 7px solid transparent;
  border-bottom: 7px solid var(--panel-bg);
  border-left: 7px solid transparent;
}

.user-profile:hover .user-detail-card,
.user-profile:focus-within .user-detail-card {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: translateY(0);
}

.detail-avatar {
  display: flex;
  width: 64px;
  height: 64px;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  overflow: hidden;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 50%;
}

.detail-avatar-icon {
  width: 30px;
  height: 30px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.detail-name {
  display: block;
  margin-top: 12px;
  overflow-wrap: anywhere;
  color: var(--text);
  font-size: 16px;
  font-weight: 650;
  line-height: 1.5;
  text-align: center;
}

.detail-contact {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
  margin-top: 14px;
  padding: 14px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.detail-field {
  min-width: 0;
  padding: 0 12px;
}

.detail-field:first-child {
  padding-left: 0;
  border-right: 1px solid var(--border);
}

.detail-field:last-child {
  padding-right: 0;
}

.detail-field span,
.detail-permission span {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
}

.detail-field strong,
.detail-permission strong {
  display: block;
  overflow-wrap: anywhere;
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
}

.detail-permission {
  margin-top: 14px;
}

.detail-permission strong {
  color: var(--accent-dark);
}

.account-menu {
  position: relative;
  z-index: 30;
  flex: 0 0 auto;
}

.account-menu-trigger[aria-expanded="true"] {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.account-menu-icon {
  width: 18px;
  height: 18px;
}

.account-menu-panel {
  position: absolute;
  z-index: 2100;
  top: calc(100% + 8px);
  right: 0;
  width: 150px;
  padding: 6px;
  background: var(--panel-bg);
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
}

.account-menu-item {
  display: flex;
  width: 100%;
  height: 38px;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  text-align: left;
  transition: background 0.18s ease, color 0.18s ease;
}

.account-menu-mobile-action {
  color: var(--text-secondary);
}

.account-menu-mobile-action:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.account-menu-item svg {
  width: 17px;
  height: 17px;
  flex: 0 0 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.account-menu-logout {
  color: #b4232f;
}

.account-menu-logout:hover {
  color: #dc2626;
  background: #fef2f2;
}

.account-menu-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
}

.account-menu-enter-active,
.account-menu-leave-active {
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.account-menu-enter-from,
.account-menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* 主内容区 */
.main-content {
  flex: 1;
  min-height: 0;
  padding: 20px;
  overflow-y: auto;
  background: var(--page-bg);
}

.main-content.purchase-list-content {
  padding: 4px;
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
    width: min(240px, 82vw);
    transform: translateX(0);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
  }

  .admin-container.sidebar-collapsed .sidebar {
    width: min(240px, 82vw);
    transform: translateX(-100%);
    box-shadow: none;
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 900;
    padding: 0;
    border: 0;
    background: rgba(15, 23, 42, 0.34);
    cursor: pointer;
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

  .user-info {
    width: 38px;
    padding: 0;
    justify-content: center;
  }

  .user-detail-card {
    position: fixed;
    top: 64px;
    right: 12px;
    width: min(320px, calc(100vw - 24px));
  }

  .user-detail-card::before,
  .user-detail-card::after {
    display: none;
  }

  .account-menu-panel {
    width: min(220px, calc(100vw - 24px));
  }

  :deep(.mobile-directory-menu .directory-trigger) {
    display: none;
  }

  .main-content {
    padding: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar-backdrop,
  .document-dock-shortcut.is-docking::after,
  .document-dock-shortcut.is-arriving,
  .document-dock-shortcut.is-arriving::after,
  .document-dock-dot {
    animation: none;
  }
  .document-dock-enter-active,
  .document-dock-leave-active,
  .document-dock-move {
    transition: none;
  }
  .document-dock-shortcut.is-arriving::after {
    opacity: 0;
  }
  .user-detail-card,
  .account-menu-enter-active,
  .account-menu-leave-active {
    transition: none;
  }
}
</style>
