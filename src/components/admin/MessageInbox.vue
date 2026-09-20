<template>
  <div
    ref="inboxRef"
    class="message-inbox"
    @keydown.esc="close"
  >
    <button
      :class="['icon-btn', 'message-inbox-trigger', { 'is-notification': isNotificationMode }]"
      type="button"
      :title="triggerTitle"
      :aria-label="triggerTitle"
      :aria-controls="panelId"
      :aria-expanded="inboxOpen"
      @click.stop="toggle"
    >
      <svg class="icon-svg" viewBox="0 0 24 24" aria-hidden="true">
        <template v-if="isNotificationMode">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </template>
        <path v-else d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span v-if="unreadCount > 0" class="badge">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <Transition name="message-inbox">
      <section
        v-if="inboxOpen"
        :id="panelId"
        :class="['message-inbox-panel', { 'is-notification-panel': isNotificationMode }]"
        :aria-label="panelTitle"
      >
        <header class="message-inbox-header">
          <div>
            <strong>{{ panelTitle }}</strong>
            <span>{{ unreadCount }} 条未读</span>
          </div>
          <button
            v-if="unreadCount > 0"
            class="message-inbox-read-all"
            type="button"
            @click="markAllRead"
          >
            全部已读
          </button>
        </header>

        <div class="message-inbox-list">
          <div v-if="!messageItems.length" class="message-inbox-empty">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path v-if="isNotificationMode" d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path v-else d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.8 8.8 0 0 1-3.8-.9L4 19l.9-3.1A7.4 7.4 0 0 1 4.5 12 7.5 7.5 0 0 1 12 4.5a7.5 7.5 0 0 1 8 7Z"/>
              <path v-if="isNotificationMode" d="M13.73 21a2 2 0 0 1-3.46 0"/>
              <path v-else d="M8.5 12h.01M12 12h.01M15.5 12h.01"/>
            </svg>
            <span>{{ isNotificationMode ? '暂无通知消息' : '暂无留言消息' }}</span>
          </div>

          <template v-else-if="isNotificationMode">
            <article
              v-for="item in messageItems"
              :key="item.id"
              :class="['message-inbox-item', 'notification-item', { unread: item.unread }]"
            >
              <div :class="['notification-item-icon', `type-${item.type || 'system'}`]" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path v-if="item.type === 'leave'" d="M6 4h12M6 20h12M8 4v5l4 3 4-3V4M8 20v-5l4-3 4 3v5"/>
                  <path v-else-if="item.type === 'payment'" d="M4 6h16v12H4zM4 10h16M8 15h3"/>
                  <path v-else d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"/>
                </svg>
              </div>

              <div class="message-inbox-main notification-main">
                <div class="message-inbox-title">
                  <strong>{{ item.title }}</strong>
                  <time>{{ item.time }}</time>
                </div>
                <p>{{ item.preview }}</p>
                <span class="notification-type-label">{{ item.typeLabel || '系统通知' }}</span>
              </div>

              <div class="notification-item-actions">
                <span v-if="item.unread" class="message-unread-dot" aria-label="未读"></span>
                <button
                  class="notification-go-button"
                  type="button"
                  @click.stop="openNotification(item)"
                >
                  立即前往
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M5 12h13M13 6l6 6-6 6"/>
                  </svg>
                </button>
              </div>
            </article>
          </template>

          <template v-else>
            <button
              v-for="item in messageItems"
              :key="item.id"
              :class="['message-inbox-item', { unread: item.unread }]"
              type="button"
              @click="openMessage(item)"
            >
              <div class="message-inbox-avatar" aria-hidden="true">
                <span>{{ contactInitials(item.contact) }}</span>
                <img
                  v-if="item.contact?.avatarUrl"
                  :src="item.contact.avatarUrl"
                  alt=""
                  @error="hideBrokenAvatar"
                >
              </div>

              <div class="message-inbox-main">
                <div class="message-inbox-title">
                  <strong>{{ item.contact?.displayName || '通讯录好友' }}</strong>
                  <time>{{ item.time }}</time>
                </div>
                <p>{{ item.preview }}</p>
              </div>

              <span v-if="item.unread" class="message-unread-dot" aria-label="未读"></span>
            </button>
          </template>
        </div>
      </section>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  mode: {
    type: String,
    default: 'messages',
    validator: value => ['messages', 'notifications'].includes(value)
  },
  messages: {
    type: Array,
    default: () => [
      {
        id: 'demo-message-1',
        contact: {
          id: 'demo-contact-1',
          displayName: '柯晓',
          position: '总经理',
          phone: '17534534236',
          online: false,
          avatarUrl: ''
        },
        preview: '下午的客户报价我已经整理好了，稍后发给你。',
        time: '今天 10:32',
        unread: true
      },
      {
        id: 'demo-message-2',
        contact: {
          id: 'demo-contact-2',
          displayName: '林悦',
          position: '财务专员',
          phone: '13800001025',
          online: true,
          avatarUrl: ''
        },
        preview: '上周的收款单已经完成核对。',
        time: '昨天 16:08',
        unread: true
      },
      {
        id: 'demo-message-3',
        contact: {
          id: 'demo-contact-3',
          displayName: '陈默',
          position: '仓库管理员',
          phone: '13800001026',
          online: false,
          avatarUrl: ''
        },
        preview: '原材料入库记录我已经补充备注。',
        time: '周五',
        unread: false
      }
    ]
  },
  notifications: {
    type: Array,
    default: () => [
      {
        id: 'demo-notification-1',
        type: 'audit',
        typeLabel: '单据审核',
        title: '销售订单待审核',
        preview: '销售订单 XS20260920018 等待你审核，请及时处理。',
        time: '今天 11:20',
        unread: true,
        target: {
          name: 'admin-sales',
          params: {},
          query: { documentNo: 'XS20260920018' }
        }
      },
      {
        id: 'demo-notification-2',
        type: 'leave',
        typeLabel: '假期批准',
        title: '请假申请待处理',
        preview: '林悦提交了 9 月 25 日的年假申请。',
        time: '今天 09:45',
        unread: true,
        target: {
          name: 'admin-hr-reports',
          params: {},
          query: { tab: 'leave', applicationId: 'QJ20260925001' }
        }
      },
      {
        id: 'demo-notification-3',
        type: 'payment',
        typeLabel: '收款审核',
        title: '收款单审核完成',
        preview: '收款单 SK20260919006 已完成审核入账。',
        time: '昨天 16:08',
        unread: false,
        target: {
          name: 'admin-finance-payment-history',
          params: {},
          query: { documentNo: 'SK20260919006' }
        }
      }
    ]
  }
})

