import axios from 'axios'
import { clearSession, getRefreshToken, getToken, saveSession } from './session'

// 统一 axios 实例：baseURL=/api，自动带令牌，统一解包 {code:0,data}；
// 访问令牌过期时用刷新令牌换新，期间的并发请求排队等待，成功后自动重放。
const request = axios.create({
  baseURL: '/api',
  timeout: 60000
})

request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export function pickMessage(data, fallback) {
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) return data.detail.map((d) => d.msg || JSON.stringify(d)).join('；')
  if (data.detail) return String(data.detail)
  return data.message || data.msg || fallback
}

let refreshing = null

export function refreshSession() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return Promise.reject(new Error('no refresh token'))
  if (!refreshing) {
    refreshing = axios
      .post('/api/auth/refresh', { refresh_token: refreshToken })
      .then((res) => {
        const data = res.data?.data
        if (!data?.token) throw new Error('refresh failed')
        saveSession(data)
        return data.token
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

function redirectToLogin() {
  clearSession()
  if (window.location.pathname !== '/login') {
    const redirect = encodeURIComponent(window.location.pathname + window.location.search)
    window.location.href = `/login?redirect=${redirect}`
  }
}

const NO_REFRESH = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/forgot-password', '/auth/reset-password']

request.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      return Promise.reject(new Error(pickMessage(body, '请求失败')))
    }
    return body
  },
  async (err) => {
    const res = err.response
    const config = err.config || {}
    if (res?.status === 401 && !config._retried && !NO_REFRESH.some((u) => (config.url || '').includes(u))) {
      try {
        const token = await refreshSession()
        config._retried = true
        config.headers = { ...config.headers, Authorization: `Bearer ${token}` }
        return request(config)
      } catch {
        redirectToLogin()
        return Promise.reject(new Error('登录已过期，请重新登录'))
      }
    }
    let msg = err.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络错误，请检查网络或稍后再试'
    if (res) msg = pickMessage(res.data, `请求失败（${res.status}）`)
    const error = new Error(msg)
    error.status = res?.status
    return Promise.reject(error)
  }
)

export default request
