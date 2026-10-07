import { defineStore } from 'pinia'

const STORAGE_KEY = 'admin_business_document_drafts'
const TYPES = ['sale-return', 'purchase', 'purchase-order', 'purchase-return']

function readDrafts() {
  try {
    const data = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}')
    return Object.fromEntries(TYPES.map(type => [type, data?.[type]?.path ? data[type] : null]))
  } catch {
    return Object.fromEntries(TYPES.map(type => [type, null]))
  }
}

export const useDocumentDraftStore = defineStore('documentDraft', {
  state: () => ({ drafts: readDrafts() }),
  actions: {
    persist() {
      try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(this.drafts)) } catch (error) {
        console.warn('保存单据草稿失败:', error)
      }
    },
    saveDraft(type, draft) {
      if (!TYPES.includes(type)) return
      this.drafts[type] = { ...draft, updatedAt: Date.now() }
      this.persist()
    },
    clearDraft(type) {
      if (!TYPES.includes(type)) return
      this.drafts[type] = null
      this.persist()
    }
  }
})
