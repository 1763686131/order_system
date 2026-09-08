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
    draftPath: (state) => {
      if (!state.draft) {
        return ''
      }

      if (state.draft.path) {
        return state.draft.path
      }

      if (state.draft.mode === 'edit' && state.draft.orderId) {
        return `/admin/orders/edit/${state.draft.orderId}`
      }

      const copyFrom = state.draft.route?.query?.copyFrom
      return copyFrom
        ? `/admin/orders/create?copyFrom=${encodeURIComponent(copyFrom)}`
        : '/admin/orders/create'
    },
    draftTitle: (state) => {
      if (!state.draft) return ''
      return state.draft.mode === 'edit' ? '修改订单' : '新增订单'
    },
    draftMark: (state) => {
      if (!state.draft) return ''
      return state.draft.mode === 'edit' ? '改' : '新'
    },
    draftShortLabel: (state) => {
      if (!state.draft) return ''
      return state.draft.mode === 'edit' ? '修改单' : '新增单'
    },
    draftMode: (state) => {
      return state.draft?.mode || 'create'
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
