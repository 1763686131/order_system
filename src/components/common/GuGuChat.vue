<template>
  <Teleport to="body">
  <div v-if="modelValue" class="nomi-admin-layer" @click.self="close" @keydown="handleKeydown">
    <section
      ref="dialogRef"
      :class="['nomi-admin-dialog', { 'is-resizing': resizing }]"
      :style="dialogStyle"
      role="dialog"
      aria-modal="true"
      aria-labelledby="nomi-admin-title"
      tabindex="-1"
    >
      <header
        :class="['nomi-admin-header', { 'is-dragging': dragging }]"
        @pointerdown="startDrag"
        @pointermove="dragDialog"
        @pointerup="stopDrag"
        @pointercancel="stopDrag"
        @lostpointercapture="stopDrag"
      >
        <div class="nomi-admin-title-wrap">
          <div class="nomi-admin-avatar" aria-hidden="true">
            <GuGuAvatar :thinking="sending || orderDraftBusy" />
          </div>
          <div>
            <h2 id="nomi-admin-title">固固助手（GuGu）</h2>
          </div>
        </div>

        <div class="nomi-admin-header-actions">
          <button
            v-if="canCreateOrder"
            class="nomi-icon-button"
            type="button"
            :title="orderDraftOpen ? '切换到日常聊天' : '整理新增订单'"
            :aria-label="orderDraftOpen ? '切换到日常聊天' : '整理新增订单'"
            :aria-pressed="orderDraftOpen"
            :disabled="sending || orderDraftBusy || !apiConfigured || statusLoading || Boolean(statusError)"
            @click="toggleOrderDraft"
          >
            <MessageSquareText v-if="orderDraftOpen" :size="18" :stroke-width="1.8" />
            <FilePlus2 v-else :size="18" :stroke-width="1.8" />
          </button>
          <button
            class="nomi-icon-button"
            type="button"
            title="保存/查看历史聊天"
            aria-label="保存/查看历史聊天"
            :aria-pressed="historyOpen"
            :disabled="sending || orderDraftBusy"
            @click="toggleHistory"
          >
            <History :size="18" :stroke-width="1.8" />
          </button>
          <button
            class="nomi-icon-button"
            type="button"
            title="清空对话"
            aria-label="清空对话"
            :disabled="historyOpen || sending || orderDraftBusy || (!messages.length && !failedQuestion && !orderDraftOpen)"
            @click="clearConversation"
          >
            <Trash2 :size="17" :stroke-width="1.8" />
          </button>
          <button
            class="nomi-icon-button"
            type="button"
            title="关闭固固助手"
            aria-label="关闭固固助手"
            @click="close"
          >
            <X :size="18" :stroke-width="1.8" />
          </button>
        </div>
      </header>

      <section v-if="historyOpen" class="nomi-admin-history-panel" aria-label="历史聊天">
        <div class="nomi-admin-history-heading">
          <div>
            <strong>历史聊天</strong>
          </div>
          <button
            class="nomi-history-close"
            type="button"
            title="返回当前聊天"
            aria-label="返回当前聊天"
            @click="historyOpen = false"
          >
            <X :size="17" :stroke-width="1.8" />
          </button>
        </div>
        <p v-if="historyNotice" class="nomi-history-notice" role="status">{{ historyNotice }}</p>
        <div v-if="historyError" class="nomi-history-error" role="alert">
          {{ historyError }}
          <button type="button" class="nomi-link-button" @click="loadChatHistories">重试</button>
        </div>
        <div v-else-if="historyLoading" class="nomi-history-empty" role="status">
          <LoaderCircle class="nomi-history-spinner" :size="24" :stroke-width="1.8" />
          <span>正在读取服务器历史...</span>
        </div>
        <div v-else-if="!chatHistories.length" class="nomi-history-empty">
          <History :size="26" :stroke-width="1.5" />
          <span>还没有保存的聊天记录</span>
        </div>
        <div v-else class="nomi-history-list">
          <article
            v-for="history in chatHistories"
            :key="history.id"
            :class="['nomi-history-item', { 'is-active': history.id === activeHistoryId }]"
          >
            <button
              class="nomi-history-open"
              type="button"
              :title="`打开：${history.title}`"
              :disabled="historyRestoring"
              @click="restoreConversation(history)"
            >
              <MessageSquareText :size="16" :stroke-width="1.8" />
              <span class="nomi-history-copy">
                <strong>{{ history.title }}</strong>
                <small>{{ formatHistoryTime(history.updatedAt) }} · {{ history.messageCount }} 条消息</small>
              </span>
            </button>
            <button
              class="nomi-history-delete"
              type="button"
              title="删除历史聊天"
              aria-label="删除历史聊天"
              :disabled="historyRestoring || historySaving"
              @click="deleteHistory(history.id)"
            >
              <Trash2 :size="15" :stroke-width="1.8" />
            </button>
          </article>
        </div>
      </section>

      <div v-else ref="messageListRef" class="nomi-admin-messages" role="log" aria-label="固固助手对话记录" aria-live="polite" :aria-busy="sending || orderDraftBusy">
        <div v-if="statusLoading" class="nomi-admin-state">
          正在检查固固助手配置...
        </div>

        <div v-else-if="statusError" class="nomi-admin-state nomi-admin-state-error">
          {{ statusError }}
          <button type="button" class="nomi-link-button" @click="loadStatus">
            重试
          </button>
        </div>

        <template v-else-if="!apiConfigured">
          <div class="nomi-admin-empty">
            <div class="nomi-empty-icon" aria-hidden="true">
              <KeyRound :size="22" :stroke-width="1.8" />
            </div>
            <strong>{{ configurationError ? 'API 配置需要更新' : '尚未配置 API 接口' }}</strong>
            <p>{{ configurationError || (canConfigure ? '先配置 AI 服务商和 API 密钥，即可开始聊天。' : '请联系有系统设置权限的管理员配置 AI 接口。') }}</p>
            <button v-if="canConfigure" type="button" class="nomi-primary-button" @click="emit('open-settings')">
              <Settings2 :size="16" :stroke-width="1.8" />
              去设置 API
            </button>
          </div>
        </template>

        <template v-else>
          <div v-if="!messages.length && !orderDraftOpen && !failedQuestion" class="nomi-admin-empty">
            <div class="nomi-welcome-avatar"><GuGuAvatar /></div>
            <strong>你好，我是固固助手（GuGu）</strong>
            <p>今天有什么想聊的？</p>
          </div>
          <div
            v-for="(message, index) in messages"
            :key="`${message.role}-${index}`"
            :class="['nomi-message-row', `is-${message.role}`]"
          >
            <GuGuOrderDraft
              v-if="message.orderFlow && message.role === 'assistant'"
              :message="message"
              :active="orderDraftOpen && canCreateOrder && message.id === orderQuestionId"
              :busy="orderDraftBusy"
              @answer="orderFlow.answerOption(message, $event)"
              @confirm="orderFlow.confirmSummary(message)"
            />
            <div v-else class="nomi-message-bubble">
              <div
                v-if="message.role === 'assistant'"
                class="nomi-message-content nomi-markdown"
                v-html="renderMarkdown(message.content)"
              ></div>
              <span v-else class="nomi-message-content">{{ message.content }}</span>
              <small v-if="message.orderQueryUsed" class="nomi-order-source">已查询订单数据</small>
              <small v-if="message.truncated" class="nomi-truncated">回复未完，可继续提问。</small>
            </div>
          </div>

          <div v-if="failedQuestion" class="nomi-message-row is-user">
            <div class="nomi-message-bubble">{{ failedQuestion }}</div>
          </div>
          <div v-if="sending || orderDraftBusy" class="nomi-message-row is-assistant">
            <div class="nomi-message-bubble nomi-loading-bubble" aria-label="固固助手正在思考">
              <span></span><span></span><span></span>
            </div>
          </div>
        </template>
      </div>

      <div v-if="sendError && apiConfigured && !orderDraftOpen && !historyOpen" class="nomi-send-error" role="alert">
        <span>{{ sendError }}</span>
        <button v-if="failedQuestion && !sending" type="button" class="nomi-link-button" @click="sendMessage(failedQuestion)">
          重试
        </button>
      </div>
      <form
        v-if="apiConfigured && !statusLoading && !statusError && !historyOpen"
        class="nomi-admin-composer"
        @submit.prevent="handleComposerSubmit"
      >
        <textarea
          ref="composerRef"
          v-model="draft"
          :disabled="sending || orderDraftBusy"
          rows="2"
          maxlength="4000"
          :placeholder="orderDraftOpen ? '输入订单内容，或回复固固的问题...' : '输入任务或问题...'"
          :aria-label="orderDraftOpen ? '输入订单内容或回复' : '输入任务或问题'"
          @compositionstart="composing = true"
          @compositionend="composing = false"
          @keydown="handleComposerKeydown"
        ></textarea>
        <button
          v-if="sending || orderDraftBusy"
          class="nomi-send-button"
          type="button"
          title="停止等待"
          aria-label="停止等待"
          :disabled="orderDraftOpening"
          @click="stopWaiting"
        >
          <Square :size="15" :stroke-width="1.9" />
        </button>
        <button
          v-else
          class="nomi-send-button"
          type="submit"
          :disabled="sending || orderDraftBusy || !draft.trim()"
          title="发送消息"
          aria-label="发送消息"
        >
          <Send :size="17" :stroke-width="1.9" />
        </button>
      </form>

      <div
        v-for="handle in resizeHandles"
        :key="handle"
        :class="['nomi-resize-handle', `is-${handle}`]"
        aria-hidden="true"
        @pointerdown="startResize($event, handle)"
        @pointermove="resizeDialog"
        @pointerup="stopResize"
        @pointercancel="stopResize"
        @lostpointercapture="stopResize"
      ></div>
    </section>
  </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { FilePlus2, History, KeyRound, LoaderCircle, MessageSquareText, Send, Settings2, Square, Trash2, X } from '@lucide/vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import request from '@/api/request'
