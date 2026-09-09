import { defineStore } from 'pinia'

// Stock drafts intentionally live only in Pinia memory. They are not sent to
// the API and disappear when the application process is restarted.
export const useStockDraftStore = defineStore('stockDraft', {
  state: () => ({
    inbound: null
  }),

  getters: {
    hasInboundDraft: state => Boolean(state.inbound)
  },

  actions: {
    saveInboundDraft(draft) {
      this.inbound = JSON.parse(JSON.stringify(draft))
    },

    clearInboundDraft() {
      this.inbound = null
    }
  }
})
