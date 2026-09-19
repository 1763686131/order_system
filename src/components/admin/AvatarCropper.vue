<template>
  <Teleport to="body">
    <Transition name="avatar-crop">
      <div
        v-if="visible"
        class="avatar-crop-layer"
        @click.self="cancelCrop"
      >
        <section
          class="avatar-crop-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="avatar-crop-title"
        >
          <header class="avatar-crop-header">
            <div>
              <span>头像设置</span>
              <h2 id="avatar-crop-title">裁剪头像</h2>
            </div>
            <button
              class="crop-icon-button"
              type="button"
              title="关闭"
              :disabled="processing"
              @click="cancelCrop"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m6 6 12 12"></path>
                <path d="m18 6-12 12"></path>
              </svg>
            </button>
          </header>

          <div class="avatar-crop-body">
            <div
              ref="stageRef"
              class="avatar-crop-stage"
              :class="{ dragging }"
              role="application"
              tabindex="0"
              aria-label="头像裁剪区域"
              @pointerdown="startDrag"
              @pointermove="moveDrag"
              @pointerup="endDrag"
              @pointercancel="endDrag"
              @keydown.left.prevent="nudgeImage(-4, 0)"
              @keydown.right.prevent="nudgeImage(4, 0)"
              @keydown.up.prevent="nudgeImage(0, -4)"
              @keydown.down.prevent="nudgeImage(0, 4)"
              @wheel.prevent="handleWheel"
            >
              <img
                v-if="sourceUrl"
                ref="imageRef"
                class="avatar-crop-image"
                :src="sourceUrl"
                :style="imageStyle"
                alt=""
                draggable="false"
                @load="handleImageLoad"
                @error="handleImageError"
              />
              <div v-if="!imageReady && !loadError" class="crop-loading">
                <span></span>
                正在载入
              </div>
              <div v-if="loadError" class="crop-error" role="alert">
                {{ loadError }}
              </div>
              <div
                v-if="imageReady"
                class="avatar-crop-selection"
                :style="selectionStyle"
                aria-hidden="true"
              ></div>
            </div>

            <div class="avatar-crop-controls">
              <button
                class="crop-icon-button"
                type="button"
                title="缩小"
                :disabled="!imageReady || zoom <= 1"
                @click="adjustZoom(-0.1)"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="11" cy="11" r="7"></circle>
                  <path d="M8 11h6"></path>
                  <path d="m16.5 16.5 4 4"></path>
                </svg>
              </button>
              <label class="crop-zoom-control">
                <span>缩放</span>
                <input
                  v-model.number="zoom"
                  type="range"
                  min="1"
                  max="3"
                  step="0.01"
                  :disabled="!imageReady"
                  @input="clampOffsets"
                />
              </label>
              <button
                class="crop-icon-button"
                type="button"
                title="放大"
                :disabled="!imageReady || zoom >= 3"
                @click="adjustZoom(0.1)"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="11" cy="11" r="7"></circle>
                  <path d="M8 11h6M11 8v6"></path>
                  <path d="m16.5 16.5 4 4"></path>
                </svg>
              </button>
              <button
                class="crop-icon-button crop-reset-button"
                type="button"
                title="重置裁剪"
                :disabled="!imageReady"
                @click="resetCrop"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 9a8 8 0 1 1 2.3 8.7"></path>
                  <path d="M4 4v5h5"></path>
                </svg>
              </button>
            </div>
          </div>

          <footer class="avatar-crop-footer">
            <button
              class="crop-button crop-button-secondary"
              type="button"
              :disabled="processing"
              @click="cancelCrop"
            >
              取消
            </button>
            <button
              class="crop-button crop-button-primary"
              type="button"
              :disabled="!imageReady || processing"
              @click="confirmCrop"
            >
              {{ processing ? '处理中' : '使用此区域' }}
            </button>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  file: {
    type: [File, Blob],
    default: null
  }
})

const emit = defineEmits(['cancel', 'confirm'])

const CROP_RATIO = 0.72
const OUTPUT_SIZE = 512

const stageRef = ref(null)
const imageRef = ref(null)
const sourceUrl = ref('')
const imageReady = ref(false)
const loadError = ref('')
const processing = ref(false)
const dragging = ref(false)
const stageSize = ref(360)
const naturalWidth = ref(0)
const naturalHeight = ref(0)
const zoom = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)

let dragPointerId = null
let dragStartX = 0
let dragStartY = 0
let dragStartOffsetX = 0
let dragStartOffsetY = 0

const clamp = (value, minimum, maximum) => (
  Math.min(maximum, Math.max(minimum, value))
)