const emit = defineEmits(['open-chat', 'open-change', 'open-notification'])

const inboxRef = ref(null)
const inboxOpen = ref(false)
const readMessageIds = ref([])

const isNotificationMode = computed(() => props.mode === 'notifications')
const panelId = computed(() => {
  return isNotificationMode.value ? 'notification-inbox-panel' : 'message-inbox-panel'
})
const triggerTitle = computed(() => {
  return isNotificationMode.value ? '打开审核通知' : '打开留言消息'
})
const panelTitle = computed(() => {
  return isNotificationMode.value ? '审核通知' : '留言消息'
})

const sourceItems = computed(() => {
  return isNotificationMode.value ? props.notifications : props.messages
})

const messageItems = computed(() => {
  return sourceItems.value.map(item => ({
    ...item,
    unread: Boolean(item.unread) && !readMessageIds.value.includes(item.id)
  }))
})

const unreadCount = computed(() => {
  return messageItems.value.filter(item => item.unread).length
})

const contactInitials = contact => {
  const name = String(contact?.displayName || contact?.name || '').trim()
  return name ? name.slice(-2) : '好友'
}

const hideBrokenAvatar = event => {
  event.currentTarget.style.display = 'none'
}

const close = () => {
  if (!inboxOpen.value) return
  inboxOpen.value = false
  emit('open-change', false)
}

const toggle = () => {
  inboxOpen.value = !inboxOpen.value
  emit('open-change', inboxOpen.value)
}

const openMessage = item => {
  if (item.unread && !readMessageIds.value.includes(item.id)) {
    readMessageIds.value = [...readMessageIds.value, item.id]
  }
  close()
  emit('open-chat', item.contact)
}

const openNotification = item => {
  if (item.unread && !readMessageIds.value.includes(item.id)) {
    readMessageIds.value = [...readMessageIds.value, item.id]
  }
  close()
  emit('open-notification', item)
}

const markAllRead = () => {
  readMessageIds.value = sourceItems.value
    .filter(item => item.unread)
    .map(item => item.id)
}

const handleClickOutside = event => {
  if (!inboxRef.value?.contains(event.target)) {
    close()
  }
}

defineExpose({
  close
})

