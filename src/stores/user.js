import { defineStore } from 'pinia'

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
    }
  }
})