const cropMetrics = computed(() => {
  const frameSize = stageSize.value * CROP_RATIO
  const frameStart = (stageSize.value - frameSize) / 2
  if (!naturalWidth.value || !naturalHeight.value) {
    return {
      frameSize,
      frameStart,
      displayWidth: 0,
      displayHeight: 0,
      centerLeft: frameStart,
      centerTop: frameStart,
      minimumLeft: frameStart,
      maximumLeft: frameStart,
      minimumTop: frameStart,
      maximumTop: frameStart,
      left: frameStart,
      top: frameStart
    }
  }

  const baseScale = Math.max(
    frameSize / naturalWidth.value,
    frameSize / naturalHeight.value
  )
  const displayWidth = naturalWidth.value * baseScale * zoom.value
  const displayHeight = naturalHeight.value * baseScale * zoom.value
  const centerLeft = frameStart + (frameSize - displayWidth) / 2
  const centerTop = frameStart + (frameSize - displayHeight) / 2
  const minimumLeft = frameStart + frameSize - displayWidth
  const maximumLeft = frameStart
  const minimumTop = frameStart + frameSize - displayHeight
  const maximumTop = frameStart

  return {
    frameSize,
    frameStart,
    displayWidth,
    displayHeight,
    centerLeft,
    centerTop,
    minimumLeft,
    maximumLeft,
    minimumTop,
    maximumTop,
    left: clamp(
      centerLeft + offsetX.value,
      minimumLeft,
      maximumLeft
    ),
    top: clamp(
      centerTop + offsetY.value,
      minimumTop,
      maximumTop
    )
  }
})

const imageStyle = computed(() => ({
  width: `${cropMetrics.value.displayWidth}px`,
  height: `${cropMetrics.value.displayHeight}px`,
  left: `${cropMetrics.value.left}px`,
  top: `${cropMetrics.value.top}px`
}))

const selectionStyle = computed(() => ({
  width: `${cropMetrics.value.frameSize}px`,
  height: `${cropMetrics.value.frameSize}px`,
  left: `${cropMetrics.value.frameStart}px`,
  top: `${cropMetrics.value.frameStart}px`
}))

function revokeSourceUrl() {
  if (sourceUrl.value) {
    URL.revokeObjectURL(sourceUrl.value)
    sourceUrl.value = ''
  }
}

function measureStage() {
  const measuredSize = stageRef.value?.clientWidth
  if (measuredSize) {
    stageSize.value = measuredSize
    clampOffsets()
  }
}

function handleImageLoad() {
  naturalWidth.value = imageRef.value?.naturalWidth || 0
  naturalHeight.value = imageRef.value?.naturalHeight || 0
  if (!naturalWidth.value || !naturalHeight.value) {
    handleImageError()
    return
  }
  loadError.value = ''
  imageReady.value = true
  resetCrop()
  nextTick(() => stageRef.value?.focus())
}

function handleImageError() {
  imageReady.value = false
  loadError.value = '图片无法读取，请重新选择'
}

function clampOffsets() {
  const metrics = cropMetrics.value
  offsetX.value = clamp(
    offsetX.value,
    metrics.minimumLeft - metrics.centerLeft,
    metrics.maximumLeft - metrics.centerLeft
  )
  offsetY.value = clamp(
    offsetY.value,
    metrics.minimumTop - metrics.centerTop,
    metrics.maximumTop - metrics.centerTop
  )
}

function resetCrop() {
  zoom.value = 1
  offsetX.value = 0
  offsetY.value = 0
  nextTick(clampOffsets)
}

function adjustZoom(amount) {
  zoom.value = Number(clamp(zoom.value + amount, 1, 3).toFixed(2))
  nextTick(clampOffsets)
}

function handleWheel(event) {
  if (!imageReady.value) return
  adjustZoom(event.deltaY < 0 ? 0.08 : -0.08)
}

