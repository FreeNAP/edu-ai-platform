import request from './index'

// 认证与用户
export const register = (data) => request.post('/auth/register', data)
export const login = (data) => request.post('/auth/login', data)
export const forgotPassword = (email) => request.post('/auth/forgot-password', { email })
export const resetPassword = (data) => request.post('/auth/reset-password', data)
export const logoutAll = () => request.post('/auth/logout-all')
export const getPublicConfig = () => request.get('/auth/config')
export const getMe = () => request.get('/auth/me')
export const updateProfile = (data) => request.put('/users/profile', data)
export const updatePassword = (data) => request.put('/users/password', data)
