<template>
  <Teleport to="body">
    <Transition name="chat-window">
      <div
        v-if="modelValue"
        class="chat-window-layer"
        @keydown.esc="close"
      >
        <section
          ref="windowRef"
          :style="windowStyle"
          class="chat-window"
          role="dialog"
          aria-modal="false"
          aria-label="留言对话"
        >
          <header
            :class="['chat-window-header', { dragging }]"
            title="按住此处拖动留言窗口"
            @pointerdown="startDrag"
          >
            <div class="chat-contact">
              <div class="chat-avatar" aria-hidden="true">
                <span>{{ contactInitials }}</span>
                <img
                  v-if="contact?.avatarUrl"
                  :src="contact.avatarUrl"
                  alt=""
                  @error="hideBrokenAvatar"
                >
              </div>

              <div class="chat-contact-info">
                <strong>{{ contactName }}</strong>
                <span>
                  <i :class="{ online: contact?.online }"></i>
                  {{ contact?.online ? '在线' : '留言' }}
                  <template v-if="contact?.position"> · {{ contact.position }}</template>
                </span>
              </div>
            </div>

            <button
              class="chat-icon-button"
              type="button"
              title="关闭留言"
              aria-label="关闭留言"
              @click="close"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18"/>
              </svg>
            </button>
          </header>

          <div
            ref="messageListRef"
            class="chat-message-list"
            aria-live="polite"
          >
            <div v-if="loading && !displayedMessages.length" class="chat-empty">
              <strong>正在加载留言...</strong>
            </div>

            <div v-else-if="loadError && !displayedMessages.length" class="chat-empty">
              <strong>留言加载失败</strong>
              <span>{{ loadError }}</span>
            </div>

            <div v-else-if="!displayedMessages.length" class="chat-empty">
              <span class="chat-empty-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.8 8.8 0 0 1-3.8-.9L4 19l.9-3.1A7.4 7.4 0 0 1 4.5 12 7.5 7.5 0 0 1 12 4.5a7.5 7.5 0 0 1 8 7Z"/>
                  <path d="M8.5 12h.01M12 12h.01M15.5 12h.01"/>
                </svg>
              </span>
              <strong>开始留言</strong>
              <span>发送一条消息给 {{ contactName }}</span>
            </div>

            <template v-else>
              <div
                v-for="message in displayedMessages"
                :key="message.id"
                :class="['chat-message-row', { 'is-mine': message.sender === 'me' }]"
              >
                <div class="chat-message-content">
                  <div
                    v-if="message.type === 'file'"
                    class="chat-file-message"
                    role="button"
                    tabindex="0"
                    title="下载附件"
                    @click="downloadAttachment(message)"
                    @keydown.enter="downloadAttachment(message)"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <path d="M14 2v6h6M8 13h8M8 17h5"/>
                    </svg>
                    <span>
                      <strong>{{ message.fileName }}</strong>
                      <small>{{ message.fileSize }}</small>
                    </span>
                  </div>
                  <p v-else>{{ message.text }}</p>
                  <time>{{ message.time }}</time>
                </div>
              </div>
            </template>
          </div>

          <footer class="chat-composer">
            <div v-if="actionError" class="chat-action-error" role="alert">
              {{ actionError }}
            </div>

            <div v-if="peerTransfer" class="peer-transfer-progress" aria-live="polite">
              <div class="peer-transfer-heading">
                <span>
                  <strong>{{ peerTransfer.fileName }}</strong>
                  <small>{{ peerTransferStatusText }}</small>
                </span>
                <button
                  v-if="peerTransferCancelable"
                  type="button"
                  @click="cancelPeerTransfer"
                >取消</button>
              </div>
              <div class="peer-transfer-track" aria-hidden="true">
                <i :style="{ width: `${peerTransferPercent}%` }"></i>
              </div>
              <span class="peer-transfer-summary">
                {{ formatFileSize(peerTransfer.transferredBytes) }} / {{ formatFileSize(peerTransfer.totalBytes) }}
                <b>{{ peerTransferPercent }}%</b>
              </span>
            </div>

            <div v-if="selectedFile" class="chat-selected-file">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <path d="M14 2v6h6"/>
              </svg>
              <span>
                <strong>{{ selectedFile.name }}</strong>
                <small>{{ formatFileSize(selectedFile.size) }}</small>
              </span>
              <div class="transfer-mode-switch" aria-label="附件发送方式">
                <button
                  type="button"
                  :class="{ active: selectedTransferMode === 'peer' }"
                  :disabled="!peerTransferAvailable"
                  title="双方在线时文件不经过服务器"
                  @click="setTransferMode('peer')"
                >在线直传</button>
                <button
                  type="button"
                  :class="{ active: selectedTransferMode === 'server' }"
                  :disabled="selectedFile.size > serverAttachmentLimit"
                  title="保存到服务器，支持对方离线接收，最大10MB"
                  @click="setTransferMode('server')"
                >离线附件</button>
              </div>
              <button
                class="selected-file-remove"
                type="button"
                title="移除附件"
                aria-label="移除附件"
                @click="clearSelectedFile"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 6l12 12M18 6 6 18"/>
                </svg>
              </button>
            </div>

            <div class="chat-composer-row">
              <textarea
                ref="composerRef"
                v-model.trim="draftMessage"
                rows="1"
                maxlength="1000"
                placeholder="输入留言，按 Enter 发送"
                aria-label="留言内容"
                @keydown.enter.exact.prevent="sendMessage"
              ></textarea>

              <input
                ref="fileInputRef"
                class="chat-file-input"
                type="file"
                @change="handleFileChange"
              >

              <button
                class="chat-icon-button chat-attach-button"
                type="button"
                :disabled="peerTransferCancelable"
                title="选择附件"
                aria-label="选择附件"
                @click="openFilePicker"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m21.4 11.6-8.9 8.9a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.7-8.7"/>
                </svg>
              </button>

              <button
                class="chat-send-button"
                type="button"
                :disabled="!canSend || sending"
                @click="sendMessage"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m22 2-7 20-4-9-9-4Z"/>
                  <path d="M22 2 11 13"/>
                </svg>
                <span>{{ sendButtonText }}</span>
              </button>
            </div>
          </footer>
        </section>
      </div>
    </Transition>

    <Transition name="peer-request">
      <section
        v-if="incomingTransfer"
        class="peer-request-card"
        role="dialog"
        aria-modal="true"
        aria-label="在线文件接收请求"
      >
        <div class="peer-request-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <path d="M14 2v6h6M12 18v-6M9.5 14.5 12 12l2.5 2.5"/>
          </svg>
        </div>
        <div class="peer-request-copy">
          <strong>{{ incomingTransfer.peer?.displayName || '同事' }} 请求发送文件</strong>
          <span>{{ incomingTransfer.fileName }}</span>
          <small>{{ formatFileSize(incomingTransfer.fileSize) }} · 局域网在线直传</small>
        </div>
        <div class="peer-request-actions">
          <button type="button" :disabled="processingIncoming" @click="rejectIncomingTransfer">
            拒绝
          </button>
          <button
            class="primary"
            type="button"
            :disabled="processingIncoming || peerTransferCancelable"
            @click="acceptIncomingTransfer"
          >{{ processingIncoming ? '建立连接中' : '同意接收' }}</button>
        </div>
      </section>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import request from '@/api/request'
