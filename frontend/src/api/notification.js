import request from './index'

// 通知
export const getNotifications = () => request.get('/notifications')
export const markNotificationRead = (id) => request.post(`/notifications/${id}/read`)
export const markAllNotificationsRead = () => request.post('/notifications/read-all')