import GuGuAvatar from './GuGuAvatar.vue'
import GuGuOrderDraft from './GuGuOrderDraft.vue'
import { useUserStore } from '@/stores/user'
import { ADMIN_ROUTE_BRANCH_PERMISSIONS } from '@/utils/adminAccess'
import { ADMIN_SALES_ORDER_PERMISSIONS } from '@/utils/accessControl'
import { looksLikeGuGuOrderRequest, useGuGuOrderConversation } from '@/composables/useGuGuOrderConversation'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  openOrder: {
    type: Function,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'open-settings'])
const userStore = useUserStore()
const canConfigure = computed(() =>
  userStore.hasPerm(ADMIN_ROUTE_BRANCH_PERMISSIONS.SYSTEM.SETTINGS)
)
const canCreateOrder = computed(() => userStore.hasPerm(ADMIN_SALES_ORDER_PERMISSIONS.CREATE))
const handleDraftConfigurationError = message => {
  apiConfigured.value = false
  configurationError.value = message
}

const toggleOrderDraft = () => {
  if (!canCreateOrder.value || sending.value || orderDraftBusy.value) return
  if (orderDraftOpen.value) orderFlow.reset()
  else orderFlow.start()
  if (orderDraftOpen.value) {
    failedQuestion.value = ''
    sendError.value = ''
  }
  nextTick(() => composerRef.value?.focus())
}

const close = () => {
  stopDrag()
  stopResize()
  emit('update:modelValue', false)
}

