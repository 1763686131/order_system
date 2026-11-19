<template>
  <Teleport to="body">
    <div class="tutorial-layer" :style="{ zIndex: step.layer ?? 3100 }">
      <div v-if="layout?.highlight" class="tutorial-highlight" :style="highlightStyle" aria-hidden="true"></div>
      <section
        ref="panelRef"
        class="tutorial-card"
        :style="panelStyle"
        tabindex="-1"
        aria-labelledby="tutorial-step-title"
        aria-describedby="tutorial-step-description"
      >
        <header class="tutorial-card-header">
          <span>第 {{ number }} 步 / 共 {{ total }} 步</span>
          <button class="tutorial-close" type="button" aria-label="退出引导" @click="closeGuide">
            <X :size="17" aria-hidden="true" />
          </button>
        </header>
        <h3 id="tutorial-step-title">{{ step.title }}</h3>
        <p id="tutorial-step-description">{{ step.description }}</p>
        <footer class="tutorial-actions">
          <button v-if="canGoBack" class="tutorial-back" type="button" @click="emit('back')">上一步</button>
          <button class="tutorial-next" type="button" :disabled="step.actionTarget && !actionReady" @click="next">
            {{ number === total ? '结束引导' : '下一步' }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, shallowRef, watch } from 'vue'
import { X } from '@lucide/vue'

const props = defineProps({
  step: { type: Object, required: true },
  number: { type: Number, required: true },
  total: { type: Number, required: true },
  nextTarget: String,
  canGoBack: Boolean
})
const emit = defineEmits(['next', 'back', 'close', 'target-missing'])
const panelRef = ref(null)
const layout = shallowRef(null)
const actionReady = ref(false)
let activeTarget = null

const highlightStyle = computed(() => {
  const { left, top, right, bottom } = layout.value.highlight
  return { left: `${left}px`, top: `${top}px`, width: `${right - left}px`, height: `${bottom - top}px` }
})

const panelStyle = computed(() => {
  if (!layout.value) return { visibility: 'hidden' }
  const { x, y, maxWidth, maxHeight } = layout.value
  return { left: `${x}px`, top: `${y}px`, maxWidth: `${maxWidth}px`, maxHeight: `${maxHeight}px` }
})

function closeGuide() {
  if (activeTarget?.isConnected && panelRef.value?.contains(document.activeElement)) {
    const focusable = 'button:not(:disabled), input:not(:disabled), select:not(:disabled)'
    const control = activeTarget.matches(focusable) ? activeTarget : activeTarget.querySelector(focusable)
    control?.focus({ preventScroll: true })
  }
  emit('close')
}

function next() {
  if (props.number === props.total) closeGuide()
  else if (props.step.actionTarget) findTarget(props.step.actionTarget)?.click()
  else emit('next')
}

function findTarget(key) {
  return Array.from(document.querySelectorAll(`[data-tutorial-target="${key}"]`))
    .find(element => element.getClientRects().length)
}

function getViewport() {
  const visual = window.visualViewport
  const left = Math.round(visual?.offsetLeft ?? 0)
  const top = Math.round(visual?.offsetTop ?? 0)
  return {
    left,
    top,
    right: left + Math.floor(visual?.width ?? window.innerWidth),
    bottom: top + Math.floor(visual?.height ?? window.innerHeight)
  }
}

function getClippingParents(target) {
  if (getComputedStyle(target).position === 'fixed') return []
  const parents = []
  for (let parent = target.parentElement; parent && parent !== document.body; parent = parent.parentElement) {
    const { overflowX, overflowY, position } = getComputedStyle(parent)
    if (overflowX !== 'visible' || overflowY !== 'visible') {
      parents.push({ parent, clipX: overflowX !== 'visible', clipY: overflowY !== 'visible' })
    }
    if (position === 'fixed') break
  }
  return parents
}

function getHighlight(target, parents, viewport) {
  const bounds = target.getBoundingClientRect()
  const listbox = target.querySelector('[role="listbox"]')
  const popup = listbox?.getClientRects().length ? listbox.getBoundingClientRect() : bounds
  let left = Math.max(Math.min(bounds.left, popup.left), viewport.left)
  let top = Math.max(Math.min(bounds.top, popup.top), viewport.top)
  let right = Math.min(Math.max(bounds.right, popup.right), viewport.right)
  let bottom = Math.min(Math.max(bounds.bottom, popup.bottom), viewport.bottom)
  for (const { parent, clipX, clipY } of parents) {
    const clip = parent.getBoundingClientRect()
    if (clipX) {
      left = Math.max(left, clip.left)
      right = Math.min(right, clip.right)
    }
    if (clipY) {
      top = Math.max(top, clip.top)
      bottom = Math.min(bottom, clip.bottom)
    }
  }
  if (left >= right || top >= bottom) return null

  const padding = 4
  return {
    left: Math.max(viewport.left, Math.floor(left) - padding),
    top: Math.max(viewport.top, Math.floor(top) - padding),
    right: Math.min(viewport.right, Math.ceil(right) + padding),
    bottom: Math.min(viewport.bottom, Math.ceil(bottom) + padding)
  }
}

