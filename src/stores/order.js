import { defineStore } from 'pinia'

export const useOrderStore = defineStore('order', {
  state: () => ({
    allOrders: [],
    currentTab: 0,
    nomiActiveFilterStart: null,
    nomiActiveFilterEnd: null,
    nomiMaterialFilterStart: null,
    nomiMaterialFilterEnd: null
  }),

  getters: {
    pendingOrders: (state) => {
      return state.allOrders.filter(order => order.status === 'pending')
    },

    completedOrders: (state) => {
      return state.allOrders.filter(order => order.status === 'completed')
    },

    shippedOrders: (state) => {
      return state.allOrders.filter(order => order.status === 'shipped')
    },

    currentOrders: (state) => {
      if (state.currentTab === 0) return state.allOrders.filter(o => o.status === 'pending')
      if (state.currentTab === 1) return state.allOrders.filter(o => o.status === 'completed')
      if (state.currentTab === 2) return state.allOrders.filter(o => o.status === 'shipped')
      return []
    }
  },

  actions: {
    setOrders(orders) {
      this.allOrders = orders
    },

    addOrder(order) {
      this.allOrders.unshift(order)
    },

    updateOrder(orderId, updates) {
      const index = this.allOrders.findIndex(o => o.id === orderId)
      if (index !== -1) {
        this.allOrders[index] = { ...this.allOrders[index], ...updates }
      }
    },

    deleteOrder(orderId) {
      const index = this.allOrders.findIndex(o => o.id === orderId)
      if (index !== -1) {
        this.allOrders.splice(index, 1)
      }
    },

    setCurrentTab(tabIndex) {
      this.currentTab = tabIndex
    },

    setDateFilter(start, end) {
      this.nomiActiveFilterStart = start
      this.nomiActiveFilterEnd = end
    },

    clearDateFilter() {
      this.nomiActiveFilterStart = null
      this.nomiActiveFilterEnd = null
    },

    setMaterialDateFilter(start, end) {
      this.nomiMaterialFilterStart = start
      this.nomiMaterialFilterEnd = end
    },

    clearMaterialDateFilter() {
      this.nomiMaterialFilterStart = null
      this.nomiMaterialFilterEnd = null
    }
  }
})