const dialogRef = ref(null)
const dialogPosition = ref(null)
const dialogSize = ref(null)
const dragging = ref(false)
const resizing = ref(false)
const resizeHandles = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
const dialogStyle = computed(() => ({
  ...(dialogPosition.value
    ? {
        position: 'fixed',
        left: `${dialogPosition.value.left}px`,
        top: `${dialogPosition.value.top}px`
      }
    : {}),
  ...(dialogSize.value
    ? {
        width: `${dialogSize.value.width}px`,
        height: `${dialogSize.value.height}px`
      }
    : {})
}))
const composerRef = ref(null)
const messageListRef = ref(null)
const messages = ref([])
const draft = ref('')
const sending = ref(false)
const composing = ref(false)
const sendError = ref('')
const failedQuestion = ref('')
const statusLoading = ref(true)
const statusError = ref('')
const apiConfigured = ref(false)
const configurationError = ref('')
const historyOpen = ref(false)
const chatHistories = ref([])
const activeHistoryId = ref('')
const historyNotice = ref('')
const historyError = ref('')
const historyLoading = ref(false)
const historySaving = ref(false)
const historyRestoring = ref(false)
let historyNoticeTimer
let historySaveTimer
let restoringHistory = false
let historySaveQueue = Promise.resolve()
let pendingHistoryId = ''
let historyGeneration = 0
const orderFlow = useGuGuOrderConversation({
  messages,
  request,
  openOrder: summary => props.openOrder(summary),
  onConfigurationError: handleDraftConfigurationError
})
const {
  active: orderDraftOpen,
  busy: orderDraftBusy,
  opening: orderDraftOpening,
  activeQuestionId: orderQuestionId
} = orderFlow
let replyController
let statusController
let previousFocus
let dragState
let resizeState

const DIALOG_BOUNDS_STORAGE_KEY = 'admin_gugu_chat_window_bounds'
const CHAT_HISTORY_STORAGE_KEY = 'admin_gugu_chat_histories'
const MAX_CHAT_HISTORIES = 30
const MAX_CHAT_HISTORY_MESSAGES = 200
const MAX_CHAT_HISTORY_BYTES = 450 * 1024

const cloneMessages = source => {
  try {
    return JSON.parse(JSON.stringify(source))
  } catch {
    return []
  }
}

const newHistoryId = () => {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID().replaceAll('-', '')
  return `gugu-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`
}

const historyPayload = (title, source) => {
  const messages = source.slice(-MAX_CHAT_HISTORY_MESSAGES)
  const payload = { title, messages }
  if (new TextEncoder().encode(JSON.stringify(payload)).length > MAX_CHAT_HISTORY_BYTES) return null
  return payload
}

const loadLegacyHistories = () => {
  try {
    const stored = JSON.parse(window.localStorage.getItem(CHAT_HISTORY_STORAGE_KEY) || '[]')
    return Array.isArray(stored)
      ? stored.filter(item => item?.id && item?.title && Array.isArray(item.messages)).slice(0, MAX_CHAT_HISTORIES)
      : []
  } catch {
    return []
  }
}

const showHistoryNotice = message => {
  historyNotice.value = message
  clearTimeout(historyNoticeTimer)
  historyNoticeTimer = setTimeout(() => {
    historyNotice.value = ''
  }, 2600)
}

const historyTitle = source => {
  const firstUserMessage = source.find(message => message.role === 'user' && message.content)
  const firstMessage = firstUserMessage || source.find(message => message.content)
  const title = String(firstMessage?.content || '未命名聊天').replace(/\s+/g, ' ').trim()
  return title.length > 32 ? `${Array.from(title).slice(0, 32).join('')}...` : title
}

const formatHistoryTime = value => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '时间未知'
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const migrateLegacyHistories = async () => {
  const legacy = loadLegacyHistories()
  if (!legacy.length) return
  const remaining = []
  for (const history of [...legacy].reverse()) {
    const payload = historyPayload(history.title, cloneMessages(history.messages))
    if (!payload) {
      remaining.push(history)
      continue
    }
    try {
      const response = await request.put(`/ai/histories/${encodeURIComponent(history.id)}`, payload)
      if (!response.success) throw new Error(response.message || '迁移本地历史聊天失败')
    } catch {
      remaining.push(history)
    }
  }
  if (remaining.length) {
    window.localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(remaining))
    showHistoryNotice(`${remaining.length} 条旧聊天暂未迁移，仍保留在本机。`)
  } else {
    window.localStorage.removeItem(CHAT_HISTORY_STORAGE_KEY)
  }
}