function startDrag(event) {
  if (!imageReady.value || processing.value) return
  dragging.value = true
  dragPointerId = event.pointerId
  dragStartX = event.clientX
  dragStartY = event.clientY
  dragStartOffsetX = offsetX.value
  dragStartOffsetY = offsetY.value
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

function moveDrag(event) {
  if (!dragging.value || event.pointerId !== dragPointerId) return
  offsetX.value = dragStartOffsetX + event.clientX - dragStartX
  offsetY.value = dragStartOffsetY + event.clientY - dragStartY
  clampOffsets()
}

function endDrag(event) {
  if (event.pointerId !== dragPointerId) return
  dragging.value = false
  dragPointerId = null
  if (event.currentTarget.hasPointerCapture?.(event.pointerId)) {
    event.currentTarget.releasePointerCapture(event.pointerId)
  }
}

function nudgeImage(horizontal, vertical) {
  if (!imageReady.value) return
  offsetX.value += horizontal
  offsetY.value += vertical
  clampOffsets()
}

function canvasToBlob(canvas, type, quality) {
  return new Promise(resolve => canvas.toBlob(resolve, type, quality))
}

async function confirmCrop() {
  if (!imageReady.value || !imageRef.value || processing.value) return
  processing.value = true
  loadError.value = ''

  try {
    const metrics = cropMetrics.value
    const sourceX = (
      (metrics.frameStart - metrics.left) / metrics.displayWidth
    ) * naturalWidth.value
    const sourceY = (
      (metrics.frameStart - metrics.top) / metrics.displayHeight
    ) * naturalHeight.value
    const sourceWidth = (
      metrics.frameSize / metrics.displayWidth
    ) * naturalWidth.value
    const sourceHeight = (
      metrics.frameSize / metrics.displayHeight
    ) * naturalHeight.value

    const canvas = document.createElement('canvas')
    canvas.width = OUTPUT_SIZE
    canvas.height = OUTPUT_SIZE
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Canvas is unavailable')
    context.imageSmoothingEnabled = true
    context.imageSmoothingQuality = 'high'
    context.drawImage(
      imageRef.value,
      sourceX,
      sourceY,
      sourceWidth,
      sourceHeight,
      0,
      0,
      OUTPUT_SIZE,
      OUTPUT_SIZE
    )

    let blob = await canvasToBlob(canvas, 'image/webp', 0.9)
    let extension = 'webp'
    if (!blob) {
      blob = await canvasToBlob(canvas, 'image/png')
      extension = 'png'
    }
    if (!blob) throw new Error('Image export failed')

    const originalName = props.file?.name || 'avatar'
    const baseName = originalName.replace(/\.[^.]+$/, '') || 'avatar'
    const croppedFile = new File(
      [blob],
      `${baseName}-avatar.${extension}`,
      {
        type: blob.type,
        lastModified: Date.now()
      }
    )
    emit('confirm', croppedFile)
  } catch (error) {
    console.error('头像裁剪失败:', error)
    loadError.value = '头像裁剪失败，请重新选择'
  } finally {
    processing.value = false
  }
}

function cancelCrop() {
  if (processing.value) return
  emit('cancel')
}

function handleWindowResize() {
  if (props.visible) nextTick(measureStage)
}

function handleWindowKeydown(event) {
  if (props.visible && event.key === 'Escape') cancelCrop()
}

watch(
  () => [props.visible, props.file],
  async ([visible, file]) => {
    revokeSourceUrl()
    imageReady.value = false
    loadError.value = ''
    naturalWidth.value = 0
    naturalHeight.value = 0
    resetCrop()
    if (!visible || !file) return
    sourceUrl.value = URL.createObjectURL(file)
    await nextTick()
    measureStage()
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('resize', handleWindowResize)
  window.addEventListener('keydown', handleWindowKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleWindowResize)
  window.removeEventListener('keydown', handleWindowKeydown)
  revokeSourceUrl()
})
</script>

<style scoped>
.avatar-crop-layer {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --panel-bg: #fff;
  --border: #dfe5ec;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  position: fixed;
  inset: 0;
  z-index: 4000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--text);
  background: rgba(15, 23, 42, 0.48);
  box-sizing: border-box;
}

.avatar-crop-dialog {
  display: flex;
  width: min(520px, calc(100vw - 48px));
  max-height: calc(100vh - 48px);
  flex-direction: column;
  overflow: hidden;
  background: #f4f7f8;
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.24);
}

.avatar-crop-header,
.avatar-crop-footer {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  background: var(--panel-bg);
}

.avatar-crop-header {
  min-height: 74px;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  box-sizing: border-box;
}

.avatar-crop-header span {
  color: var(--accent-dark);
  font-size: 11px;
  font-weight: 700;
}

.avatar-crop-header h2 {
  margin: 4px 0 0;
  font-size: 18px;
  font-weight: 650;
}

.avatar-crop-body {
  min-height: 0;
  padding: 20px;
  overflow-y: auto;
}

