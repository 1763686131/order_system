import { nextTick, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDocumentDraftStore } from '@/stores/documentDraft'

export function captureDocumentViewport() {
  const form = document.querySelector('.business-document-form')
  const inputs = Array.from(form?.querySelectorAll('input, select, textarea') || [])
  return {
    scrollTop: document.querySelector('.main-content')?.scrollTop || 0,
    tableScrollLeft: form?.querySelector('.products-table-wrapper')?.scrollLeft || 0,
    activeFieldIndex: inputs.indexOf(document.activeElement)
  }
}

export async function restoreDocumentViewport(viewport) {
  if (!viewport) return
  await nextTick()
  const main = document.querySelector('.main-content')
  const form = document.querySelector('.business-document-form')
  if (main) main.scrollTop = viewport.scrollTop || 0
  const table = form?.querySelector('.products-table-wrapper')
  if (table) table.scrollLeft = viewport.tableScrollLeft || 0
  const input = form?.querySelectorAll('input, select, textarea')[viewport.activeFieldIndex]
  input?.focus({ preventScroll: true })
}

export function useDocumentDraft(props, ui) {
  const route = useRoute()
  const store = useDocumentDraftStore()
  const type = props.documentType
  const path = route.fullPath
  let ready = false
  let timer
  const persistDraft = () => {
    if (!ready || ui.loading || ui.loadFailed || ui.readOnly) return
    const form = JSON.parse(JSON.stringify(ui.form))
    form.items.forEach(item => { item.showDropdown = false; item.filteredProducts = [] })
    store.saveDraft(type, {
      path, action: props.action, documentId: props.documentId, form,
      savedDocumentId: ui.savedDocumentId ?? ui.savedReturnId,
      viewport: captureDocumentViewport()
    })
  }
  const discardDraft = () => {
    ready = false
    clearTimeout(timer)
    store.clearDraft(type)
  }
  watch(() => ui.loading, async loading => {
    if (loading || ui.loadFailed || ui.readOnly) return
    const saved = store.drafts[type]
    if (saved?.path === path) {
      if (ui.restoreDraft) ui.restoreDraft(saved)
      else {
        ui.form = JSON.parse(JSON.stringify(saved.form))
        if (type === 'purchase') ui.savedDocumentId = saved.savedDocumentId ?? props.documentId
        else ui.savedReturnId = saved.savedDocumentId ?? props.documentId
      }
      await restoreDocumentViewport(saved.viewport)
    }
    ready = true
    persistDraft()
  }, { immediate: true })
  watch(() => ui.form, () => {
    if (!ready) return
    clearTimeout(timer)
    timer = setTimeout(persistDraft, 120)
  }, { deep: true })
  onBeforeUnmount(() => {
    clearTimeout(timer)
    persistDraft()
    ready = false
  })
  return { discardDraft }
}