const saveConversation = async (snapshot, { quiet = false } = {}) => {
  if (!snapshot.length) return null
  const payload = historyPayload(historyTitle(snapshot), snapshot)
  if (!payload) {
    if (!quiet) historyError.value = '当前聊天内容过长，无法保存。'
    else showHistoryNotice('当前聊天过长，无法自动保存。')
    return null
  }
  const generation = historyGeneration
  const id = activeHistoryId.value || (pendingHistoryId ||= newHistoryId())
  historySaveQueue = historySaveQueue.catch(() => {}).then(async () => {
    const response = await request.put(`/ai/histories/${encodeURIComponent(id)}`, payload)
    if (!response.success) throw new Error(response.message || '保存历史聊天失败')
    if (historyGeneration === generation && messages.value.length) {
      activeHistoryId.value = id
      pendingHistoryId = ''
    }
    const current = chatHistories.value.find(history => history.id === id)
    const saved = {
      id,
      title: response.data?.title || payload.title,
      messageCount: response.data?.messageCount || snapshot.length,
      createdAt: current?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    chatHistories.value = [saved, ...chatHistories.value.filter(history => history.id !== id)]
      .slice(0, MAX_CHAT_HISTORIES)
    historyError.value = ''
    return saved
  })
  try {
    if (!quiet) historySaving.value = true
    const saved = await historySaveQueue
    if (!quiet) showHistoryNotice('当前对话已保存到服务器。')
    return saved
  } catch (error) {
    if (quiet) showHistoryNotice('历史聊天自动保存失败，请检查网络连接后重试。')
    else historyError.value = error.response?.data?.message || error.message || '保存历史聊天失败'
    return null
  } finally {
    if (!quiet) historySaving.value = false
  }
}

const saveCurrentConversation = async () => {
  if (!messages.value.length) {
    showHistoryNotice('当前还没有可保存的聊天内容。')
    return null
  }
  clearTimeout(historySaveTimer)
  return saveConversation(cloneMessages(messages.value))
}

const loadChatHistories = async () => {
  historyLoading.value = true
  historyError.value = ''
  try {
    await migrateLegacyHistories()
    const response = await request.get('/ai/histories')
    if (!response.success || !Array.isArray(response.items)) {
      throw new Error(response.message || '读取服务器历史聊天失败')
    }
    chatHistories.value = response.items
  } catch (error) {
    historyError.value = error.response?.data?.message || error.message || '读取服务器历史聊天失败'
  } finally {
    historyLoading.value = false
  }
}

const toggleHistory = async () => {
  if (sending.value || orderDraftBusy.value) return
  if (historyOpen.value) {
    historyOpen.value = false
    nextTick(() => composerRef.value?.focus())
    return
  }
  historyOpen.value = true
  historyError.value = ''
  historyLoading.value = true
  clearTimeout(historySaveTimer)
  try {
    await migrateLegacyHistories()
    if (messages.value.length) {
      const saved = await saveCurrentConversation()
      if (!saved) throw new Error(historyError.value || '当前聊天未能保存到服务器')
    }
    const response = await request.get('/ai/histories')
    if (!response.success || !Array.isArray(response.items)) {
      throw new Error(response.message || '读取服务器历史聊天失败')
    }
    chatHistories.value = response.items
  } catch (error) {
    historyError.value = error.response?.data?.message || error.message || '读取服务器历史聊天失败'
  } finally {
    historyLoading.value = false
  }
  nextTick(() => dialogRef.value?.focus())
}

const restoreConversation = async history => {
  if (sending.value || orderDraftBusy.value || historyRestoring.value) return
  historyRestoring.value = true
  historyError.value = ''
  clearTimeout(historySaveTimer)
  try {
    await historySaveQueue.catch(() => {})
    const response = await request.get(`/ai/histories/${encodeURIComponent(history.id)}`)
    if (!response.success || !Array.isArray(response.data?.messages)) {
      throw new Error(response.message || '读取历史聊天失败')
    }
    historyGeneration += 1
    pendingHistoryId = ''
    orderFlow.reset()
    restoringHistory = true
    messages.value = cloneMessages(response.data.messages).map((message, index) => ({
      ...message,
      id: `history-${history.id}-${index}`
    }))
    activeHistoryId.value = history.id
    failedQuestion.value = ''
    sendError.value = ''
    draft.value = ''
    historyOpen.value = false
    await nextTick()
    restoringHistory = false
    await scrollToBottom()
    composerRef.value?.focus()
  } catch (error) {
    historyError.value = error.response?.data?.message || error.message || '读取历史聊天失败'
  } finally {
    restoringHistory = false
    historyRestoring.value = false
  }
}

const deleteHistory = async id => {
  clearTimeout(historySaveTimer)
  const deletingActiveHistory = activeHistoryId.value === id
  if (deletingActiveHistory) {
    historyGeneration += 1
    activeHistoryId.value = ''
    pendingHistoryId = ''
  }
  try {
    historySaveQueue = historySaveQueue.catch(() => {}).then(() =>
      request.delete(`/ai/histories/${encodeURIComponent(id)}`)
    )
    const response = await historySaveQueue
    if (!response.success) throw new Error(response.message || '删除历史聊天失败')
    chatHistories.value = chatHistories.value.filter(item => item.id !== id)
    if (activeHistoryId.value === id) activeHistoryId.value = ''
    showHistoryNotice('服务器历史聊天已删除。')
  } catch (error) {
    historyError.value = error.response?.data?.message || error.message || '删除历史聊天失败'
  }
}

const queueHistorySave = () => {
  if (restoringHistory || !messages.value.length) return
  clearTimeout(historySaveTimer)
  historySaveTimer = setTimeout(() => {
    saveConversation(cloneMessages(messages.value), { quiet: true })
  }, 350)
}

watch(messages, queueHistorySave, { deep: true, flush: 'post' })

const loadStoredDialogBounds = () => {
  try {
    const bounds = JSON.parse(window.localStorage.getItem(DIALOG_BOUNDS_STORAGE_KEY) || 'null')
    if (
      ![bounds?.left, bounds?.top, bounds?.width, bounds?.height].every(Number.isFinite)
      || bounds.width <= 0
      || bounds.height <= 0
    ) return null
    return { left: bounds.left, top: bounds.top, width: bounds.width, height: bounds.height }
  } catch {
    return null
  }
}

let savedDialogBounds = loadStoredDialogBounds()

const restoreDialogBounds = () => {
  if (!savedDialogBounds || document.documentElement.clientWidth <= 780) return
  const { left, top, width, height } = savedDialogBounds
  dialogPosition.value = { left, top }
  dialogSize.value = { width, height }
}

const saveDialogBounds = () => {
  if (!dialogRef.value || document.documentElement.clientWidth <= 780) return
  const { left, top, width, height } = dialogRef.value.getBoundingClientRect()
  savedDialogBounds = {
    left: dialogPosition.value?.left ?? left,
    top: dialogPosition.value?.top ?? top,
    width: dialogSize.value?.width ?? width,
    height: dialogSize.value?.height ?? height
  }
  try {
    window.localStorage.setItem(DIALOG_BOUNDS_STORAGE_KEY, JSON.stringify(savedDialogBounds))
  } catch {
    // 浏览器禁用本地存储时，仍在当前页面内保留窗口设置。
  }
}

const getResizeLimits = () => {
  const viewportWidth = document.documentElement.clientWidth
  const viewportHeight = document.documentElement.clientHeight
  const availableWidth = Math.max(0, viewportWidth - 28)
  const availableHeight = Math.max(0, viewportHeight - 96)
  const minWidth = Math.min(340, availableWidth)
  const minHeight = Math.min(320, availableHeight)
  return {
    viewportWidth,
    viewportHeight,
    minWidth,
    minHeight,
    maxWidth: Math.max(minWidth, Math.min(820, availableWidth)),
    maxHeight: Math.max(minHeight, Math.min(860, availableHeight))
  }
}

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(value, maximum))

const splitMarkdownTableRow = line => {
  const trimmed = line.trim()
  if (!trimmed.includes('|')) return []
  return trimmed
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map(cell => cell.trim())
}