.avatar-crop-stage {
  position: relative;
  width: min(360px, calc(100vw - 88px));
  aspect-ratio: 1;
  margin: 0 auto;
  overflow: hidden;
  background:
    linear-gradient(45deg, #d9e0e7 25%, transparent 25%),
    linear-gradient(-45deg, #d9e0e7 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #d9e0e7 75%),
    linear-gradient(-45deg, transparent 75%, #d9e0e7 75%),
    #eef2f6;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
  background-size: 16px 16px;
  border: 1px solid var(--border-strong);
  border-radius: 7px;
  cursor: grab;
  touch-action: none;
  user-select: none;
  box-sizing: border-box;
}

.avatar-crop-stage.dragging {
  cursor: grabbing;
}

.avatar-crop-stage:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

.avatar-crop-image {
  position: absolute;
  max-width: none;
  pointer-events: none;
  user-select: none;
}

.avatar-crop-selection {
  position: absolute;
  z-index: 2;
  border: 2px solid #fff;
  border-radius: 50%;
  box-shadow:
    0 0 0 999px rgba(15, 23, 42, 0.56),
    0 0 0 1px rgba(15, 23, 42, 0.28);
  pointer-events: none;
  box-sizing: border-box;
}

.avatar-crop-selection::before,
.avatar-crop-selection::after {
  position: absolute;
  background: rgba(255, 255, 255, 0.52);
  content: '';
}

.avatar-crop-selection::before {
  top: 50%;
  right: 8%;
  left: 8%;
  height: 1px;
}

.avatar-crop-selection::after {
  top: 8%;
  bottom: 8%;
  left: 50%;
  width: 1px;
}

.crop-loading,
.crop-error {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 20px;
  color: var(--text-secondary);
  background: rgba(244, 247, 248, 0.94);
  box-sizing: border-box;
  font-size: 13px;
  text-align: center;
}

.crop-loading span {
  width: 16px;
  height: 16px;
  border: 2px solid var(--accent-border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: crop-spin 0.7s linear infinite;
}

.crop-error {
  color: #b4232f;
}

.avatar-crop-controls {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) 34px 34px;
  align-items: end;
  gap: 8px;
  width: min(360px, calc(100vw - 88px));
  margin: 16px auto 0;
}

.crop-zoom-control {
  display: grid;
  min-width: 0;
  gap: 7px;
}

.crop-zoom-control span {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.crop-zoom-control input {
  width: 100%;
  height: 20px;
  margin: 0;
  accent-color: var(--accent);
  cursor: pointer;
}

.crop-icon-button {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
}

.crop-icon-button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.crop-icon-button:disabled,
.crop-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.crop-icon-button svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.crop-reset-button {
  margin-left: 2px;
}

.avatar-crop-footer {
  min-height: 66px;
  justify-content: flex-end;
  gap: 10px;
  padding: 13px 18px;
  border-top: 1px solid var(--border);
  box-sizing: border-box;
}

.crop-button {
  display: inline-flex;
  min-width: 104px;
  height: 38px;
  align-items: center;
  justify-content: center;
  padding: 0 18px;
  border: 1px solid transparent;
  border-radius: 5px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.crop-button-secondary {
  color: var(--text-secondary);
  background: #fff;
  border-color: var(--border-strong);
}

.crop-button-secondary:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.crop-button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.crop-button-primary:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb), 0.22);
}

.crop-icon-button:focus-visible,
.crop-button:focus-visible,
.crop-zoom-control input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.avatar-crop-enter-active,
.avatar-crop-leave-active {
  transition: opacity 0.18s ease;
}

.avatar-crop-enter-active .avatar-crop-dialog,
.avatar-crop-leave-active .avatar-crop-dialog {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.avatar-crop-enter-from,
.avatar-crop-leave-to {
  opacity: 0;
}

.avatar-crop-enter-from .avatar-crop-dialog,
.avatar-crop-leave-to .avatar-crop-dialog {
  opacity: 0;
  transform: translateY(10px);
}

@keyframes crop-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 780px) {
  .avatar-crop-layer {
    padding: 16px;
  }

  .avatar-crop-dialog {
    width: calc(100vw - 32px);
    max-height: calc(100vh - 32px);
  }

  .avatar-crop-body {
    padding: 16px;
  }

  .avatar-crop-stage,
  .avatar-crop-controls {
    width: min(320px, calc(100vw - 64px));
  }

  .avatar-crop-footer {
    padding-right: 16px;
    padding-left: 16px;
  }

  .crop-button {
    flex: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .avatar-crop-enter-active,
  .avatar-crop-leave-active,
  .avatar-crop-enter-active .avatar-crop-dialog,
  .avatar-crop-leave-active .avatar-crop-dialog {
    transition: none;
  }
}
</style>
