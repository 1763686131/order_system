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
          <div v-if="loading && !messageItems.length" class="message-inbox-empty">
            <span>正在加载...</span>
          </div>

          <div v-else-if="loadError && !messageItems.length" class="message-inbox-empty">
            <span>{{ loadError }}</span>
            <button type="button" class="message-inbox-read-all" @click="loadItems">重新加载</button>
          </div>

          <div v-else-if="!messageItems.length" class="message-inbox-empty">
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
import request from '@/api/request'

const props = defineProps({
  mode: {
    type: String,
    default: 'messages',
    validator: value => ['messages', 'notifications'].includes(value)
  }
})

const emit = defineEmits(['open-chat', 'open-change', 'open-notification'])

const inboxRef = ref(null)
const inboxOpen = ref(false)
const sourceItems = ref([])
const loading = ref(false)
const loadError = ref('')
const remoteUnreadCount = ref(0)
let refreshTimer = null

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

const messageItems = computed(() => {
  return sourceItems.value
})

const unreadCount = computed(() => {
  return remoteUnreadCount.value
})

const contactInitials = contact => {
  const name = String(contact?.displayName || contact?.name || '').trim()
  return name ? name.slice(-2) : '好友'
}

const hideBrokenAvatar = event => {
  event.currentTarget.style.display = 'none'
}

const formatTime = value => {
  if (!value) return ''
  const normalized = String(value).replace(' ', 'T')
  const date = new Date(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(normalized)
    ? `${normalized}Z`
    : normalized)
  if (Number.isNaN(date.getTime())) return value
  const now = new Date()
  const sameDay = date.toDateString() === now.toDateString()
  if (sameDay) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
  }
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const loadItems = async ({ silent = false } = {}) => {
  if (!silent) loading.value = true
  loadError.value = ''
  try {
    if (isNotificationMode.value) {
      const [response, countResponse] = await Promise.all([
        request.get('/admin/notifications', { params: { limit: 50 } }),
        request.get('/admin/notifications/unread-count')
      ])
      sourceItems.value = (response?.notifications || []).map(item => ({
        ...item,
        time: formatTime(item.createdAt)
      }))
      remoteUnreadCount.value = Number(countResponse?.unreadCount || 0)
    } else {
      const [response, countResponse] = await Promise.all([
        request.get('/admin/messages/conversations', { params: { limit: 50 } }),
        request.get('/admin/messages/unread-count')
      ])
      sourceItems.value = (response?.conversations || []).map(item => ({
        ...item,
        contact: { ...item.contact, conversationId: item.id },
        time: formatTime(item.lastMessageAt),
        unread: Number(item.unreadCount || 0) > 0
      }))
      remoteUnreadCount.value = Number(countResponse?.unreadCount || 0)
    }
  } catch (error) {
    loadError.value = error?.response?.data?.message || '消息加载失败'
  } finally {
    loading.value = false
  }
}

const close = () => {
  if (!inboxOpen.value) return
  inboxOpen.value = false
  emit('open-change', false)
}

const toggle = () => {
  inboxOpen.value = !inboxOpen.value
  emit('open-change', inboxOpen.value)
  if (inboxOpen.value) loadItems()
}

const openMessage = async item => {
  if (item.unread) {
    await request.post(`/admin/messages/conversations/${item.id}/read`).catch(() => {})
  }
  close()
  emit('open-chat', item.contact)
  loadItems({ silent: true })
}

const openNotification = async item => {
  if (item.unread) {
    await request.post(`/admin/notifications/${item.id}/read`).catch(() => {})
  }
  close()
  emit('open-notification', item)
  loadItems({ silent: true })
}

const markAllRead = async () => {
  if (isNotificationMode.value) {
    await request.post('/admin/notifications/read-all')
  } else {
    await request.post('/admin/messages/read-all')
  }
  await loadItems({ silent: true })
}

const handleClickOutside = event => {
  if (!inboxRef.value?.contains(event.target)) {
    close()
  }
}

defineExpose({
  close,
  refresh: loadItems
})

onMounted(() => {
  document.addEventListener('pointerdown', handleClickOutside)
  loadItems()
  refreshTimer = window.setInterval(() => loadItems({ silent: true }), 20000)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleClickOutside)
  if (refreshTimer) window.clearInterval(refreshTimer)
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
