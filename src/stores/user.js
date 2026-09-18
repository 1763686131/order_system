import { defineStore } from 'pinia'
import request from '@/api/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    id: null,
    username: '',
    name: '',
    avatarUrl: '',
    role: '',
    roles: [],
    permissions: [],
    isSuperAdmin: false,
    canAccessAdmin: false,
    mustChangePassword: false,
    authChecked: false
  }),

  getters: {
    isLoggedIn: (state) => Boolean(state.id && state.username),
    getRoleName: (state) => {
      if (state.isSuperAdmin) return '超级管理员'
      return state.roles.map(role => role.name).join('、') || '普通账号'
    },
    hasPerm: (state) => {
      return (permissionCode) => (
        state.isSuperAdmin || state.permissions.includes(permissionCode)
      )
    }
  },

  actions: {
    setUser(userData = {}) {
      this.id = userData.id || null
      this.username = userData.username || ''
      this.name = userData.displayName || userData.name || ''
      this.avatarUrl = userData.avatarUrl || ''
      this.role = userData.role || ''
      this.roles = Array.isArray(userData.roles) ? userData.roles : []
      this.permissions = Array.isArray(userData.permissions)
        ? userData.permissions
        : []
      this.isSuperAdmin = Boolean(userData.isSuperAdmin)
      this.canAccessAdmin = Boolean(userData.canAccessAdmin)
      this.mustChangePassword = Boolean(userData.mustChangePassword)
      this.authChecked = true
    },

    clearUser() {
      this.id = null
      this.username = ''
      this.name = ''
      this.avatarUrl = ''
      this.role = ''
      this.roles = []
      this.permissions = []
      this.isSuperAdmin = false
      this.canAccessAdmin = false
      this.mustChangePassword = false
      localStorage.removeItem('local_user')
    },

    async restoreSession(force = false) {
      if (this.authChecked && !force) return this.isLoggedIn
      try {
        const response = await request.get('/auth/me')
        if (response.success && response.user) {
          this.setUser(response.user)
          return true
        }
      } catch (error) {
        if (error?.response?.status !== 401) {
          console.error('Failed to restore session:', error)
        }
      }
      this.clearUser()
      this.authChecked = true
      return false
    },

    async login(username, password) {
      const response = await request.post('/auth/login', { username, password })
      if (response.success && response.user) this.setUser(response.user)
      return response
    },

    async logout() {
      this.clearUser()
      this.authChecked = true
      try {
        await request.post('/auth/logout')
      } catch (error) {
        console.error('Logout request failed:', error)
      }
    }
  }
})
