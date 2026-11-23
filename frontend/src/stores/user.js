import { defineStore } from 'pinia'
import * as authApi from '../api/auth'
import { getNotifications } from '../api/notification'
import { clearSession, getToken, saveSession } from '../api/session'

function loadUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    user: loadUser(),
    unreadCount: 0,
    config: { demo_mode: false, password_min_length: 8, smtp_enabled: false, ai_daily_quota: 0 }
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin',
    isTeacher: (s) => ['teacher', 'admin'].includes(s.user?.role),
    displayName: (s) => s.user?.nickname || s.user?.username || ''
  },
  actions: {
    setAuth(data) {
      saveSession(data)
      this.token = data.token
      this.user = data.user
    },
    async loadConfig() {
      try {
        this.config = { ...this.config, ...(await authApi.getPublicConfig()) }
      } catch {
        /* 使用默认配置 */
      }
      return this.config
    },
    async login(data) {
      const res = await authApi.login(data)
      this.setAuth(res)
      return res.user
    },
    async register(data) {
      const res = await authApi.register(data)
      this.setAuth(res)
      return res.user
    },
    async fetchMe() {
      const u = await authApi.getMe()
      this.user = u
      localStorage.setItem('user', JSON.stringify(u))
      return u
    },
    async updateProfile(data) {
      const u = await authApi.updateProfile(data)
      this.user = u
      localStorage.setItem('user', JSON.stringify(u))
      return u
    },
    async changePassword(data) {
      const res = await authApi.updatePassword(data)
      this.setAuth(res)
      return res
    },
    async logoutAll() {
      await authApi.logoutAll()
      this.logout()
    },
    async refreshUnread() {
      if (!this.token) return
      try {
        const res = await getNotifications()
        this.unreadCount = res?.unread_count ?? 0
      } catch {
        /* 静默 */
      }
    },
    logout() {
      this.token = ''
      this.user = null
      this.unreadCount = 0
      clearSession()
    }
  }
})