import { subscribeAdminRealtime } from '@/utils/adminRealtime'
import {
  canStreamPeerFileToDisk,
  choosePeerFileDestination,
  createPeerFileReceiver,
  createPeerFileSender,
  supportsPeerFileTransfer
} from '@/utils/peerFileTransfer'

const CHAT_WINDOW_POSITION_KEY = 'order-system-chat-window-position'
const CHAT_WINDOW_EDGE_GAP = 12
const SERVER_ATTACHMENT_LIMIT = 10 * 1024 * 1024

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  contact: {
    type: Object,
    default: () => ({
      id: 'demo-contact',
      displayName: '通讯录好友',
      position: '',
      online: false,
      avatarUrl: ''
    })
  }
})

const emit = defineEmits(['update:modelValue', 'message-sent', 'open-contact'])

const windowRef = ref(null)
const messageListRef = ref(null)
const composerRef = ref(null)
const fileInputRef = ref(null)
const draftMessage = ref('')
const selectedFile = ref(null)
const selectedTransferMode = ref('server')
const displayedMessages = ref([])
const loading = ref(false)
const sending = ref(false)
const loadError = ref('')
const actionError = ref('')
const windowPosition = ref(null)
const dragging = ref(false)
const peerTransfer = ref(null)
const incomingTransfer = ref(null)
const processingIncoming = ref(false)

let dragPointerId = null
let dragStartX = 0
let dragStartY = 0
let dragStartLeft = 0
let dragStartTop = 0
let dragWidth = 0
let dragHeight = 0
let previousUserSelect = ''
let refreshTimer = null
let unsubscribeRealtime = null
let unsubscribeTransferRealtime = null
let transferFallbackTimer = null
let activePeerSession = null
let syncingTransfers = false
let applyingPeerAnswer = false
let peerAnswerApplied = false

const serverAttachmentLimit = SERVER_ATTACHMENT_LIMIT

const contactName = computed(() => {
  return props.contact?.displayName || props.contact?.name || '通讯录好友'
})

const contactInitials = computed(() => {
  const name = String(contactName.value).trim()
  return name ? name.slice(-2) : '好友'
})

const canSend = computed(() => {
  return Boolean(draftMessage.value || selectedFile.value) && !peerTransferCancelable.value
})

