import request from './index'

// 后台管理（仅 admin）
export const getAdminStats = () => request.get('/admin/stats')

export const adminGetUsers = (params) => request.get('/admin/users', { params })
export const adminUpdateUser = (id, data) => request.put(`/admin/users/${id}`, data)
export const adminDeleteUser = (id) => request.delete(`/admin/users/${id}`)

export const adminGetCourses = (params) => request.get('/admin/courses', { params })
export const adminCreateCourse = (data) => request.post('/admin/courses', data)
export const adminUpdateCourse = (id, data) => request.put(`/admin/courses/${id}`, data)
export const adminDeleteCourse = (id) => request.delete(`/admin/courses/${id}`)

export const adminGetLecturers = (params) => request.get('/admin/lecturers', { params })
export const adminCreateLecturer = (data) => request.post('/admin/lecturers', data)
export const adminUpdateLecturer = (id, data) => request.put(`/admin/lecturers/${id}`, data)
export const adminDeleteLecturer = (id) => request.delete(`/admin/lecturers/${id}`)

export const adminGetJobs = (params) => request.get('/admin/jobs', { params })
export const adminCreateJob = (data) => request.post('/admin/jobs', data)
export const adminUpdateJob = (id, data) => request.put(`/admin/jobs/${id}`, data)
export const adminDeleteJob = (id) => request.delete(`/admin/jobs/${id}`)

export const adminGetOrders = (params) => request.get('/admin/orders', { params })
export const adminUpdateOrder = (id, data) => request.put(`/admin/orders/${id}`, data)

export const adminGetApplications = (params) => request.get('/admin/applications', { params })
export const adminUpdateApplication = (id, data) => request.put(`/admin/applications/${id}`, data)

export const adminCreateUser = (data) => request.post('/admin/users', data)
export const adminGetOutline = (id) => request.get(`/admin/courses/${id}/outline`)
export const adminSaveOutline = (id, chapters) => request.put(`/admin/courses/${id}/outline`, chapters)
export const adminGetQuestions = (params) => request.get('/admin/questions', { params })
export const adminDeleteQuestion = (id) => request.delete(`/admin/questions/${id}`)
