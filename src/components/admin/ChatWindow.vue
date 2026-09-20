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
            <div v-if="!displayedMessages.length" class="chat-empty">
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
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <path d="M14 2v6h6M8 13h8M8 17h5"/>
                    </svg>
                    <span>
                      <strong>{{ message.fileName }}</strong>
                      <small>{{ message.fileSize || '本地演示附件' }}</small>
                    </span>
                  </div>
                  <p v-else>{{ message.text }}</p>
                  <time>{{ message.time }}</time>
                </div>
              </div>
            </template>
          </div>

          <footer class="chat-composer">
            <div v-if="selectedFile" class="chat-selected-file">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <path d="M14 2v6h6"/>
              </svg>
              <span>{{ selectedFile.name }}</span>
              <button
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
                :disabled="!canSend"
                @click="sendMessage"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m22 2-7 20-4-9-9-4Z"/>
                  <path d="M22 2 11 13"/>
                </svg>
                <span>发送</span>
              </button>
            </div>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const CHAT_WINDOW_POSITION_KEY = 'order-system-chat-window-position'
const CHAT_WINDOW_EDGE_GAP = 12

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
  },
  messages: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'send'])

const windowRef = ref(null)
const messageListRef = ref(null)
const composerRef = ref(null)
const fileInputRef = ref(null)
const draftMessage = ref('')
const selectedFile = ref(null)
const displayedMessages = ref([])
const windowPosition = ref(null)
const dragging = ref(false)

let dragPointerId = null
let dragStartX = 0
let dragStartY = 0
let dragStartLeft = 0
let dragStartTop = 0
let dragWidth = 0
let dragHeight = 0
let previousUserSelect = ''

const contactName = computed(() => {
  return props.contact?.displayName || props.contact?.name || '通讯录好友'
})

const contactInitials = computed(() => {
  const name = String(contactName.value).trim()
  return name ? name.slice(-2) : '好友'
})

const canSend = computed(() => {
  return Boolean(draftMessage.value || selectedFile.value)
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

const demoMessages = computed(() => {
  return [
    {
      id: `demo-${props.contact?.id || 'contact'}-1`,
      sender: 'them',
      text: `你好，这里是和${contactName.value}的留言对话。`,
      time: '今天 09:30'
    },
    {
      id: `demo-${props.contact?.id || 'contact'}-2`,
      sender: 'me',
      text: '好的，收到。后续可以在这里留言沟通。',
      time: '今天 09:32'
    }
  ]
})

const syncMessages = () => {
  displayedMessages.value = props.messages.length
    ? props.messages.map(message => ({ ...message }))
    : demoMessages.value.map(message => ({ ...message }))
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

const sendMessage = () => {
  if (!canSend.value) return

  const file = selectedFile.value
  const message = {
    id: `local-${Date.now()}`,
    sender: 'me',
    type: file ? 'file' : 'text',
    text: draftMessage.value,
    fileName: file?.name || '',
    fileSize: file ? formatFileSize(file.size) : '',
    time: '刚刚'
  }

  displayedMessages.value.push(message)
  emit('send', {
    contact: props.contact,
    message
  })

  draftMessage.value = ''
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
  scrollToBottom()
  composerRef.value?.focus()
}

const openFilePicker = () => {
  fileInputRef.value?.click()
}

const handleFileChange = event => {
  selectedFile.value = event.target.files?.[0] || null
}

const clearSelectedFile = () => {
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

const formatFileSize = size => {
  if (!size) return '0 B'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const hideBrokenAvatar = event => {
  event.currentTarget.style.display = 'none'
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
  () => [props.modelValue, props.contact?.id, props.messages],
  ([visible]) => {
    if (!visible) return
    syncMessages()
    draftMessage.value = ''
    selectedFile.value = null
    nextTick(() => clampStoredPosition(true))
    scrollToBottom()
    nextTick(() => composerRef.value?.focus())
  },
  { deep: true, immediate: true }
)

onMounted(() => {
  loadStoredPosition()
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
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-selected-file button {
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

.chat-selected-file button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
}

.chat-selected-file button svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
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