const normalizeMarkdownTables = source => {
  const lines = source.split('\n')
  for (let index = 0; index < lines.length - 1; index += 1) {
    const headerCells = splitMarkdownTableRow(lines[index])
    const separatorCells = splitMarkdownTableRow(lines[index + 1])
    if (
      headerCells.length < 2
      || separatorCells.length < 2
      || !separatorCells.every(cell => /^:?-{3,}:?$/.test(cell))
    ) {
      continue
    }
    const normalizedSeparators = headerCells.map((_, cellIndex) => separatorCells[cellIndex] || '---')
    lines[index + 1] = `| ${normalizedSeparators.join(' | ')} |`
  }
  return lines.join('\n')
}

const renderMarkdown = content => {
  const source = normalizeMarkdownTables(String(content || ''))
  try {
    const html = marked.parse(source, {
      gfm: true,
      breaks: true
    })
    return DOMPurify.sanitize(html, {
      USE_PROFILES: { html: true },
      ALLOW_DATA_ATTR: false,
      FORBID_ATTR: ['style'],
      FORBID_TAGS: ['embed', 'form', 'iframe', 'object', 'script', 'style']
    })
  } catch {
    return `<p>${source
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/\n/g, '<br>')}</p>`
  }
}

const clampDialogPosition = (left = dialogPosition.value?.left, top = dialogPosition.value?.top) => {
  if (!dialogRef.value || left == null || top == null) return
  const rect = dialogRef.value.getBoundingClientRect()
  const { viewportWidth, viewportHeight } = getResizeLimits()
  dialogPosition.value = {
    left: clamp(left, 0, Math.max(0, viewportWidth - rect.width)),
    top: clamp(top, 0, Math.max(0, viewportHeight - rect.height))
  }
}

const clampDialogBounds = () => {
  if (!dialogRef.value) return
  const limits = getResizeLimits()
  if (limits.viewportWidth <= 780) {
    dialogSize.value = null
    dialogPosition.value = null
    return
  }
  const rect = dialogRef.value.getBoundingClientRect()
  const width = dialogSize.value
    ? clamp(dialogSize.value.width, limits.minWidth, limits.maxWidth)
    : rect.width
  const height = dialogSize.value
    ? clamp(dialogSize.value.height, limits.minHeight, limits.maxHeight)
    : rect.height
  const left = clamp(dialogPosition.value?.left ?? rect.left, 0, Math.max(0, limits.viewportWidth - width))
  const top = clamp(dialogPosition.value?.top ?? rect.top, 0, Math.max(0, limits.viewportHeight - height))
  if (dialogSize.value) {
    dialogSize.value = { width, height }
  }
  dialogPosition.value = { left, top }
}

const startDrag = event => {
  if (
    !event.isPrimary
    || event.button !== 0
    || event.target.closest('button')
    || !dialogRef.value
    || dragState
    || resizeState
  ) return
  const rect = dialogRef.value.getBoundingClientRect()
  dialogPosition.value = { left: rect.left, top: rect.top }
  dragState = {
    pointerId: event.pointerId,
    handle: event.currentTarget,
    startX: event.clientX,
    startY: event.clientY,
    left: rect.left,
    top: rect.top
  }
  dragging.value = true
  event.currentTarget.setPointerCapture(event.pointerId)
  event.preventDefault()
}

const dragDialog = event => {
  if (!dragState || event.pointerId !== dragState.pointerId) return
  clampDialogPosition(
    dragState.left + event.clientX - dragState.startX,
    dragState.top + event.clientY - dragState.startY
  )
}

const stopDrag = event => {
  if (!dragState || (event?.pointerId != null && event.pointerId !== dragState.pointerId)) return
  const { handle, pointerId } = dragState
  dragState = null
  dragging.value = false
  if (handle.hasPointerCapture(pointerId)) handle.releasePointerCapture(pointerId)
  saveDialogBounds()
}

const startResize = (event, direction) => {
  if (
    !event.isPrimary
    || event.button !== 0
    || !dialogRef.value
    || dragState
    || resizeState
  ) return
  const rect = dialogRef.value.getBoundingClientRect()
  dialogPosition.value = { left: rect.left, top: rect.top }
  dialogSize.value = { width: rect.width, height: rect.height }
  resizeState = {
    pointerId: event.pointerId,
    handle: event.currentTarget,
    direction,
    startX: event.clientX,
    startY: event.clientY,
    left: rect.left,
    top: rect.top,
    width: rect.width,
    height: rect.height
  }
  resizing.value = true
  event.currentTarget.setPointerCapture(event.pointerId)
  event.preventDefault()
  event.stopPropagation()
}

const resizeDialog = event => {
  if (!resizeState || event.pointerId !== resizeState.pointerId) return
  const { direction, startX, startY, left, top, width, height } = resizeState
  const limits = getResizeLimits()
  const deltaX = event.clientX - startX
  const deltaY = event.clientY - startY
  let nextLeft = left
  let nextTop = top
  let nextWidth = width
  let nextHeight = height

  if (direction.includes('e')) {
    nextWidth = clamp(
      width + deltaX,
      limits.minWidth,
      Math.min(limits.maxWidth, limits.viewportWidth - left)
    )
  } else if (direction.includes('w')) {
    nextWidth = clamp(
      width - deltaX,
      limits.minWidth,
      Math.min(limits.maxWidth, left + width)
    )
    nextLeft = left + width - nextWidth
  }

  if (direction.includes('s')) {
    nextHeight = clamp(
      height + deltaY,
      limits.minHeight,
      Math.min(limits.maxHeight, limits.viewportHeight - top)
    )
  } else if (direction.includes('n')) {
    nextHeight = clamp(
      height - deltaY,
      limits.minHeight,
      Math.min(limits.maxHeight, top + height)
    )
    nextTop = top + height - nextHeight
  }

  dialogPosition.value = { left: nextLeft, top: nextTop }
  dialogSize.value = { width: nextWidth, height: nextHeight }
}

const stopResize = event => {
  if (!resizeState || (event?.pointerId != null && event.pointerId !== resizeState.pointerId)) return
  const { handle, pointerId } = resizeState
  resizeState = null
  resizing.value = false
  if (handle.hasPointerCapture(pointerId)) handle.releasePointerCapture(pointerId)
  saveDialogBounds()
}