onMounted(() => {
  document.addEventListener('pointerdown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleClickOutside)
})
</script>

<style scoped>
.message-inbox {
  position: relative;
  z-index: 40;
  flex: 0 0 auto;
}

.icon-btn {
  position: relative;
  display: flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.icon-btn:hover,
.message-inbox-trigger[aria-expanded="true"] {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.icon-btn:focus-visible,
.message-inbox-read-all:focus-visible,
.message-inbox-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.icon-svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  display: flex;
  min-width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
  padding: 2px 5px;
  color: #ffffff;
  background: #ef4444;
  border-radius: 999px;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.3);
  box-sizing: border-box;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.message-inbox-panel {
  position: absolute;
  z-index: 2200;
  top: calc(100% + 8px);
  right: 0;
  width: 350px;
  max-width: calc(100vw - 24px);
  overflow: hidden;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.16);
}

.message-inbox-panel.is-notification-panel {
  width: 430px;
}

.message-inbox-header {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 14px;
  border-bottom: 1px solid var(--border);
}

.message-inbox-header > div {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.message-inbox-header strong {
  font-size: 14px;
  font-weight: 700;
}

.message-inbox-header span {
  color: var(--text-muted);
  font-size: 11px;
}

.message-inbox-read-all {
  padding: 4px 6px;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}

.message-inbox-read-all:hover {
  background: var(--accent-soft);
}

.message-inbox-list {
  max-height: min(370px, calc(100vh - 160px));
  overflow-y: auto;
  scrollbar-color: var(--border-strong) transparent;
  scrollbar-width: thin;
}

.message-inbox-list::-webkit-scrollbar {
  width: 7px;
}

.message-inbox-list::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 999px;
}

.message-inbox-item {
  display: grid;
  width: 100%;
  min-height: 70px;
  grid-template-columns: 38px minmax(0, 1fr) 8px;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  color: var(--text);
  background: var(--panel-bg);
  border: 0;
  border-bottom: 1px solid #edf1f5;
  cursor: pointer;
  text-align: left;
  transition: background 0.18s ease;
}

.message-inbox-item:last-child {
  border-bottom: 0;
}

.message-inbox-item:hover,
.message-inbox-item.unread {
  background: #f8fcfa;
}

.notification-item {
  grid-template-columns: 34px minmax(0, 1fr) auto;
  cursor: default;
}

.notification-item-icon {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 5px;
}

.notification-item-icon.type-leave {
  color: #a4510b;
  background: #fff3df;
  border-color: #f5d39e;
}

.notification-item-icon.type-payment {
  color: #16647a;
  background: #e7f5f8;
  border-color: #b9dfe8;
}

.notification-item-icon svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.notification-main {
  align-self: center;
}

.notification-type-label {
  display: inline-block;
  margin-top: 5px;
  padding: 2px 6px;
  color: var(--text-secondary);
  background: #f1f5f9;
  border-radius: 999px;
  font-size: 10px;
  line-height: 1.3;
}

.notification-item-actions {
  display: flex;
  min-width: 74px;
  align-items: flex-end;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
}

.notification-go-button {
  display: inline-flex;
  height: 28px;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 8px;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 5px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.notification-go-button:hover {
  color: #ffffff;
  background: var(--accent);
  border-color: var(--accent);
}

.notification-go-button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.notification-go-button svg {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.message-inbox-avatar {
  position: relative;
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  overflow: hidden;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
}

.message-inbox-avatar img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-inbox-main {
  min-width: 0;
}

.message-inbox-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.message-inbox-title strong {
  overflow: hidden;
  font-size: 13px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-inbox-title time {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 10px;
}

.message-inbox-main p {
  overflow: hidden;
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-unread-dot {
  width: 7px;
  height: 7px;
  background: #ef4444;
  border-radius: 50%;
}

.message-inbox-empty {
  display: flex;
  min-height: 150px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.message-inbox-empty svg {
  width: 26px;
  height: 26px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.message-inbox-enter-active,
.message-inbox-leave-active {
  transform-origin: top right;
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.message-inbox-enter-from,
.message-inbox-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 780px) {
  .message-inbox-panel {
    position: fixed;
    top: 64px;
    right: 12px;
    width: calc(100vw - 24px);
  }

  .message-inbox-panel.is-notification-panel {
    width: calc(100vw - 24px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .message-inbox-enter-active,
  .message-inbox-leave-active,
  .icon-btn,
  .message-inbox-item,
  .notification-go-button {
    transition: none;
  }
}
</style>