const peerTransferAvailable = computed(() => (
  Boolean(props.contact?.online) && supportsPeerFileTransfer()
))

const peerTransferCancelable = computed(() => (
  Boolean(peerTransfer.value) && ['preparing', 'offered', 'connecting', 'transferring', 'sent'].includes(
    peerTransfer.value.status
  )
))

const peerTransferPercent = computed(() => {
  const total = Number(peerTransfer.value?.totalBytes || 0)
  const transferred = Number(peerTransfer.value?.transferredBytes || 0)
  if (!total) return 0
  return Math.min(100, Math.round((transferred / total) * 100))
})

const peerTransferStatusText = computed(() => {
  const labels = {
    preparing: '正在生成局域网连接',
    offered: '等待对方同意接收',
    connecting: '对方已同意，正在建立连接',
    transferring: peerTransfer.value?.direction === 'incoming' ? '正在接收' : '正在发送',
    sent: '文件已发送，等待对方保存完成',
    completed: '传输完成',
    rejected: '对方已拒绝',
    cancelled: '传输已取消',
    failed: peerTransfer.value?.error || '传输失败',
    expired: '接收请求已过期'
  }
  return labels[peerTransfer.value?.status] || '在线直传'
})

const sendButtonText = computed(() => {
  if (sending.value) return selectedTransferMode.value === 'peer' ? '连接中' : '发送中'
  if (selectedFile.value && selectedTransferMode.value === 'peer') return '发起直传'
  return '发送'
})

const windowStyle = computed(() => {
  if (!windowPosition.value) return {}

  return {
    top: `${windowPosition.value.top}px`,
    left: `${windowPosition.value.left}px`,
    right: 'auto',
    bottom: 'auto'
  }
})

