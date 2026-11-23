import axios from 'axios'

// 统一 axios 实例：baseURL=/api，自动带 token，统一解包 {code:0,data}
const request = axios.create({
  baseURL: '/api',
  timeout: 60000 // AI 接口后端最长 30s，留足余量
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function pickMessage(data, fallback) {
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    // FastAPI 校验错误格式 [{loc, msg, type}]
    return data.detail.map((d) => d.msg || JSON.stringify(d)).join('；')
  }
  if (data.detail) return String(data.detail)
  if (data.message) return data.message
  if (data.msg) return data.msg
  return fallback
}

request.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      return Promise.reject(new Error(pickMessage(body, '请求失败')))
    }
    return body
  },
  (err) => {
    const res = err.response
    let msg = err.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络错误，请检查后端服务'
    if (res) {
      msg = pickMessage(res.data, `请求失败（${res.status}）`)
      const url = err.config?.url || ''
      // 登录/注册等认证接口的 401 直接抛错，不强制跳转
      if (res.status === 401 && !url.includes('/auth/')) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        if (window.location.pathname !== '/login') {
          const redirect = encodeURIComponent(window.location.pathname + window.location.search)
          window.location.href = `/login?redirect=${redirect}`
        }
        msg = '登录已过期，请重新登录'
      }
    }
    return Promise.reject(new Error(msg))
  }
)

export default request
