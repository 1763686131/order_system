<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="column-order-overlay"
      @click.self="close"
      @keydown.esc.stop.prevent="close"
      @keydown.tab="trapFocus"
    >
      <section ref="dialog" class="column-order-dialog" role="dialog" aria-modal="true" :aria-label="title" tabindex="-1">
        <header class="column-order-header">
          <h2>{{ title }}</h2>
          <button class="column-order-icon" type="button" title="关闭" aria-label="关闭" @click="close">
            <X aria-hidden="true" />
          </button>
        </header>

        <ol ref="list" class="column-order-list" aria-label="表格列顺序">
          <li
            v-for="(column, index) in draftColumns"
            :key="column.key"
            :data-column-order-key="column.key"
            class="column-order-row"
            :class="{ 'is-dragging': draggingKey === column.key, 'is-fixed': column.fixed, 'is-hidden': draftHiddenKeys.includes(column.key) }"
          >
            <span v-if="column.fixed" class="column-order-lock" title="固定列">
              <Lock aria-hidden="true" />
            </span>
            <button
              v-else
              type="button"
              class="column-order-icon column-order-grip"
              :title="`拖动${column.label}`"
              :aria-label="`调整${column.label}的位置`"
              @pointerdown="startDrag($event, column.key)"
              @keydown.up.prevent="moveColumn(column.key, -1)"
              @keydown.down.prevent="moveColumn(column.key, 1)"
            >
              <GripVertical aria-hidden="true" />
            </button>
            <span class="column-order-index" aria-hidden="true">{{ index + 1 }}</span>
            <span class="column-order-label" :title="column.label">{{ column.label }}</span>
            <span v-if="column.fixed" class="column-order-fixed-label">固定</span>
            <div v-else class="column-order-row-actions">
              <button
                class="column-order-icon"
                type="button"
                :title="`上移${column.label}`"
                :aria-label="`上移${column.label}`"
                :disabled="!canMove(index, -1)"
                @click="moveColumn(column.key, -1)"
              >
                <ArrowUp aria-hidden="true" />
              </button>
              <button
                class="column-order-icon"
                type="button"
                :title="`下移${column.label}`"
                :aria-label="`下移${column.label}`"
                :disabled="!canMove(index, 1)"
                @click="moveColumn(column.key, 1)"
              >
                <ArrowDown aria-hidden="true" />
              </button>
            </div>
            <div class="column-order-visibility">
              <span class="column-order-visibility-label">{{ draftHiddenKeys.includes(column.key) ? '隐藏' : '显示' }}</span>
              <button
                class="column-order-switch"
                type="button"
                role="switch"
                :aria-checked="!draftHiddenKeys.includes(column.key)"
                :aria-label="`显示${column.label}列`"
                :title="visibilityTitle(column)"
                :disabled="!canToggleVisibility(column)"
                @click="toggleVisibility(column.key)"
              ><span aria-hidden="true"></span></button>
            </div>
          </li>
        </ol>

        <footer class="column-order-footer">
          <button class="column-order-button column-order-reset" type="button" @click="resetDraft">
            <RotateCcw aria-hidden="true" />
            恢复默认
          </button>
          <button class="column-order-button" type="button" @click="close">取消</button>
          <button class="column-order-button column-order-apply" type="button" @click="apply">应用设置</button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowDown, ArrowUp, GripVertical, Lock, RotateCcw, X } from '@lucide/vue'
import { normalizeColumnOrder, normalizeHiddenColumnKeys } from '@/composables/useTableColumnOrder'

const props = defineProps({
  visible: { type: Boolean, default: false },
  columns: { type: Array, required: true },
  defaultColumns: { type: Array, required: true },
  hiddenKeys: { type: Array, default: () => [] },
  title: { type: String, default: '调整表格列' }
})
const emit = defineEmits(['update:visible', 'apply'])
const dialog = ref(null)
const list = ref(null)
const draftColumns = ref([])
const draftHiddenKeys = ref([])
const draggingKey = ref(null)
let pointerId = null
let previousFocus = null