const handleViewportResize = async () => {
  stopDrag()
  stopResize()
  restoreDialogBounds()
  await nextTick()
  clampDialogBounds()
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const loadStatus = async () => {
  statusController?.abort()
  const controller = new AbortController()
  statusController = controller
  statusLoading.value = true
  statusError.value = ''
  try {
    const response = await request.get('/ai/status', { signal: controller.signal })
    if (!response.success) {
      throw new Error(response.message || '固固助手配置读取失败')
    }
    apiConfigured.value = Boolean(response.data?.configured)
    configurationError.value = response.data?.configurationError || ''
  } catch (error) {
    if (controller.signal.aborted) return
    statusError.value = error.response?.data?.message || error.message || '固固助手配置读取失败，请稍后重试'
  } finally {
    if (statusController === controller) {
      statusLoading.value = false
      await scrollToBottom()
    }
  }
}

const clearConversation = () => {
  if (historyOpen.value || sending.value || orderDraftBusy.value) return
  historyGeneration += 1
  pendingHistoryId = ''
  clearTimeout(historySaveTimer)
  orderFlow.reset()
  messages.value = []
  failedQuestion.value = ''
  sendError.value = ''
  draft.value = ''
  activeHistoryId.value = ''
  composerRef.value?.focus()
}

const handleComposerSubmit = () => {
  const content = draft.value.trim()
  if (!content || sending.value || orderDraftBusy.value || !apiConfigured.value) return
  if (canCreateOrder.value && orderDraftOpen.value) {
    draft.value = ''
    orderFlow.submit(content)
    return
  }
  if (canCreateOrder.value && looksLikeGuGuOrderRequest(content)) {
    orderFlow.start()
    draft.value = ''
    failedQuestion.value = ''
    sendError.value = ''
    orderFlow.submit(content)
    return
  }
  sendMessage()
}

const sendMessage = async (question = draft.value) => {
  const content = question.trim()
  if (!content || sending.value || !apiConfigured.value) return
  if (Array.from(content).length > 4000) {
    sendError.value = '每次提问最多 4000 个字符'
    return
  }

  messages.value.push({ role: 'user', content })
  if (question === draft.value) draft.value = ''
  failedQuestion.value = ''
  sendError.value = ''
  sending.value = true
  const controller = new AbortController()
  replyController = controller
  await scrollToBottom()

  try {
    const context = messages.value.slice(-19)
      .map(({ role, content }) => ({ role, content }))
    while (context.length > 1 && context.reduce((sum, item) => sum + Array.from(item.content).length, 0) > 60000) {
      context.splice(0, 2)
    }
    const response = await request.post(
      '/ai/chat',
      { messages: context },
      { timeout: 75000, signal: controller.signal }
    )
    if (!response.success) {
      const error = new Error(response.message || '固固助手暂时无法回答')
      error.apiCode = response.code
      throw error
    }
    if (!response.data?.content) throw new Error('固固助手没有返回有效回复，请重试')
    messages.value.push({
      role: 'assistant',
      content: response.data.content,
      orderQueryUsed: Boolean(response.data.orderQueryUsed),
      truncated: Boolean(response.data.truncated)
    })
  } catch (error) {
    messages.value.pop()
    failedQuestion.value = content
    const code = error.response?.data?.code || error.apiCode
    sendError.value = controller.signal.aborted
      ? '已停止等待回复。'
      : error.response?.data?.message || '固固助手请求失败，请稍后重试。'
    if (['missing_api_key', 'invalid_api_key'].includes(code)) {
      apiConfigured.value = false
      configurationError.value = code === 'invalid_api_key' ? sendError.value : ''
      if (!draft.value) draft.value = content
    }
  } finally {
    sending.value = false
    replyController = null
    await scrollToBottom()
    if (props.modelValue) composerRef.value?.focus()
  }
}

const stopWaiting = () => {
  replyController?.abort()
  orderFlow.cancel()
}

const handleComposerKeydown = event => {
  if (event.key !== 'Enter' || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey) return
  if (event.isComposing || composing.value || event.keyCode === 229) return
  event.preventDefault()
  handleComposerSubmit()
}

const handleKeydown = event => {
  if (event.key === 'Escape') {
    event.stopPropagation()
    close()
  }
  if (event.key !== 'Tab') return
  const focusable = [...(dialogRef.value?.querySelectorAll('button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled])') || [])]
    .filter(element => element.getClientRects().length)
  const first = focusable[0]
  const last = focusable.at(-1)
  if (!first) {
    event.preventDefault()
    return
  }
  if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.value)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(() => props.modelValue, async isOpen => {
  if (!isOpen) {
    stopDrag()
    stopResize()
    await nextTick()
    if (previousFocus?.isConnected) previousFocus.focus()
    return
  }
  previousFocus = document.activeElement
  restoreDialogBounds()
  await nextTick()
  clampDialogBounds()
  dialogRef.value?.focus()
  await loadStatus()
  if (props.modelValue && !sending.value && !orderDraftBusy.value) composerRef.value?.focus()
})

watch(() => messages.value.length, scrollToBottom)
watch(orderDraftBusy, async busy => {
  await scrollToBottom()
  if (!busy && props.modelValue) composerRef.value?.focus()
})
watch(canCreateOrder, allowed => {
  if (!allowed) orderFlow.reset()
})

const handleWindowBlur = () => {
  stopDrag()
  stopResize()
}

onMounted(() => {
  window.addEventListener('resize', handleViewportResize)
  window.addEventListener('blur', handleWindowBlur)
})

onUnmounted(() => {
  stopDrag()
  stopResize()
  window.removeEventListener('resize', handleViewportResize)
  window.removeEventListener('blur', handleWindowBlur)
  replyController?.abort()
  statusController?.abort()
  orderFlow.reset()
  clearTimeout(historyNoticeTimer)
  clearTimeout(historySaveTimer)
})
</script>

<style scoped>
.nomi-admin-layer {
  position: fixed;
  inset: 0;
  z-index: 4000;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 74px 22px 22px;
  background: rgba(15, 23, 42, 0.2);
  color: #172033;
  font-size: 14px;
  letter-spacing: 0;
}

.nomi-admin-dialog {
  display: flex;
  width: min(430px, calc(100vw - 28px));
  height: min(640px, calc(100vh - 96px));
  height: min(640px, calc(100dvh - 96px));
  box-sizing: border-box;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #dbe3eb;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.2);
}

.nomi-admin-dialog.is-resizing {
  user-select: none;
}

.nomi-resize-handle {
  position: absolute;
  z-index: 5;
  touch-action: none;
}

.nomi-resize-handle.is-n,
.nomi-resize-handle.is-s {
  right: 12px;
  left: 12px;
  height: 8px;
  cursor: ns-resize;
}

.nomi-resize-handle.is-n {
  top: 0;
}

.nomi-resize-handle.is-s {
  bottom: 0;
}

.nomi-resize-handle.is-e,
.nomi-resize-handle.is-w {
  top: 12px;
  bottom: 12px;
  width: 8px;
  cursor: ew-resize;
}

.nomi-resize-handle.is-e {
  right: 0;
}

.nomi-resize-handle.is-w {
  left: 0;
}

.nomi-resize-handle.is-ne,
.nomi-resize-handle.is-se,
.nomi-resize-handle.is-sw,
.nomi-resize-handle.is-nw {
  width: 16px;
  height: 16px;
}

.nomi-resize-handle.is-ne {
  top: 0;
  right: 0;
  cursor: nesw-resize;
}

.nomi-resize-handle.is-se {
  right: 0;
  bottom: 0;
  cursor: nwse-resize;
}

.nomi-resize-handle.is-sw {
  bottom: 0;
  left: 0;
  cursor: nesw-resize;
}

.nomi-resize-handle.is-nw {
  top: 0;
  left: 0;
  cursor: nwse-resize;
}

.nomi-resize-handle.is-se::after {
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 7px;
  height: 7px;
  border-right: 2px solid #94a3b8;
  border-bottom: 2px solid #94a3b8;
  content: '';
  opacity: 0.85;
}

.nomi-admin-header {
  display: flex;
  min-height: 66px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 16px;
  border-bottom: 1px solid #e8edf2;
  flex: 0 0 66px;
  cursor: move;
  touch-action: none;
  user-select: none;
}

.nomi-admin-header.is-dragging {
  cursor: grabbing;
}

.nomi-admin-title-wrap,
.nomi-admin-header-actions {
  display: flex;
  align-items: center;
}

.nomi-admin-title-wrap {
  min-width: 0;
  gap: 10px;
}

.nomi-admin-avatar {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  flex: 0 0 36px;
  border-radius: 6px;
  color: #08745a;
  background: transparent;
}

.nomi-admin-header h2 {
  margin: 0;
  color: #172033;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.35;
}

.nomi-admin-header-actions {
  gap: 4px;
}

.nomi-icon-button,
.nomi-send-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  cursor: pointer;
}

