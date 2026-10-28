<template>
  <Teleport to="body">
    <div class="share-overlay" @click.self="close" @keydown.esc="close">
      <section
        ref="dialog"
        class="share-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="qualification-share-title"
        tabindex="-1"
        @keydown.tab="keepFocus"
      >
        <header class="dialog-header">
          <h2 id="qualification-share-title">分享二维码</h2>
          <button class="icon-button" type="button" aria-label="关闭" title="关闭" :disabled="saving" @click="close">
            <X :size="20" aria-hidden="true" />
          </button>
        </header>
        <p class="file-title">{{ title }}</p>
        <div v-if="loading" class="share-state" role="status">正在加载分享设置...</div>
        <template v-else>
          <div class="toggle-row">
            <label for="qualification-share-toggle">允许游客访问</label>
            <button
              id="qualification-share-toggle"
              class="share-switch"
              :class="{ enabled }"
              type="button"
              role="switch"
              :aria-checked="enabled"
              aria-label="允许游客访问"
              :disabled="saving || !ready"
              @click="toggleShare"
            ><span></span></button>
          </div>
          <p class="share-status" :class="{ active: enabled }">
            {{ saving ? '正在更新...' : enabled ? '分享已开启' : '分享已关闭，游客无法访问' }}
          </p>
          <template v-if="enabled && shareUrl">
            <div class="qr-preview">
              <img v-if="qrImage" :src="qrImage" width="224" height="224" :alt="`${title}的分享二维码`" />
              <span v-else role="status">{{ qrError ? '二维码生成失败' : '正在生成二维码...' }}</span>
            </div>
            <button v-if="qrError" class="text-button" type="button" @click="generateQr">重新生成</button>
            <label class="link-label" for="qualification-share-link">外部访问链接</label>
            <div class="link-row">
              <input id="qualification-share-link" ref="linkInput" :value="shareUrl" readonly @focus="$event.target.select()" />
              <button class="icon-button" type="button" :title="copied ? '已复制' : '复制链接'" :aria-label="copied ? '已复制' : '复制链接'" @click="copyLink">
                <Check v-if="copied" :size="18" aria-hidden="true" />
                <Copy v-else :size="18" aria-hidden="true" />
              </button>
            </div>
            <p v-if="isLocalAddress" class="local-address-note">当前链接使用本机地址，请通过客户可访问的域名打开系统后生成二维码。</p>
            <div class="dialog-actions">
              <a class="preview-link" :href="shareUrl" target="_blank" rel="noopener noreferrer">
                <ExternalLink :size="16" aria-hidden="true" />打开预览
              </a>
              <a v-if="qrImage" class="download-button" :href="qrImage" :download="downloadName">
                <Download :size="16" aria-hidden="true" />下载二维码
              </a>
            </div>
          </template>
          <p v-if="error" class="error-message" role="alert">{{ error }}</p>
          <button v-if="!ready" class="text-button" type="button" @click="loadSettings">重新加载</button>
        </template>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { Check, Copy, Download, ExternalLink, X } from '@lucide/vue'
import QRCode from 'qrcode'
import request from '@/api/request'

const props = defineProps({
  qualificationId: { type: String, required: true },
  title: { type: String, required: true }
})
const emit = defineEmits(['close'])
const dialog = ref(null)
const linkInput = ref(null)
const loading = ref(true)
const ready = ref(false)
const saving = ref(false)
const enabled = ref(false)
const sharePath = ref('')
const qrImage = ref('')
const qrError = ref(false)
const error = ref('')
const copied = ref(false)
const shareUrl = computed(() => sharePath.value ? new URL(sharePath.value, window.location.origin).href : '')
const isLocalAddress = ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)
const downloadName = computed(() => `${props.title.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_').slice(0, 100)}-二维码.png`)
let qrVersion = 0
let copyTimer
let disposed = false
let previousFocus
let previousBodyOverflow

function close() {
  if (!saving.value) emit('close')
}

function keepFocus(event) {
  const elements = dialog.value?.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled)')
  if (!elements?.length) return
  const first = elements[0]
  const last = elements[elements.length - 1]
  if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.value)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

async function generateQr() {
  const version = ++qrVersion
  qrImage.value = ''
  qrError.value = false
  if (!enabled.value || !shareUrl.value) return
  try {
    const image = await QRCode.toDataURL(shareUrl.value, {
      width: 768, margin: 4, errorCorrectionLevel: 'Q', color: { dark: '#000000', light: '#ffffff' }
    })
    if (!disposed && version === qrVersion && enabled.value) qrImage.value = image
  } catch {
    if (!disposed && version === qrVersion) qrError.value = true
  }
}