const stopDrag = () => {
  const wasDragging = pointerId !== null
  draggingKey.value = null
  pointerId = null
  if (!wasDragging) return
  document.removeEventListener('pointermove', moveDrag)
  document.removeEventListener('pointerup', endDrag)
  document.removeEventListener('pointercancel', endDrag)
  window.removeEventListener('blur', stopDrag)
}

const canMove = (index, direction) => {
  const target = draftColumns.value[index + direction]
  return Boolean(target && !target.fixed && !draftColumns.value[index]?.fixed)
}

const moveTo = (key, targetIndex) => {
  const index = draftColumns.value.findIndex(column => column.key === key)
  if (index < 0 || index === targetIndex || draftColumns.value[index].fixed ||
      !draftColumns.value[targetIndex] || draftColumns.value[targetIndex].fixed) return
  const next = [...draftColumns.value]
  const [column] = next.splice(index, 1)
  next.splice(targetIndex, 0, column)
  draftColumns.value = next
}

const moveColumn = (key, direction) => {
  const index = draftColumns.value.findIndex(column => column.key === key)
  if (canMove(index, direction)) moveTo(key, index + direction)
}

const moveDrag = event => {
  if (event.pointerId !== pointerId || draggingKey.value === null || !list.value) return
  event.preventDefault()
  const bounds = list.value.getBoundingClientRect()
  if (event.clientY < bounds.top + 36) list.value.scrollTop -= 12
  if (event.clientY > bounds.bottom - 36) list.value.scrollTop += 12
  const row = document.elementFromPoint(event.clientX, event.clientY)?.closest('[data-column-order-key]')
  if (!row || !list.value.contains(row)) return
  const index = draftColumns.value.findIndex(column => column.key === draggingKey.value)
  const targetIndex = draftColumns.value.findIndex(column => column.key === row.dataset.columnOrderKey)
  const rect = row.getBoundingClientRect()
  const midpoint = rect.top + rect.height / 2
  if ((index < targetIndex && event.clientY < midpoint) ||
      (index > targetIndex && event.clientY > midpoint)) return
  moveTo(draggingKey.value, targetIndex)
}

const endDrag = event => {
  if (event.pointerId === pointerId) stopDrag()
}

const startDrag = (event, key) => {
  if (event.button !== 0 || event.isPrimary === false) return
  event.preventDefault()
  stopDrag()
  draggingKey.value = key
  pointerId = event.pointerId
  event.currentTarget.focus()
  document.addEventListener('pointermove', moveDrag, { passive: false })
  document.addEventListener('pointerup', endDrag)
  document.addEventListener('pointercancel', endDrag)
  window.addEventListener('blur', stopDrag)
}

const close = () => {
  stopDrag()
  emit('update:visible', false)
}

const apply = () => {
  stopDrag()
  emit('apply', draftColumns.value.map(column => column.key), draftHiddenKeys.value.slice())
  emit('update:visible', false)
}

const resetDraft = () => {
  stopDrag()
  draftColumns.value = normalizeColumnOrder(props.defaultColumns)
  draftHiddenKeys.value = []
}

const canToggleVisibility = column => column.hideable !== false &&
  (draftHiddenKeys.value.includes(column.key) || draftColumns.value.length - draftHiddenKeys.value.length > 1)

const visibilityTitle = column => {
  if (column.hideable === false) return '此列必须显示'
  if (!canToggleVisibility(column)) return '至少保留一列显示'
  return `${draftHiddenKeys.value.includes(column.key) ? '显示' : '隐藏'}${column.label}列`
}

const toggleVisibility = key => {
  const column = draftColumns.value.find(item => item.key === key)
  if (!column || !canToggleVisibility(column)) return
  stopDrag()
  draftHiddenKeys.value = draftHiddenKeys.value.includes(key)
    ? draftHiddenKeys.value.filter(item => item !== key)
    : [...draftHiddenKeys.value, key]
}

const loadDraft = () => {
  draftColumns.value = [...props.columns]
  draftHiddenKeys.value = normalizeHiddenColumnKeys(props.columns, props.hiddenKeys)
}

const trapFocus = event => {
  const buttons = Array.from(dialog.value?.querySelectorAll('button:not(:disabled)') || [])
  const first = buttons[0]
  const last = buttons.at(-1)
  if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.value)) {
    event.preventDefault()
    last?.focus()
  } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog.value)) {
    event.preventDefault()
    first?.focus()
  }
}