const formatMessageTime = value => {
  if (!value) return ''
  const normalized = String(value).replace(' ', 'T')
  const date = new Date(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(normalized)
    ? `${normalized}Z`
    : normalized)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

const normalizeMessage = message => ({
  ...message,
  fileName: message.attachment?.fileName || '',
  fileSize: message.attachment ? formatFileSize(message.attachment.fileSize) : '',
  downloadUrl: message.attachment?.downloadUrl || '',
  time: formatMessageTime(message.createdAt)
})

const loadMessages = async ({ silent = false } = {}) => {
  if (!props.modelValue || !props.contact?.id) return
  if (!silent) loading.value = true
  loadError.value = ''
  try {
    const response = await request.get(`/admin/messages/with/${props.contact.id}/messages`)
    displayedMessages.value = (response?.messages || []).map(normalizeMessage)
    await scrollToBottom()
  } catch (error) {
    loadError.value = error?.response?.data?.message || '请稍后重试'
  } finally {
    loading.value = false
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const close = () => {
  emit('update:modelValue', false)
}

const appendSentMessage = message => {
  if (!message) return
  displayedMessages.value.push(normalizeMessage(message))
  emit('message-sent', message)
  scrollToBottom()
}

const sendTextContent = async content => {
  if (!content) return null
  const response = await request.post('/admin/messages', {
    recipientEmployeeId: props.contact.id,
    content,
    clientMessageId: `${Date.now()}-${Math.random().toString(16).slice(2)}`
  })
  appendSentMessage(response.message)
  return response.message
}

const clearSelectedFile = () => {
  selectedFile.value = null
  selectedTransferMode.value = 'server'
  if (fileInputRef.value) fileInputRef.value.value = ''
}

const reportPeerStatus = async (status, reason = '') => {
  const transferId = peerTransfer.value?.id
  if (!transferId) return null
  try {
    return await request.post(`/admin/peer-transfers/${transferId}/status`, { status, reason })
  } catch (error) {
    if (error?.response?.status !== 409) throw error
    return null
  }
}

const closePeerSession = async ({ abort = false } = {}) => {
  const session = activePeerSession
  activePeerSession = null
  if (!session) return
  if (abort && typeof session.abort === 'function') {
    await session.abort()
    return
  }
  session.close?.()
}

const failPeerTransfer = async error => {
  const message = error?.message || '局域网文件传输失败'
  if (peerTransfer.value?.status === 'sent') return
  if (peerTransfer.value) {
    peerTransfer.value = {
      ...peerTransfer.value,
      status: 'failed',
      error: message,
      terminalHandled: true
    }
  }
  actionError.value = message
  try {
    await reportPeerStatus('failed', message)
  } catch {
    // 原始连接错误优先展示，状态还会通过过期机制收敛。
  }
  await closePeerSession({ abort: true })
}

const startPeerTransfer = async file => {
  if (!supportsPeerFileTransfer()) {
    throw new Error('当前浏览器不支持局域网在线直传')
  }
  if (!props.contact?.online) {
    throw new Error('对方当前不在线，请改用10MB以内的离线附件')
  }

  peerTransfer.value = {
    id: '',
    direction: 'outgoing',
    fileName: file.name,
    totalBytes: file.size,
    transferredBytes: 0,
    status: 'preparing'
  }
  peerAnswerApplied = false
  const session = createPeerFileSender({
    file,
    onProgress: transferredBytes => {
      if (!peerTransfer.value) return
      peerTransfer.value = { ...peerTransfer.value, transferredBytes }
    },
    onStatus: status => {
      if (!peerTransfer.value) return
      peerTransfer.value = { ...peerTransfer.value, status }
      if (status === 'transferring') {
        reportPeerStatus('transferring').catch(error => failPeerTransfer(error))
      }
    },
    onComplete: () => {
      if (!peerTransfer.value) return
      peerTransfer.value = {
        ...peerTransfer.value,
        status: 'sent',
        transferredBytes: file.size
      }
    },
    onError: failPeerTransfer
  })
  activePeerSession = session
  try {
    const offer = await session.createOffer()
    const response = await request.post('/admin/peer-transfers', {
      recipientEmployeeId: props.contact.id,
      fileName: file.name,
      fileSize: file.size,
      mimeType: file.type || 'application/octet-stream',
      offer
    }, { timeout: 45000 })
    peerTransfer.value = {
      ...peerTransfer.value,
      id: response.transfer.id,
      status: 'offered'
    }
  } catch (error) {
    await closePeerSession({ abort: true })
    peerTransfer.value = null
    throw error
  }
}

const sendMessage = async () => {
  if (!canSend.value || sending.value || !props.contact?.id) return

  sending.value = true
  actionError.value = ''
  const file = selectedFile.value
  const text = draftMessage.value
  try {
    if (file && selectedTransferMode.value === 'peer') {
      await startPeerTransfer(file)
      if (text) await sendTextContent(text)
    } else if (file) {
      const formData = new FormData()
      formData.append('recipientEmployeeId', String(props.contact.id))
      formData.append('content', text)
      formData.append('file', file)
      const response = await request.post('/admin/messages/attachments', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000
      })
      appendSentMessage(response.message)
    } else {
      await sendTextContent(text)
    }
    draftMessage.value = ''
    clearSelectedFile()
    composerRef.value?.focus()
  } catch (error) {
    actionError.value = error?.response?.data?.message || error?.response?.data?.error ||
      error?.message || '留言发送失败'
  } finally {
    sending.value = false
  }
}

const openFilePicker = () => {
  fileInputRef.value?.click()
}

const handleFileChange = event => {
  const file = event.target.files?.[0] || null
  actionError.value = ''
  selectedFile.value = file
  if (!file) return
  if (file.size > SERVER_ATTACHMENT_LIMIT && !peerTransferAvailable.value) {
    actionError.value = '超过10MB的文件需要对方在线并使用支持WebRTC的浏览器'
    event.target.value = ''
    selectedFile.value = null
    return
  }
  selectedTransferMode.value = peerTransferAvailable.value ? 'peer' : 'server'
}

const setTransferMode = mode => {
  if (mode === 'peer' && !peerTransferAvailable.value) {
    actionError.value = '在线直传需要对方在线且双方浏览器支持WebRTC'
    return
  }
  if (mode === 'server' && selectedFile.value?.size > SERVER_ATTACHMENT_LIMIT) {
    actionError.value = '离线附件最大支持10MB'
    return
  }
  actionError.value = ''
  selectedTransferMode.value = mode
}

const formatFileSize = size => {
  if (!size) return '0 B'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`
}

const syncPeerTransfers = async () => {
  if (syncingTransfers || !supportsPeerFileTransfer()) return
  syncingTransfers = true
  try {
    if (peerTransfer.value?.id && !peerTransfer.value.terminalHandled) {
      const response = await request.get(`/admin/peer-transfers/${peerTransfer.value.id}`)
      const remote = response.transfer
      if (
        peerTransfer.value.direction === 'outgoing' &&
        remote.status === 'accepted' && remote.answer && !applyingPeerAnswer && !peerAnswerApplied
      ) {
        applyingPeerAnswer = true
        peerTransfer.value = { ...peerTransfer.value, status: 'connecting' }
        try {
          await activePeerSession?.applyAnswer(remote.answer)
          peerAnswerApplied = true
        } catch (error) {
          await failPeerTransfer(error)
        } finally {
          applyingPeerAnswer = false
        }
      } else if (['completed', 'rejected', 'cancelled', 'failed', 'expired'].includes(remote.status)) {
        peerTransfer.value = {
          ...peerTransfer.value,
          status: remote.status,
          error: remote.failureReason || '',
          terminalHandled: true
        }
        await closePeerSession({ abort: remote.status !== 'completed' })
        if (remote.status === 'completed' && props.modelValue) {
          await loadMessages({ silent: true })
          emit('message-sent')
        }
      }
    }

    const pendingResponse = await request.get('/admin/peer-transfers/pending')
    const pending = pendingResponse?.transfers || []
    if (!peerTransferCancelable.value) {
      incomingTransfer.value = pending[0] || null
    }
  } catch (error) {
    if (error?.response?.status !== 403 && error?.response?.status !== 404) {
      console.error('同步在线文件传输失败', error)
    }
  } finally {
    syncingTransfers = false
  }
}

const rejectIncomingTransfer = async () => {
  if (!incomingTransfer.value || processingIncoming.value) return
  processingIncoming.value = true
  try {
    await request.post(`/admin/peer-transfers/${incomingTransfer.value.id}/respond`, {
      accepted: false
    })
    incomingTransfer.value = null
  } catch (error) {
    actionError.value = error?.response?.data?.message || '拒绝文件失败'
  } finally {
    processingIncoming.value = false
  }
}

const acceptIncomingTransfer = async () => {
  const incoming = incomingTransfer.value
  if (!incoming || processingIncoming.value || peerTransferCancelable.value) return
  processingIncoming.value = true
  let writable = null
  try {
    if (canStreamPeerFileToDisk()) {
      writable = await choosePeerFileDestination(incoming.fileName)
    }
    emit('open-contact', incoming.peer)
    peerTransfer.value = {
      id: incoming.id,
      direction: 'incoming',
      fileName: incoming.fileName,
      totalBytes: Number(incoming.fileSize),
      transferredBytes: 0,
      status: 'connecting'
    }
    const session = createPeerFileReceiver({
      metadata: incoming,
      writable,
      onProgress: transferredBytes => {
        if (!peerTransfer.value) return
        peerTransfer.value = { ...peerTransfer.value, transferredBytes }
      },
      onStatus: status => {
        if (!peerTransfer.value) return
        peerTransfer.value = { ...peerTransfer.value, status }
      },
      onComplete: async () => {
        if (!peerTransfer.value) return
        peerTransfer.value = {
          ...peerTransfer.value,
          status: 'completed',
          transferredBytes: Number(incoming.fileSize)
        }
        try {
          await reportPeerStatus('completed')
          peerTransfer.value = { ...peerTransfer.value, terminalHandled: true }
          await nextTick()
          await loadMessages({ silent: true })
          emit('message-sent')
        } catch (error) {
          actionError.value = error?.response?.data?.message || '文件已保存，但完成状态登记失败'
        } finally {
          await closePeerSession()
        }
      },
      onError: failPeerTransfer
    })
    activePeerSession = session
    const answer = await session.createAnswer(incoming.offer)
    await request.post(`/admin/peer-transfers/${incoming.id}/respond`, {
      accepted: true,
      answer
    }, { timeout: 45000 })
    incomingTransfer.value = null
  } catch (error) {
    if (error?.name !== 'AbortError') {
      await failPeerTransfer(error)
      incomingTransfer.value = null
    }
  } finally {
    processingIncoming.value = false
  }
}

const cancelPeerTransfer = async () => {
  if (!peerTransferCancelable.value) return
  try {
    await reportPeerStatus('cancelled')
  } catch {
    // 本地立即终止，远端会在连接断开或信令过期后结束。
  }
  await closePeerSession({ abort: true })
  if (peerTransfer.value) {
    peerTransfer.value = {
      ...peerTransfer.value,
      status: 'cancelled',
      terminalHandled: true
    }
  }
}

const hideBrokenAvatar = event => {
  event.currentTarget.style.display = 'none'
}

const downloadAttachment = message => {
  if (message.downloadUrl) window.open(message.downloadUrl, '_blank', 'noopener')
}

const loadStoredPosition = () => {
  try {
    const rawPosition = window.localStorage.getItem(CHAT_WINDOW_POSITION_KEY)
    if (!rawPosition) return

    const parsedPosition = JSON.parse(rawPosition)
    if (!Number.isFinite(parsedPosition?.left) || !Number.isFinite(parsedPosition?.top)) {
      return
    }

    windowPosition.value = {
      left: parsedPosition.left,
      top: parsedPosition.top
    }
  } catch {
    windowPosition.value = null
  }
}

const savePosition = () => {
  if (!windowPosition.value) return

  try {
    window.localStorage.setItem(
      CHAT_WINDOW_POSITION_KEY,
      JSON.stringify(windowPosition.value)
    )
  } catch {
    // 浏览器禁用本地存储时仍保留当前页面内的拖动位置。
  }
}

const getClampedPosition = (left, top, width = dragWidth, height = dragHeight) => {
  const maxLeft = Math.max(
    CHAT_WINDOW_EDGE_GAP,
    window.innerWidth - width - CHAT_WINDOW_EDGE_GAP
  )
  const maxTop = Math.max(
    CHAT_WINDOW_EDGE_GAP,
    window.innerHeight - height - CHAT_WINDOW_EDGE_GAP
  )

  return {
    left: Math.min(Math.max(CHAT_WINDOW_EDGE_GAP, left), maxLeft),
    top: Math.min(Math.max(CHAT_WINDOW_EDGE_GAP, top), maxTop)
  }
}

const clampStoredPosition = (persist = false) => {
  if (!windowPosition.value || !windowRef.value) return

  const rect = windowRef.value.getBoundingClientRect()
  const nextPosition = getClampedPosition(
    windowPosition.value.left,
    windowPosition.value.top,
    rect.width,
    rect.height
  )

  const changed = nextPosition.left !== windowPosition.value.left ||
    nextPosition.top !== windowPosition.value.top
  windowPosition.value = nextPosition
  if (persist && changed) savePosition()
}

const startDrag = event => {
  if (event.button !== 0 || event.target?.closest?.('button') || !windowRef.value) return

  const rect = windowRef.value.getBoundingClientRect()
  windowPosition.value = {
    left: rect.left,
    top: rect.top
  }
  dragPointerId = event.pointerId
  dragStartX = event.clientX
  dragStartY = event.clientY
  dragStartLeft = rect.left
  dragStartTop = rect.top
  dragWidth = rect.width
  dragHeight = rect.height
  dragging.value = true
  previousUserSelect = document.body.style.userSelect
  document.body.style.userSelect = 'none'

  window.addEventListener('pointermove', handleDragMove)
  window.addEventListener('pointerup', stopDrag)
  window.addEventListener('pointercancel', stopDrag)
  event.preventDefault()
}

const handleDragMove = event => {
  if (!dragging.value || event.pointerId !== dragPointerId) return

  windowPosition.value = getClampedPosition(
    dragStartLeft + event.clientX - dragStartX,
    dragStartTop + event.clientY - dragStartY
  )
}

const stopDrag = event => {
  if (event.pointerId !== dragPointerId) return

  dragging.value = false
  dragPointerId = null
  document.body.style.userSelect = previousUserSelect
  window.removeEventListener('pointermove', handleDragMove)
  window.removeEventListener('pointerup', stopDrag)
  window.removeEventListener('pointercancel', stopDrag)
  savePosition()
}

const handleViewportResize = () => {
  clampStoredPosition(true)
}

watch(
  () => [props.modelValue, props.contact?.id],
  ([visible]) => {
    if (refreshTimer) {
      window.clearInterval(refreshTimer)
      refreshTimer = null
    }
    if (!visible) return
    displayedMessages.value = []
    draftMessage.value = ''
    clearSelectedFile()
    actionError.value = ''
    loadMessages()
    refreshTimer = window.setInterval(() => loadMessages({ silent: true }), 60000)
    nextTick(() => clampStoredPosition(true))
    nextTick(() => composerRef.value?.focus())
  },
  { immediate: true }
)

onMounted(() => {
  loadStoredPosition()
  unsubscribeRealtime = subscribeAdminRealtime('messages', () => {
    if (props.modelValue) loadMessages({ silent: true })
  })
  unsubscribeTransferRealtime = subscribeAdminRealtime('transfers', syncPeerTransfers)
  transferFallbackTimer = window.setInterval(syncPeerTransfers, 60000)
  syncPeerTransfers()
  window.addEventListener('resize', handleViewportResize)
})

onUnmounted(() => {
  if (dragging.value) {
    dragging.value = false
    document.body.style.userSelect = previousUserSelect
  }
  window.removeEventListener('pointermove', handleDragMove)
  window.removeEventListener('pointerup', stopDrag)
  window.removeEventListener('pointercancel', stopDrag)
  window.removeEventListener('resize', handleViewportResize)
  unsubscribeRealtime?.()
  unsubscribeTransferRealtime?.()
  if (refreshTimer) window.clearInterval(refreshTimer)
  if (transferFallbackTimer) window.clearInterval(transferFallbackTimer)
  closePeerSession({ abort: true })
})

defineExpose({ close })
</script>

<style scoped>
.chat-window-layer {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;

  position: fixed;
  inset: 0;
  z-index: 10000;
  pointer-events: none;
}

.chat-window {
  position: absolute;
  right: 24px;
  bottom: 24px;
  display: flex;
  width: min(430px, calc(100vw - 32px));
  height: min(650px, calc(100vh - 48px));
  flex-direction: column;
  overflow: hidden;
  pointer-events: auto;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 18px 46px rgba(15, 23, 42, 0.2);
}

.chat-window-header {
  display: flex;
  min-height: 70px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 14px 0 18px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border);
  cursor: move;
  touch-action: none;
  user-select: none;
}

.chat-window-header.dragging {
  cursor: grabbing;
}

.chat-contact {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.chat-avatar {
  position: relative;
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  place-items: center;
  overflow: hidden;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
}

.chat-avatar img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chat-contact-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.chat-contact-info strong {
  overflow: hidden;
  font-size: 15px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-contact-info span {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-contact-info i {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 4px;
  vertical-align: 1px;
  background: var(--text-muted);
  border-radius: 50%;
}

.chat-contact-info i.online {
  background: var(--accent);
}

.chat-icon-button {
  display: inline-flex;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.chat-icon-button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.chat-icon-button:focus-visible,
.chat-send-button:focus-visible,
.chat-composer textarea:focus-visible,
.chat-selected-file button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.chat-icon-button svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.chat-message-list {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  padding: 16px 14px;
  overflow-y: auto;
  background: #f4f7f8;
  scrollbar-color: var(--border-strong) transparent;
  scrollbar-width: thin;
}

.chat-message-list::-webkit-scrollbar {
  width: 7px;
}

.chat-message-list::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 999px;
}

.chat-message-row {
  display: flex;
  justify-content: flex-start;
}

.chat-message-row.is-mine {
  justify-content: flex-end;
}

.chat-message-content {
  display: flex;
  max-width: 78%;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.is-mine .chat-message-content {
  align-items: flex-end;
}

.chat-message-content p {
  margin: 0;
  padding: 9px 11px;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 5px 7px 7px 7px;
  font-size: 13px;
  line-height: 1.55;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.is-mine .chat-message-content p {
  color: #ffffff;
  background: var(--accent);
  border-color: var(--accent);
  border-radius: 7px 5px 7px 7px;
}

.chat-message-content time {
  padding: 0 3px;
  color: var(--text-muted);
  font-size: 10px;
  line-height: 1.3;
}

.chat-file-message {
  display: flex;
  min-width: 190px;
  align-items: center;
  gap: 9px;
  padding: 10px;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 5px 7px 7px 7px;
}

.is-mine .chat-file-message {
  color: #ffffff;
  background: var(--accent);
  border-color: var(--accent);
  border-radius: 7px 5px 7px 7px;
}

.chat-file-message > svg {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.chat-file-message > span {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.chat-file-message strong,
.chat-file-message small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-file-message strong {
  font-size: 12px;
  font-weight: 650;
}

.chat-file-message small {
  color: var(--text-secondary);
  font-size: 10px;
}

.is-mine .chat-file-message small {
  color: rgba(255, 255, 255, 0.76);
}

.chat-empty {
  display: flex;
  min-height: 220px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6px;
  margin: auto 0;
  color: var(--text-muted);
  text-align: center;
}

.chat-empty strong {
  color: var(--text-secondary);
  font-size: 14px;
}

.chat-empty > span:last-child {
  font-size: 12px;
}

.chat-empty-icon {
  display: grid;
  width: 42px;
  height: 42px;
  margin-bottom: 4px;
  place-items: center;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 50%;
}

.chat-empty-icon svg {
  width: 21px;
  height: 21px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.chat-composer {
  padding: 10px 12px 12px;
  background: var(--panel-bg);
  border-top: 1px solid var(--border);
}

.chat-action-error {
  margin-bottom: 8px;
  color: #b42318;
  font-size: 12px;
  line-height: 1.45;
}

.chat-selected-file {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
  margin-bottom: 8px;
  padding: 6px 8px;
  color: var(--text-secondary);
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 5px;
  font-size: 11px;
}

.chat-selected-file > svg {
  width: 15px;
  height: 15px;
  flex: 0 0 15px;
  fill: none;
  stroke: var(--accent-dark);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.chat-selected-file > span {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.chat-selected-file > span strong,
.chat-selected-file > span small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-selected-file > span strong {
  color: var(--text-secondary);
  font-size: 11px;
}

.chat-selected-file > span small {
  color: var(--text-muted);
  font-size: 10px;
}

.chat-selected-file .selected-file-remove {
  display: inline-flex;
  width: 22px;
  height: 22px;
  flex: 0 0 22px;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  padding: 0;
  color: var(--text-muted);
  background: transparent;
  border: 0;
  border-radius: 4px;
  cursor: pointer;
}

.chat-selected-file .selected-file-remove:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.chat-selected-file .selected-file-remove svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.transfer-mode-switch {
  display: inline-flex;
  flex: 0 0 auto;
  padding: 2px;
  background: #edf1f5;
  border-radius: 5px;
}

.chat-selected-file .transfer-mode-switch button {
  width: auto;
  height: 24px;
  flex: 0 0 auto;
  margin: 0;
  padding: 0 7px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 3px;
  font-size: 10px;
  cursor: pointer;
}

.chat-selected-file .transfer-mode-switch button.active {
  color: var(--accent-dark);
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
}

.chat-selected-file .transfer-mode-switch button:disabled {
  color: #a8b1bf;
  cursor: not-allowed;
}

.peer-transfer-progress {
  margin-bottom: 8px;
  padding: 9px 10px;
  background: #f6faf9;
  border: 1px solid #cfe7df;
  border-radius: 5px;
}

.peer-transfer-heading,
.peer-transfer-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.peer-transfer-heading > span {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.peer-transfer-heading strong {
  overflow: hidden;
  color: var(--text);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.peer-transfer-heading small,
.peer-transfer-summary {
  color: var(--text-muted);
  font-size: 10px;
}

.peer-transfer-heading button {
  flex: 0 0 auto;
  padding: 3px 7px;
  color: #b42318;
  background: #ffffff;
  border: 1px solid #f0c5c1;
  border-radius: 4px;
  font-size: 10px;
  cursor: pointer;
}

.peer-transfer-track {
  height: 5px;
  margin: 8px 0 5px;
  overflow: hidden;
  background: #dfe8e5;
  border-radius: 3px;
}

.peer-transfer-track i {
  display: block;
  height: 100%;
  background: var(--accent);
  border-radius: inherit;
  transition: width 0.16s ease;
}

.peer-transfer-summary b {
  color: var(--accent-dark);
  font-weight: 650;
}

.peer-request-card {
  position: fixed;
  top: 72px;
  right: 24px;
  z-index: 10020;
  display: grid;
  width: min(370px, calc(100vw - 32px));
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 10px 12px;
  padding: 14px;
  color: #172033;
  background: #ffffff;
  border: 1px solid #d9e1e8;
  border-radius: 7px;
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.2);
}

.peer-request-icon {
  display: grid;
  width: 42px;
  height: 42px;
  grid-row: 1 / span 2;
  place-items: center;
  color: #08745a;
  background: #e9f8f3;
  border: 1px solid #a9e5d2;
  border-radius: 50%;
}

.peer-request-icon svg {
  width: 21px;
  height: 21px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.peer-request-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.peer-request-copy strong {
  font-size: 13px;
}

.peer-request-copy span,
.peer-request-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.peer-request-copy span {
  color: #39465a;
  font-size: 12px;
}

.peer-request-copy small {
  color: #7b8798;
  font-size: 10px;
}

.peer-request-actions {
  display: flex;
  grid-column: 2;
  justify-content: flex-end;
  gap: 7px;
}

.peer-request-actions button {
  height: 30px;
  padding: 0 10px;
  color: #596579;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  font-size: 11px;
  cursor: pointer;
}

.peer-request-actions button.primary {
  color: #ffffff;
  background: #0f9f78;
  border-color: #0f9f78;
}

.peer-request-actions button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.peer-request-enter-active,
.peer-request-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.peer-request-enter-from,
.peer-request-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.chat-composer-row {
  display: flex;
  align-items: flex-end;
  gap: 7px;
}

.chat-composer textarea {
  min-width: 0;
  min-height: 38px;
  max-height: 110px;
  flex: 1;
  padding: 9px 10px;
  resize: vertical;
  color: var(--text);
  background: var(--panel-bg);
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  box-sizing: border-box;
  font: inherit;
  font-size: 13px;
  line-height: 1.45;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.chat-composer textarea::placeholder {
  color: var(--text-muted);
}

.chat-composer textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.chat-file-input {
  display: none;
}

.chat-attach-button {
  background: var(--panel-bg);
  border-color: var(--border-strong);
}

.chat-send-button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 0 11px;
  color: #ffffff;
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
  transition: background 0.18s ease, border-color 0.18s ease, opacity 0.18s ease;
}

.chat-send-button:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.chat-send-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.chat-send-button svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.chat-window-enter-active,
.chat-window-leave-active {
  transition: opacity 0.18s ease;
}

.chat-window-enter-active .chat-window,
.chat-window-leave-active .chat-window {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.chat-window-enter-from,
.chat-window-leave-to {
  opacity: 0;
}

.chat-window-enter-from .chat-window,
.chat-window-leave-to .chat-window {
  opacity: 0;
  transform: translateY(10px);
}

@media (max-width: 780px) {
  .chat-window {
    right: 12px;
    bottom: 12px;
    width: calc(100vw - 24px);
    height: calc(100vh - 24px);
  }

  .peer-request-card {
    top: 12px;
    right: 12px;
    width: calc(100vw - 24px);
    box-sizing: border-box;
  }

  .chat-selected-file {
    flex-wrap: wrap;
  }

  .transfer-mode-switch {
    order: 4;
    width: 100%;
  }

  .chat-selected-file .transfer-mode-switch button {
    flex: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .chat-window-enter-active,
  .chat-window-leave-active,
  .chat-window-enter-active .chat-window,
  .chat-window-leave-active .chat-window,
  .chat-window-header,
  .chat-icon-button,
  .chat-composer textarea,
  .chat-send-button {
    transition: none;
  }
}
</style>
