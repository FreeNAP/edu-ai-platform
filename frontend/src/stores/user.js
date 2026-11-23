import { defineStore } from 'pinia'
import * as authApi from '../api/auth'
import { getNotifications } from '../api/notification'

function loadUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: loadUser(),
    unreadCount: 0
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin',
    displayName: (s) => s.user?.nickname || s.user?.username || ''
  },
  actions: {
    setAuth(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    async login(data) {
      const res = await authApi.login(data)
      this.setAuth(res.token, res.user)
      return res.user
    },
    async register(data) {
      const res = await authApi.register(data)
      this.setAuth(res.token, res.user)
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
    async refreshUnread() {
      if (!this.token) return
      try {
        const res = await getNotifications()
        this.unreadCount = res?.unread_count ?? 0
      } catch {
        // 通知为加分项，接口未就绪时静默处理
      }
    },
    logout() {
      this.token = ''
      this.user = null
      this.unreadCount = 0
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
