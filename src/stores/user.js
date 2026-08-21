import { defineStore } from 'pinia'
import request from '@/api/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    username: '',
    name: '',
    role: '',
    permissions: []
  }),

  getters: {
    isLoggedIn: (state) => !!state.username,

    getRoleName: (state) => {
      const roleMap = {
        'super_admin': '超级管理员',
        'admin': '管理员',
        'employee': '员工',
        'operator': '员工'
      }
      return roleMap[state.role] || state.role
    },

    hasPerm: (state) => {
      return (permKey) => {
        if (state.role === 'super_admin') return true
        return state.permissions && state.permissions.includes(permKey)
      }
    }
  },

  actions: {
    setUser(userData) {
      this.username = userData.username || ''
      this.name = userData.name || ''
      this.role = userData.role || ''
      this.permissions = userData.permissions || []

      // 持久化到 localStorage
      localStorage.setItem('local_user', JSON.stringify({
        username: this.username,
        name: this.name,
        role: this.role,
        permissions: this.permissions
      }))
    },

    logout() {
      this.username = ''
      this.name = ''
      this.role = ''
      this.permissions = []
      localStorage.removeItem('local_user')
    },

    // API 请求方法
    async login(username, password) {
      try {
        const response = await request({
          url: '/login',
          method: 'POST',
          data: { username, password }
        })

        if (response.success) {
          this.setUser(response.user)
        }
        return response
      } catch (error) {
        console.error('Login failed:', error)
        throw error
      }
    },

    async fetchUsers() {
      try {
        const response = await request({ url: '/users', method: 'GET' })
        return Array.isArray(response) ? response : []
      } catch (error) {
        console.error('Failed to fetch users:', error)
        return []
      }
    },

    async createUser(userData) {
      try {
        const response = await request({
          url: '/users',
          method: 'POST',
          data: userData
        })
        return response
      } catch (error) {
        console.error('Failed to create user:', error)
        throw error
      }
    },

    async updateUser(username, updates) {
      try {
        const response = await request({
          url: `/users/${username}`,
          method: 'PUT',
          data: updates
        })
        return response
      } catch (error) {
        console.error('Failed to update user:', error)
        throw error
      }
    },

    async deleteUser(username) {
      try {
        const response = await request({
          url: `/users/${username}`,
          method: 'DELETE'
        })
        return response
      } catch (error) {
        console.error('Failed to delete user:', error)
        throw error
      }
    },

    async updatePassword(username, password) {
      try {
        const response = await request({
          url: `/users/${username}/password`,
          method: 'PUT',
          data: { password }
        })
        return response
      } catch (error) {
        console.error('Failed to update password:', error)
        throw error
      }
    }
  }
})