watch(() => props.visible, async visible => {
  stopDrag()
  if (visible) {
    previousFocus = document.activeElement
    loadDraft()
    await nextTick()
    if (props.visible) dialog.value?.focus()
  } else if (previousFocus?.isConnected) {
    previousFocus.focus()
    previousFocus = null
  }
}, { immediate: true })

watch([() => props.columns, () => props.hiddenKeys], () => {
  if (!props.visible) return
  stopDrag()
  loadDraft()
})

onBeforeUnmount(stopDrag)
</script>

<style scoped>
.column-order-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147482100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: #172033;
  background: rgba(15, 23, 42, 0.42);
  font-size: 13px;
}

.column-order-dialog {
  display: flex;
  width: min(540px, 100%);
  max-height: calc(100dvh - 32px);
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.2);
  outline: none;
}

.column-order-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid #e2e8f0;
}

.column-order-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
}

.column-order-list {
  min-height: 0;
  margin: 0;
  padding: 10px 14px;
  overflow-y: auto;
  overscroll-behavior: contain;
  list-style: none;
}

.column-order-row {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 10px;
  padding: 4px 6px;
  border-bottom: 1px solid #edf1f5;
  user-select: none;
}

.column-order-row:last-child {
  border-bottom: 0;
}

.column-order-row.is-dragging {
  background: #e9f8f3;
  box-shadow: inset 3px 0 #0f9f78;
}

.column-order-row.is-fixed {
  color: #8a96a8;
  background: #f8fafc;
}

.column-order-row.is-hidden .column-order-label {
  color: #8a96a8;
}

.column-order-icon,
.column-order-lock {
  display: inline-flex;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #68758a;
  background: transparent;
  border: 0;
  border-radius: 4px;
}

.column-order-icon {
  cursor: pointer;
}

.column-order-icon:hover:not(:disabled) {
  color: #08745a;
  background: #e9f8f3;
}

.column-order-icon:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.column-order-grip {
  cursor: grab;
  touch-action: none;
}

.is-dragging .column-order-grip {
  cursor: grabbing;
}

.column-order-icon svg,
.column-order-lock svg,
.column-order-button svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.column-order-index {
  min-width: 20px;
  color: #8a96a8;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.column-order-label {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.column-order-fixed-label {
  color: #8a96a8;
  font-size: 11px;
}

.column-order-row-actions {
  display: flex;
  flex-shrink: 0;
  gap: 2px;
}

.column-order-visibility {
  display: flex;
  flex: 0 0 72px;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.column-order-visibility-label {
  color: #68758a;
  font-size: 11px;
}

.column-order-switch {
  display: inline-flex;
  width: 32px;
  height: 18px;
  flex: 0 0 32px;
  align-items: center;
  padding: 2px;
  border: 0;
  border-radius: 9px;
  background: #a6b0bd;
  cursor: pointer;
}

.column-order-switch span {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.15s;
}

.column-order-switch[aria-checked="true"] {
  background: #0f9f78;
}

.column-order-switch[aria-checked="true"] span {
  transform: translateX(14px);
}

.column-order-switch:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.column-order-footer {
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 8px;
  padding: 14px 18px;
  border-top: 1px solid #e2e8f0;
}

.column-order-button {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  color: #596579;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.column-order-button:hover {
  color: #08745a;
  background: #e9f8f3;
  border-color: #a9e5d2;
}

.column-order-reset {
  margin-right: auto;
}

.column-order-apply {
  color: #fff;
  background: #0f9f78;
  border-color: #0f9f78;
}

.column-order-apply:hover {
  color: #fff;
  background: #08745a;
  border-color: #08745a;
}

.column-order-dialog button:focus-visible {
  outline: 2px solid #0f9f78;
  outline-offset: 2px;
}

@media (max-width: 420px) {
  .column-order-list { padding: 8px; }
  .column-order-row { gap: 5px; padding: 4px 0; }
  .column-order-visibility-label { display: none; }
  .column-order-visibility { flex-basis: 32px; }
}
</style>
