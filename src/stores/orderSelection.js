import { defineStore } from 'pinia'

const selectionKey = (mode, accountId) => `${accountId ?? 'guest'}:${mode}`
const normalizeIds = ids => [...new Set(
  Array.isArray(ids) ? ids.filter(id => Number.isSafeInteger(id) && id > 0) : []
)]

export const useOrderSelectionStore = defineStore('orderSelection', {
  state: () => ({
    selections: {}
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
    }
  }
})