function getPanelPosition(highlight, panel, viewport) {
  const gap = 12
  const left = viewport.left + gap
  const top = viewport.top + gap
  const right = viewport.right - gap
  const bottom = viewport.bottom - gap
  const maxWidth = Math.max(1, right - left)
  const maxHeight = Math.max(1, bottom - top)
  const width = Math.min(panel.offsetWidth, maxWidth)
  const height = Math.min(panel.scrollHeight + panel.offsetHeight - panel.clientHeight, maxHeight)
  const place = (x, y, availableHeight = maxHeight) => ({ x, y, maxWidth, maxHeight: availableHeight })
  if (!highlight) return place(right - width, bottom - height)

  const alignedX = Math.max(left, Math.min(highlight.left, right - width))
  const alignedY = Math.max(top, Math.min(highlight.top, bottom - height))
  if (highlight.right + gap + width <= right) return place(highlight.right + gap, alignedY)
  if (highlight.left - gap - width >= left) return place(highlight.left - gap - width, alignedY)
  if (highlight.bottom + gap + height <= bottom) return place(alignedX, highlight.bottom + gap)
  if (highlight.top - gap - height >= top) return place(alignedX, highlight.top - gap - height)

  const roomAbove = highlight.top - top - gap
  const roomBelow = bottom - highlight.bottom - gap
  if (Math.max(roomAbove, roomBelow) >= 118) {
    return roomAbove > roomBelow
      ? place(alignedX, top, roomAbove)
      : place(alignedX, highlight.bottom + gap, roomBelow)
  }
  return place(alignedX, roomAbove > roomBelow ? top : bottom - height)
}

watch([() => props.step, () => props.nextTarget, panelRef], ([step, nextTarget, panel], _, onCleanup) => {
  if (!panel) return
  const handleEscape = event => {
    if (event.key !== 'Escape' || event.defaultPrevented) return
    event.preventDefault()
    closeGuide()
  }
  const listeners = new AbortController()
  window.addEventListener('keydown', handleEscape, { signal: listeners.signal })
  let clippingParents = []
  let frame = 0
  let missingTimer = 0

  function updatePosition() {
    frame = 0
    const target = findTarget(step.target)
    if (step.actionTarget && nextTarget && (!step.waitForClose || !target) && findTarget(nextTarget)) {
      emit('next')
      return
    }
    if (!target) {
      if (activeTarget) emit('close')
      else if (!missingTimer) {
        layout.value = null
        missingTimer = window.setTimeout(() => emit('target-missing'), 2000)
      }
      return
    }

    if (target !== activeTarget) {
      window.clearTimeout(missingTimer)
      missingTimer = 0
      if (activeTarget) resizeObserver.unobserve(activeTarget)
      activeTarget = target
      clippingParents = getClippingParents(target)
      resizeObserver.observe(target)
      target.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'instant' })
      nextTick(() => {
        if (activeTarget === target) panel.focus({ preventScroll: true })
      })
    }

    const button = step.actionTarget ? findTarget(step.actionTarget) : null
    actionReady.value = Boolean(button && !button.matches(':disabled, [aria-disabled="true"]'))
    if (target.closest('[role="dialog"]')?.querySelector('[role="alertdialog"]')) {
      layout.value = null
      return
    }
    const viewport = getViewport()
    const highlight = getHighlight(target, clippingParents, viewport)
    const position = getPanelPosition(highlight, panel, viewport)
    layout.value = { ...position, highlight }
  }

  const schedulePosition = () => {
    if (!frame) frame = window.requestAnimationFrame(updatePosition)
  }
  const eventOptions = { passive: true, signal: listeners.signal }
  window.addEventListener('resize', schedulePosition, eventOptions)
  window.addEventListener('scroll', schedulePosition, { ...eventOptions, capture: true })
  document.addEventListener('transitionend', schedulePosition, eventOptions)
  window.visualViewport?.addEventListener('resize', schedulePosition, eventOptions)
  window.visualViewport?.addEventListener('scroll', schedulePosition, eventOptions)

  const resizeObserver = new ResizeObserver(schedulePosition)
  resizeObserver.observe(panel)

  const contentObserver = new MutationObserver(schedulePosition)
  contentObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['data-tutorial-target', 'disabled', 'aria-disabled', 'hidden']
  })

  onCleanup(() => {
    window.cancelAnimationFrame(frame)
    window.clearTimeout(missingTimer)
    listeners.abort()
    resizeObserver.disconnect()
    contentObserver.disconnect()
    activeTarget = null
  })
  updatePosition()
}, { flush: 'post' })
</script>

<style scoped>
.tutorial-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.tutorial-highlight {
  position: fixed;
  box-sizing: border-box;
  border: 2px solid #36d8a8;
  border-radius: 9px;
  box-shadow: 0 0 0 100vmax rgba(15, 23, 42, .36);
}

.tutorial-card {
  position: fixed;
  box-sizing: border-box;
  width: min(306px, calc(100vw - 24px));
  padding: 12px 14px 14px;
  overflow-y: auto;
  pointer-events: auto;
  color: #172033;
  background: #fff;
  border: 1px solid #dce8e3;
  border-radius: 10px;
  box-shadow: 0 12px 32px rgba(15, 23, 42, .22);
}

.tutorial-card:focus {
  outline: none;
}

.tutorial-card-header,
.tutorial-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tutorial-card-header {
  justify-content: space-between;
  color: #08745a;
  font-size: 12px;
  font-weight: 600;
}

.tutorial-card h3 {
  margin: 3px 0 5px;
  font-size: 16px;
}

.tutorial-card p {
  margin: 0 0 12px;
  color: #506075;
  font-size: 13px;
  line-height: 1.55;
}

.tutorial-close {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  padding: 0;
  color: #596579;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
}

.tutorial-actions {
  justify-content: flex-end;
}

.tutorial-actions button {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.tutorial-next {
  color: #fff;
  background: #08745a;
  border: 1px solid transparent;
}

.tutorial-next:hover {
  background: #065d48;
}

.tutorial-next:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.tutorial-back {
  color: #415167;
  background: #fff;
  border: 1px solid #cbd5e1;
}

.tutorial-back:hover,
.tutorial-close:hover {
  background: #f1f5f9;
}
</style>