.nomi-icon-button {
  width: 32px;
  height: 32px;
  border-radius: 5px;
  color: #596579;
  background: transparent;
}

.nomi-icon-button:hover {
  color: #08745a;
  background: #e9f8f3;
}

.nomi-admin-history-panel {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  padding: 14px 16px;
  overflow: hidden;
  background: #f8fafb;
}

.nomi-admin-history-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
}

.nomi-admin-history-heading > div,
.nomi-history-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.nomi-admin-history-heading strong {
  color: #172033;
  font-size: 14px;
}

.nomi-admin-history-heading span,
.nomi-history-copy small {
  color: #64748b;
  font-size: 11px;
}

.nomi-history-close,
.nomi-history-delete {
  display: inline-flex;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 5px;
  color: #596579;
  background: transparent;
  cursor: pointer;
}

.nomi-history-close:hover,
.nomi-history-delete:hover {
  color: #08745a;
  background: #e9f8f3;
}

.nomi-history-notice {
  margin: 8px 0 0;
  color: #596579;
  font-size: 12px;
}

.nomi-history-error {
  margin-top: 10px;
  color: #b42318;
  font-size: 12px;
  line-height: 1.6;
}

.nomi-history-error .nomi-link-button {
  margin-left: 8px;
}

.nomi-history-spinner {
  animation: nomi-history-spin 1s linear infinite;
}

@keyframes nomi-history-spin {
  to {
    transform: rotate(360deg);
  }
}

.nomi-history-empty {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  color: #64748b;
  font-size: 13px;
}

