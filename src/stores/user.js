import { defineStore } from 'pinia'
import request from '@/api/request'
import { hasPermission, normalizeAccessState } from '@/utils/accessControl'

const DEVICE_ID_KEY = 'order_system_device_id'

const getBrowserName = () => {
  const userAgent = navigator.userAgent || ''
  if (userAgent.includes('Edg/')) return 'Edge'
  if (userAgent.includes('Chrome/')) return 'Chrome'
  if (userAgent.includes('Firefox/')) return 'Firefox'
  if (userAgent.includes('Safari/')) return 'Safari'
  return '浏览器'
}

const getDeviceIdentity = () => {
  let deviceId = ''
  try {
    deviceId = localStorage.getItem(DEVICE_ID_KEY) || ''
    if (!deviceId) {
      deviceId = globalThis.crypto?.randomUUID?.()
        || `device-${Date.now()}-${Math.random().toString(16).slice(2)}`
      localStorage.setItem(DEVICE_ID_KEY, deviceId)
    }
  } catch {
    deviceId = `device-${Date.now()}`
  }

  const platform = navigator.userAgentData?.platform || navigator.platform || '新设备'
  return {
    id: deviceId,
    name: `${platform} · ${getBrowserName()}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || ''
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    id: null,
    username: '',
    name: '',
    avatarUrl: '',
    phone: '',
    position: '',
    role: '',
    roles: [],
    permissions: [],
    isSuperAdmin: false,
    canAccessAdmin: false,
    longSession: false,
    allStores: false,
    allWarehouses: false,
    storeIds: [],
    warehouseIds: [],
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
      return (permissionCode) => hasPermission(state, permissionCode)
    }
  },

  actions: {
    setUser(userData = {}) {
      const accessState = normalizeAccessState(userData)
      this.id = userData.id || null
      this.username = userData.username || ''
      this.name = userData.displayName || userData.name || ''
      this.avatarUrl = userData.avatarUrl || ''
      this.phone = userData.phone || ''
      this.position = userData.position || ''
      this.role = userData.role || ''
      this.roles = Array.isArray(userData.roles) ? userData.roles : []
      this.permissions = accessState.permissions
      this.isSuperAdmin = accessState.isSuperAdmin
      this.canAccessAdmin = accessState.canAccessAdmin
      this.longSession = accessState.longSession
      this.allStores = accessState.allStores
      this.allWarehouses = accessState.allWarehouses
      this.storeIds = accessState.storeIds
      this.warehouseIds = accessState.warehouseIds
      this.mustChangePassword = Boolean(userData.mustChangePassword)
      this.authChecked = true
    },

    clearUser() {
      this.id = null
      this.username = ''
      this.name = ''
      this.avatarUrl = ''
      this.phone = ''
      this.position = ''
      this.role = ''
      this.roles = []
      this.permissions = []
      this.isSuperAdmin = false
      this.canAccessAdmin = false
      this.longSession = false
      this.allStores = false
      this.allWarehouses = false
      this.storeIds = []
      this.warehouseIds = []
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
      const response = await request.post('/auth/login', {
        username,
        password,
        device: getDeviceIdentity()
      })
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
