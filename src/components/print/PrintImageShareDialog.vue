<template>
  <Teleport to="body">
    <section
      v-if="visible"
      ref="dialogRef"
      class="print-image-share"
      role="dialog"
      aria-modal="true"
      aria-label="分享单据图片"
      tabindex="-1"
      @keydown.esc.prevent.stop="emit('close')"
      @keydown.tab="trapFocus"
    >
      <header class="image-share-header">
        <div>
          <h3>分享单据图片</h3>
          <p>{{ fileName }}</p>
        </div>
        <button
          ref="closeButtonRef"
          type="button"
          class="image-share-icon"
          title="返回打印预览"
          aria-label="返回打印预览"
          @click="emit('close')"
        >
          <X :size="20" aria-hidden="true" />
        </button>
      </header>
      <div class="image-share-toolbar">
        <span>长按图片保存或转发</span>
        <button
          type="button"
          class="image-share-icon"
          :title="zoomed ? '适应屏幕' : '查看原图'"
          :aria-label="zoomed ? '适应屏幕' : '查看原图'"
          :aria-pressed="zoomed"
          :disabled="!imageWidth || imageError"
          @click="zoomed = !zoomed"
        >
          <ZoomOut v-if="zoomed" :size="18" aria-hidden="true" />
          <ZoomIn v-else :size="18" aria-hidden="true" />
        </button>
      </div>
      <div ref="imageAreaRef" class="image-share-body">
        <div v-if="imageError" class="image-share-error" role="alert">
          <p>图片加载失败</p>
          <button type="button" class="image-share-button" @click="emit('regenerate')">
            <RefreshCw :size="16" aria-hidden="true" />重新生成
          </button>
        </div>
        <img
          v-else
          :src="src"
          :alt="fileName || '单据图片'"
          class="image-share-picture"
          :style="zoomed ? { width: `${imageWidth}px`, maxWidth: 'none' } : undefined"
          @load="imageWidth = $event.target.naturalWidth"
          @error="imageError = true"
        />
      </div>
      <footer class="image-share-footer">
        <p v-if="notice" role="status">{{ notice }}</p>
        <div>
          <button
            v-if="canShare"
            type="button"
            class="image-share-button"
            :disabled="sharing || imageError"
            @click="emit('share')"
          >
            <Share2 :size="17" aria-hidden="true" />{{ sharing ? '分享中' : '系统分享' }}
          </button>
          <a
            :href="downloadUrl || src"
            :download="fileName"
            target="_blank"
            rel="noopener"
            class="image-share-button image-share-save"
          >
            <Download :size="17" aria-hidden="true" />保存图片
          </a>
        </div>
      </footer>
    </section>
  </Teleport>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { Download, RefreshCw, Share2, X, ZoomIn, ZoomOut } from '@lucide/vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  src: { type: String, default: '' },
  downloadUrl: { type: String, default: '' },
  fileName: { type: String, default: '' },
  canShare: { type: Boolean, default: false },
  sharing: { type: Boolean, default: false },
  notice: { type: String, default: '' }
})
const emit = defineEmits(['close', 'share', 'regenerate'])
const dialogRef = ref(null)
const closeButtonRef = ref(null)
const imageAreaRef = ref(null)
const zoomed = ref(false)
const imageWidth = ref(0)
const imageError = ref(false)

watch([() => props.visible, () => props.src], () => {
  zoomed.value = false
  imageWidth.value = 0
  imageError.value = false
})

watch(zoomed, () => {
  imageAreaRef.value?.scrollTo(0, 0)
}, { flush: 'post' })

watch(() => props.visible, async (visible, previous, onCleanup) => {
  if (!visible) return
  const activeElement = document.activeElement
  const overflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  onCleanup(() => {
    document.body.style.overflow = overflow
    if (activeElement?.isConnected) activeElement.focus({ preventScroll: true })
  })
  await nextTick()
  if (props.visible) closeButtonRef.value?.focus({ preventScroll: true })
}, { flush: 'post', immediate: true })

function trapFocus(event) {
  const elements = [...dialogRef.value.querySelectorAll('button:not(:disabled), a[href]')]
  const first = elements[0]
  const last = elements.at(-1)
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last?.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first?.focus()
  }
}
</script>

<style scoped>
.print-image-share {
  position: fixed;
  inset: 0;
  z-index: 2147483100;
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  color: #172033;
  background: #f1f3f5;
}

.image-share-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: calc(12px + env(safe-area-inset-top, 0px)) 16px 12px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.image-share-header > div {
  min-width: 0;
}

.image-share-header h3 {
  margin: 0;
  font-size: 17px;
  line-height: 1.5;
}

.image-share-header p {
  margin: 4px 0 0;
  color: #596579;
  font-size: 12px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.image-share-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 40px;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  color: #596579;
  background: #fff;
  cursor: pointer;
}

.image-share-icon:disabled {
  opacity: 0.5;
  cursor: default;
}

.image-share-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 16px;
  color: #596579;
  font-size: 13px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.image-share-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  touch-action: pan-x pan-y pinch-zoom;
  -webkit-overflow-scrolling: touch;
}

.image-share-picture {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  margin: 0 auto;
  background: #fff;
  -webkit-touch-callout: default;
  -webkit-user-select: auto;
  user-select: auto;
}

.image-share-error {
  padding: 32px 16px;
  text-align: center;
  color: #b42318;
}

.image-share-footer {
  flex-shrink: 0;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom, 0px));
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

.image-share-footer p {
  margin: 0 0 10px;
  font-size: 13px;
  color: #596579;
}

.image-share-footer > div {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.image-share-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #172033;
  font: inherit;
  font-size: 14px;
  line-height: 1.4;
  text-decoration: none;
  cursor: pointer;
}

.image-share-button:disabled {
  opacity: 0.5;
  cursor: default;
}

.image-share-save {
  border-color: #0f9f78;
  background: #0f9f78;
  color: #fff;
}

.image-share-icon:focus-visible,
.image-share-button:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}
</style>
