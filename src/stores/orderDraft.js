import { defineStore } from 'pinia'

const STORAGE_KEY = 'admin_order_form_draft'

function readStoredDraft() {
  if (typeof sessionStorage === 'undefined') {
    return null
  }

  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch (error) {
    console.warn('读取订单草稿失败:', error)
    return null
  }
}

function writeStoredDraft(draft) {
  if (typeof sessionStorage === 'undefined') {
    return
  }

  try {
    if (draft) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft))
    } else {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  } catch (error) {
    console.warn('保存订单草稿失败:', error)
  }
}

export const useOrderDraftStore = defineStore('orderDraft', {
  state: () => ({
    draft: readStoredDraft()
  }),

  getters: {
    hasDraft: (state) => Boolean(state.draft),
    draftLocation: (state) => {
      if (!state.draft?.route) {
        return null
      }

      return {
        name: state.draft.route.name,
        params: { ...(state.draft.route.params || {}) },
        query: { ...(state.draft.route.query || {}) }
      }
    },
    draftTitle: (state) => {
      if (!state.draft) return ''
      return state.draft.mode === 'edit' ? '修改订单' : '新增订单'
    }
  },

  actions: {
    saveDraft(draft) {
      this.draft = {
        ...draft,
        updatedAt: Date.now()
      }
      writeStoredDraft(this.draft)
    },

    clearDraft() {
      this.draft = null
      writeStoredDraft(null)
    }
  }
})