.nomi-history-list {
  min-height: 0;
  flex: 1;
  margin-top: 10px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.nomi-history-item {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 4px;
  padding: 5px 3px 5px 8px;
  border-bottom: 1px solid #e2e8f0;
}

.nomi-history-item.is-active {
  background: #eef8f4;
}

.nomi-history-open {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 9px;
  padding: 6px 2px;
  border: 0;
  color: #596579;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.nomi-history-copy strong {
  overflow: hidden;
  color: #253349;
  font-size: 12px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nomi-history-copy small {
  margin-top: 3px;
}

.nomi-history-delete {
  color: #7b8797;
}

.nomi-history-delete:hover {
  color: #b42318;
  background: #fff1f2;
}

.nomi-history-open:disabled,
.nomi-history-delete:disabled {
  cursor: default;
  opacity: 0.5;
}

.nomi-admin-messages {
  min-height: 0;
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: #f8fafb;
  user-select: text;
  -webkit-user-select: text;
  overscroll-behavior: contain;
}

.nomi-admin-state,
.nomi-admin-empty {
  color: #596579;
  font-size: 13px;
  line-height: 1.65;
  text-align: center;
}

.nomi-admin-state {
  padding: 42px 12px;
}

.nomi-admin-state-error {
  color: #b42318;
}

.nomi-admin-empty {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.nomi-welcome-avatar {
  width: 54px;
  height: 54px;
  margin-bottom: 14px;
}

.nomi-truncated {
  display: block;
  margin-top: 8px;
  color: #596579;
  font-size: 11px;
}

.nomi-order-source {
  display: block;
  margin-top: 8px;
  color: #08745a;
  font-size: 11px;
}

.nomi-send-error {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  color: #b42318;
  background: #fff1f2;
  font-size: 12px;
  line-height: 1.5;
}

.nomi-send-error .nomi-link-button {
  flex: 0 0 auto;
}

.nomi-icon-button:disabled {
  cursor: default;
  opacity: 0.4;
}

.nomi-admin-dialog button:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

.nomi-history-open:focus-visible,
.nomi-history-delete:focus-visible,
.nomi-history-close:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

.nomi-empty-icon {
  display: inline-flex;
  width: 46px;
  height: 46px;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border-radius: 50%;
  color: #08745a;
  background: #e9f8f3;
}

.nomi-admin-empty strong {
  color: #172033;
  font-size: 14px;
}

.nomi-admin-empty p {
  max-width: 280px;
  margin: 8px 0 16px;
}

.nomi-message-row {
  display: flex;
  margin-bottom: 12px;
}

.nomi-message-row.is-user {
  justify-content: flex-end;
}

.nomi-message-bubble {
  max-width: 84%;
  padding: 10px 12px;
  border-radius: 7px;
  color: #263247;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  font-size: 13px;
  line-height: 1.65;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.nomi-markdown {
  white-space: normal;
}

.nomi-markdown :deep(:first-child) {
  margin-top: 0;
}

.nomi-markdown :deep(:last-child) {
  margin-bottom: 0;
}

.nomi-markdown :deep(p) {
  margin: 0 0 9px;
}

.nomi-markdown :deep(h1),
.nomi-markdown :deep(h2),
.nomi-markdown :deep(h3),
.nomi-markdown :deep(h4) {
  margin: 0 0 9px;
  color: #172033;
  font-size: 14px;
  line-height: 1.45;
}

.nomi-markdown :deep(h1) {
  font-size: 16px;
}

.nomi-markdown :deep(h2) {
  font-size: 15px;
}

.nomi-markdown :deep(ul),
.nomi-markdown :deep(ol) {
  margin: 0 0 9px;
  padding-left: 20px;
}

.nomi-markdown :deep(li + li) {
  margin-top: 4px;
}

.nomi-markdown :deep(blockquote) {
  margin: 0 0 9px;
  padding: 6px 10px;
  border-left: 3px solid #9bdac8;
  color: #596579;
  background: #f4faf8;
}

.nomi-markdown :deep(code) {
  padding: 1px 4px;
  border-radius: 3px;
  color: #08745a;
  background: #e9f8f3;
  font-size: 0.92em;
}

.nomi-markdown :deep(pre) {
  max-width: 100%;
  margin: 0 0 9px;
  padding: 9px 10px;
  overflow-x: auto;
  border-radius: 5px;
  color: #e8edf2;
  background: #172033;
}

.nomi-markdown :deep(pre code) {
  padding: 0;
  color: inherit;
  background: transparent;
}

.nomi-markdown :deep(table) {
  display: block;
  width: max-content;
  min-width: 100%;
  max-width: 100%;
  margin: 0 0 9px;
  overflow-x: auto;
  border-collapse: collapse;
  font-size: 12px;
  line-height: 1.45;
}

.nomi-markdown :deep(th),
.nomi-markdown :deep(td) {
  min-width: 72px;
  padding: 6px 8px;
  border: 1px solid #dbe3eb;
  text-align: left;
  vertical-align: top;
}

.nomi-markdown :deep(th) {
  color: #172033;
  background: #eef5f3;
  font-weight: 700;
  white-space: nowrap;
}

.nomi-markdown :deep(td) {
  background: #ffffff;
}

.nomi-markdown :deep(a) {
  color: #08745a;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.nomi-markdown :deep(hr) {
  margin: 10px 0;
  border: 0;
  border-top: 1px solid #dbe3eb;
}

.nomi-markdown :deep(img) {
  max-width: 100%;
  height: auto;
}

.nomi-message-row.is-user .nomi-message-bubble {
  color: #ffffff;
  background: #0f9f78;
  border-color: #0f9f78;
}

.nomi-loading-bubble {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 13px 14px;
}

.nomi-loading-bubble span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #0f9f78;
  animation: nomi-pulse 1.1s ease-in-out infinite;
}

.nomi-loading-bubble span:nth-child(2) {
  animation-delay: 0.14s;
}

.nomi-loading-bubble span:nth-child(3) {
  animation-delay: 0.28s;
}

.nomi-admin-composer {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 12px 14px;
  border-top: 1px solid #e8edf2;
  background: #ffffff;
  flex: 0 0 auto;
}

.nomi-admin-composer textarea {
  min-height: 42px;
  min-width: 0;
  max-height: 150px;
  flex: 1;
  resize: vertical;
  padding: 10px 11px;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  color: #172033;
  background: #ffffff;
  font: inherit;
  font-size: 13px;
  line-height: 1.5;
}

.nomi-admin-composer textarea:focus {
  outline: none;
  border-color: #0f9f78;
  box-shadow: 0 0 0 3px rgba(15, 159, 120, 0.1);
}

.nomi-send-button {
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  border-radius: 5px;
  color: #ffffff;
  background: #0f9f78;
}

.nomi-send-button:hover {
  background: #08745a;
}

.nomi-send-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.nomi-primary-button {
  display: inline-flex;
  height: 36px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 13px;
  border: 1px solid #0f9f78;
  border-radius: 5px;
  color: #ffffff;
  background: #0f9f78;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.nomi-primary-button:hover {
  background: #08745a;
}

.nomi-link-button {
  padding: 0;
  border: 0;
  color: #08745a;
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-weight: 650;
}

.nomi-link-button:hover {
  text-decoration: underline;
  text-underline-offset: 3px;
}

@keyframes nomi-pulse {
  0%, 100% {
    opacity: 0.35;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-2px);
  }
}

@media (max-width: 780px) {
  .nomi-admin-layer {
    align-items: flex-end;
    padding: 0;
  }

  .nomi-admin-dialog {
    width: 100%;
    height: min(680px, calc(100vh - 62px));
    height: min(680px, calc(100dvh - 62px));
    border-right: 0;
    border-bottom: 0;
    border-left: 0;
    border-radius: 8px 8px 0 0;
  }

  .nomi-resize-handle {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .nomi-loading-bubble span {
    animation: none;
  }
}
</style>