async function loadSettings() {
  loading.value = true
  ready.value = false
  error.value = ''
  try {
    const response = await request.get(`/hr/qualifications/${props.qualificationId}/share`)
    if (!response.success) throw new Error(response.message || '加载分享设置失败')
    if (disposed) return
    enabled.value = response.data.enabled
    sharePath.value = response.data.path || ''
    ready.value = true
    generateQr()
  } catch (failure) {
    if (!disposed) error.value = failure.response?.data?.message || failure.message || '加载分享设置失败'
  } finally {
    if (!disposed) loading.value = false
  }
}

async function toggleShare() {
  if (saving.value || !ready.value) return
  saving.value = true
  error.value = ''
  try {
    const response = await request.put(`/hr/qualifications/${props.qualificationId}/share`, { enabled: !enabled.value })
    if (!response.success) throw new Error(response.message || '更新分享开关失败')
    if (disposed) return
    enabled.value = response.data.enabled
    sharePath.value = response.data.path || ''
    copied.value = false
    generateQr()
  } catch (failure) {
    if (!disposed) error.value = failure.response?.data?.message || failure.message || '更新分享开关失败'
  } finally {
    if (!disposed) saving.value = false
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copied.value = true
    window.clearTimeout(copyTimer)
    copyTimer = window.setTimeout(() => { copied.value = false }, 2000)
  } catch {
    linkInput.value?.focus()
    linkInput.value?.select()
    error.value = '请复制已选中的链接'
  }
}

onMounted(async () => {
  previousFocus = document.activeElement
  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  await nextTick()
  dialog.value?.focus()
  loadSettings()
})

onBeforeUnmount(() => {
  disposed = true
  ++qrVersion
  window.clearTimeout(copyTimer)
  document.body.style.overflow = previousBodyOverflow
  previousFocus?.focus()
})
</script>

<style scoped>
.share-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgb(17 24 39 / 45%);
}
.share-dialog {
  width: min(100%, 460px);
  max-height: calc(100dvh - 40px);
  overflow-y: auto;
  padding: 24px;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  box-shadow: 0 20px 60px rgb(0 0 0 / 25%);
  box-sizing: border-box;
}
.dialog-header, .toggle-row, .link-row, .dialog-actions { display: flex; align-items: center; gap: 12px; }
.dialog-header, .toggle-row, .dialog-actions { justify-content: space-between; }
.dialog-header h2 { margin: 0; font-size: 18px; color: #1f2937; }
.file-title { margin: 12px 0 24px; font-size: 14px; color: #6b7280; overflow-wrap: anywhere; }
.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
}
.icon-button:hover { color: #2563eb; border-color: #93c5fd; }
.toggle-row label { font-size: 14px; font-weight: 500; }
.share-switch { position: relative; flex-shrink: 0; width: 44px; height: 24px; padding: 0; border: 0; border-radius: 12px; background: #9ca3af; cursor: pointer; }
.share-switch.enabled { background: #16a34a; }
.share-switch span { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: transform 0.15s; }
.share-switch.enabled span { transform: translateX(20px); }
button:disabled { cursor: wait; opacity: 0.6; }
.share-status { margin: 10px 0 0; font-size: 13px; color: #6b7280; }
.share-status.active { color: #15803d; }
.qr-preview { display: flex; align-items: center; justify-content: center; width: 224px; height: 224px; max-width: 100%; margin: 16px auto; color: #6b7280; font-size: 14px; }
.qr-preview img { display: block; width: 224px; height: 224px; max-width: 100%; object-fit: contain; }
.link-label { display: block; margin-bottom: 8px; font-size: 13px; }
.link-row input { width: 100%; min-width: 0; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: #f9fafb; font: inherit; font-size: 13px; color: #374151; box-sizing: border-box; }
.dialog-actions { flex-wrap: wrap; margin-top: 20px; font-size: 14px; }
.preview-link, .download-button { display: inline-flex; align-items: center; gap: 6px; text-decoration: none; }
.preview-link { color: #2563eb; }
.download-button { padding: 9px 14px; border-radius: 6px; background: #3b82f6; color: #fff; }
.download-button:hover { background: #2563eb; }
.local-address-note { margin: 12px 0 0; color: #b45309; font-size: 12px; line-height: 1.6; }
.share-state { padding: 24px 0; text-align: center; color: #6b7280; font-size: 14px; }
.error-message { margin: 16px 0 0; color: #b91c1c; font-size: 13px; }
.text-button { padding: 8px 0; border: 0; background: transparent; color: #2563eb; font: inherit; font-size: 14px; cursor: pointer; }
button:focus-visible, input:focus-visible, a:focus-visible { outline: 2px solid #2563eb; outline-offset: 3px; }
@media (max-width: 480px) {
  .share-overlay { padding: 12px; }
  .share-dialog { padding: 20px 16px; max-height: calc(100dvh - 24px); }
}
</style>
