<template>
  <Teleport to="body">
    <dialog
      ref="dialog"
      class="finance-attachment-preview"
      aria-labelledby="finance-attachment-title"
      @cancel.prevent="emit('close')"
      @click="closeOnBackdrop"
      @keydown.left.prevent="previous"
      @keydown.right.prevent="next"
    >
      <section class="voucher-dialog">
        <header class="voucher-header">
          <h2 id="finance-attachment-title">{{ title }}</h2>
          <button type="button" class="voucher-icon" title="关闭预览" aria-label="关闭预览" @click="emit('close')">
            <X :size="20" />
          </button>
        </header>
        <div class="voucher-content">
          <p v-if="loading" class="voucher-message" role="status">加载凭证中...</p>
          <div v-else-if="error" class="voucher-message" role="alert">
            <p>{{ error }}</p>
            <button type="button" class="voucher-retry" @click="loadFile">重新加载</button>
          </div>
          <div v-else-if="isPdf" class="voucher-message">
            <FileText :size="42" aria-hidden="true" />
            <p>PDF 凭证</p>
            <a :href="previewUrl" :download="currentFile.name || '凭证.pdf'">下载查看</a>
          </div>
          <img
            v-else-if="previewUrl"
            :src="previewUrl"
            :alt="currentFile.name || '凭证图片'"
            @error="error = '图片无法显示，请下载原文件查看'"
          >
        </div>
        <footer class="voucher-footer">
          <span class="voucher-filename" :title="currentFile.name">{{ currentFile.name || '凭证' }}</span>
          <nav v-if="files.length > 1" class="voucher-pagination" aria-label="切换凭证">
            <button type="button" class="voucher-icon" title="上一张" aria-label="上一张" :disabled="index === 0" @click="previous">
              <ChevronLeft :size="18" />
            </button>
            <span>{{ index + 1 }} / {{ files.length }}</span>
            <button type="button" class="voucher-icon" title="下一张" aria-label="下一张" :disabled="index === files.length - 1" @click="next">
              <ChevronRight :size="18" />
            </button>
          </nav>
          <a v-if="previewUrl" class="voucher-icon" :href="previewUrl" :download="currentFile.name || '凭证'" title="下载凭证" aria-label="下载凭证">
            <Download :size="18" />
          </a>
        </footer>
      </section>
    </dialog>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, Download, FileText, X } from '@lucide/vue'
import request from '@/api/request'

const props = defineProps({
  title: { type: String, default: '凭证预览' },
  files: { type: Array, required: true }
})
const emit = defineEmits(['close'])
const dialog = ref(null)
const index = ref(0)
const currentFile = computed(() => props.files[index.value] || {})
const loading = ref(false)
const error = ref('')
const previewUrl = ref('')
const isPdf = ref(false)
let requestVersion = 0
let controller = null
let previousOverflow = ''

function clearPreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

async function loadFile() {
  const version = ++requestVersion
  controller?.abort()
  controller = new AbortController()
  clearPreview()
  error.value = ''
  loading.value = true
  try {
    const url = currentFile.value.url
    if (!url) throw new Error('凭证地址不存在')
    const blob = await request.get(url, {
      baseURL: '',
      responseType: 'blob',
      signal: controller.signal
    })
    if (version !== requestVersion) return
    isPdf.value = blob.type === 'application/pdf' || /\.pdf$/i.test(currentFile.value.name || '')
    previewUrl.value = URL.createObjectURL(blob)
  } catch (err) {
    if (version !== requestVersion || err.code === 'ERR_CANCELED') return
    error.value = '凭证加载失败，请重新加载'
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

function previous() {
  if (index.value > 0) index.value -= 1
}

function next() {
  if (index.value < props.files.length - 1) index.value += 1
}

function closeOnBackdrop(event) {
  if (event.target !== dialog.value) return
  const bounds = dialog.value.getBoundingClientRect()
  if (event.clientX < bounds.left || event.clientX > bounds.right ||
      event.clientY < bounds.top || event.clientY > bounds.bottom) emit('close')
}

watch(() => currentFile.value.url, loadFile, { immediate: true })
onMounted(() => {
  previousOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  dialog.value.showModal()
})
onBeforeUnmount(() => {
  ++requestVersion
  controller?.abort()
  clearPreview()
  document.body.style.overflow = previousOverflow
})
</script>

<style scoped>
.finance-attachment-preview{width:min(960px,calc(100vw - 32px));max-width:none;max-height:calc(100dvh - 32px);margin:auto;padding:0;overflow:hidden;color:#172033;background:#fff;border:1px solid #dbe3eb;border-radius:7px;box-shadow:0 20px 65px rgba(15,23,42,.3)}
.finance-attachment-preview::backdrop{background:rgba(15,23,42,.68)}
.voucher-dialog{display:flex;max-height:calc(100dvh - 34px);flex-direction:column}
.voucher-header,.voucher-footer{display:flex;flex:none;align-items:center;gap:12px;padding:12px 16px}
.voucher-header{justify-content:space-between;border-bottom:1px solid #e2e8f0}
.voucher-header h2{min-width:0;margin:0;overflow-wrap:anywhere;font-size:15px;line-height:1.5}
.voucher-icon{display:inline-flex;box-sizing:border-box;width:34px;height:34px;flex:none;align-items:center;justify-content:center;padding:0;color:#596579;background:#fff;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;text-decoration:none}
.voucher-icon:hover:not(:disabled){color:#08745a;background:#e9f8f3;border-color:#a9e5d2}
.voucher-icon:disabled{opacity:.4;cursor:not-allowed}
.voucher-icon:focus-visible,.voucher-retry:focus-visible,a:focus-visible{outline:2px solid #0f9f78;outline-offset:2px}
.voucher-content{display:flex;min-height:220px;flex:1;align-items:center;justify-content:center;overflow:auto;padding:16px;background:#f4f7f8}
.voucher-content img{display:block;max-width:100%;max-height:calc(100dvh - 210px);object-fit:contain}
.voucher-message{display:flex;min-height:220px;align-items:center;justify-content:center;flex-direction:column;gap:12px;margin:0;color:#596579;font-size:14px;text-align:center}
.voucher-message p{margin:0}
.voucher-message a{color:#08745a}
.voucher-retry{padding:7px 12px;color:#08745a;background:#fff;border:1px solid #a9e5d2;border-radius:4px;cursor:pointer;font:inherit}
.voucher-footer{border-top:1px solid #e2e8f0}
.voucher-filename{min-width:0;flex:1;overflow:hidden;color:#596579;font-size:13px;text-overflow:ellipsis;white-space:nowrap}
.voucher-pagination{display:flex;flex:none;align-items:center;gap:8px;font-size:13px}
.voucher-pagination span{min-width:42px;text-align:center}
@media(max-width:600px){.voucher-header,.voucher-footer{gap:8px;padding:10px}.voucher-content{padding:10px}.voucher-header h2{font-size:14px}}
</style>
