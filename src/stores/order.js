import { defineStore } from 'pinia'
import request from '@/api/request'
import { useUserStore } from './user'

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
    // 基础数据操作
    setOrders(orders) {
      this.allOrders = orders
    },

    applyOrderEvent(event) {
      const action = event?.action
      const order = event?.order
      const orderId = order?.id ?? event?.orderId

      if (action === 'deleted') {
        const deleteIndex = this.allOrders.findIndex(item => item.id === orderId)
        if (deleteIndex !== -1) {
          this.allOrders.splice(deleteIndex, 1)
        }
        return
      }

      if (!order || orderId == null) return

      const orderIndex = this.allOrders.findIndex(item => item.id === orderId)
      if (orderIndex === -1) {
        this.allOrders.unshift(order)
      } else {
        this.allOrders[orderIndex] = order
      }
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
    },

    // API 请求方法
    async fetchOrders() {
      try {
        const response = await request({ url: '/orders', method: 'GET' })
        this.setOrders(response)
        return response
      } catch (error) {
        console.error('Failed to fetch orders:', error)
        throw error
      }
    },

    async createOrder(orderData) {
      try {
        const response = await request({
          url: '/orders',
          method: 'POST',
          data: orderData
        })
        if (response.success) {
          await this.fetchOrders()
        }
        return response
      } catch (error) {
        console.error('Failed to create order:', error)
        throw error
      }
    },

    async updateOrderById(orderId, updates) {
      try {
        const response = await request({
          url: `/orders/${orderId}`,
          method: 'PUT',
          data: updates
        })
        if (response.success || response.ok !== false) {
          await this.fetchOrders()
        }
        return response
      } catch (error) {
        console.error('Failed to update order:', error)
        throw error
      }
    },

    async deleteOrderById(orderId) {
      try {
        const response = await request({
          url: `/orders/${orderId}`,
          method: 'DELETE'
        })
        if (response.success || response.ok !== false) {
          this.deleteOrder(orderId)
        }
        return response
      } catch (error) {
        console.error('Failed to delete order:', error)
        throw error
      }
    },

    async uploadReceipt(orderId, formData) {
      try {
        // 使用原生fetch，因为需要发送FormData
        const userStore = useUserStore()
        const response = await fetch(`/api/orders/${orderId}/upload_receipt`, {
          method: 'POST',
          headers: {
            'Username': String(userStore.username),
            'Role': String(userStore.role)
          },
          body: formData
        })

        if (response.ok) {
          await this.fetchOrders()
          return { success: true }
        } else {
          return { success: false }
        }
      } catch (error) {
        console.error('Failed to upload receipt:', error)
        throw error
      }
    },

    async deleteReceipt(orderId) {
      try {
        const response = await request({
          url: `/orders/${orderId}/receipt`,
          method: 'DELETE'
        })
        if (response.success) {
          await this.fetchOrders()
        }
        return response
      } catch (error) {
        console.error('Failed to delete receipt:', error)
        throw error
      }
    },

    async fetchCarrierTags() {
      try {
        const response = await request({ url: '/carrier_tags', method: 'GET' })
        return Array.isArray(response) ? response : []
      } catch (error) {
        console.error('Failed to fetch carrier tags:', error)
        return []
      }
    },

    async saveCarrierTag(tag) {
      try {
        const response = await request({
          url: '/carrier_tags',
          method: 'POST',
          data: { tag }
        })
        return response
      } catch (error) {
        console.error('Failed to save carrier tag:', error)
        throw error
      }
    }
  }
})
