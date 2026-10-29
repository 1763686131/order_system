import { defineStore } from 'pinia'

const STORAGE_KEY = 'admin_order_list_selections'
const selectionKey = (mode, accountId) => `${accountId ?? 'guest'}:${mode}`
const normalizeIds = ids => [...new Set(
  Array.isArray(ids) ? ids.filter(id => Number.isSafeInteger(id) && id > 0) : []
)]

function readStoredSelections() {
  try {
    if (typeof sessionStorage === 'undefined') return {}
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}')
    if (!saved || typeof saved !== 'object' || Array.isArray(saved)) return {}
    return Object.fromEntries(Object.entries(saved).map(([key, ids]) => [key, normalizeIds(ids)]))
  } catch {
    return {}
  }
}

export const useOrderSelectionStore = defineStore('orderSelection', {
  state: () => ({
    selections: readStoredSelections()
  }),

  getters: {
    selectedIdsFor: state => (mode, accountId) =>
      state.selections[selectionKey(mode, accountId)] || []
  },

  actions: {
    setSelectedIds(mode, accountId, ids) {
      const key = selectionKey(mode, accountId)
      const selected = normalizeIds(ids)
      if (selected.length) this.selections[key] = selected
      else delete this.selections[key]

      try {
        if (typeof sessionStorage === 'undefined') return
        if (Object.keys(this.selections).length) {
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify(this.selections))
        } else {
          sessionStorage.removeItem(STORAGE_KEY)
        }
      } catch {
        // Keep the in-memory selection when browser storage is unavailable.
      }
    }
  }
})
