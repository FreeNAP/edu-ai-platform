// 令牌存取：访问令牌 + 刷新令牌 + 用户信息（localStorage）
const KEYS = { token: 'token', refresh: 'refresh_token', user: 'user' }

export function getToken() {
  return localStorage.getItem(KEYS.token) || ''
}

export function getRefreshToken() {
  return localStorage.getItem(KEYS.refresh) || ''
}

export function saveSession({ token, refresh_token: refreshToken, user }) {
  if (token) localStorage.setItem(KEYS.token, token)
  if (refreshToken) localStorage.setItem(KEYS.refresh, refreshToken)
  if (user) localStorage.setItem(KEYS.user, JSON.stringify(user))
}

export function clearSession() {
  Object.values(KEYS).forEach((k) => localStorage.removeItem(k))
}
