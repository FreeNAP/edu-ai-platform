import request from './index'

// 实习就业
export const getJobs = (params) => request.get('/jobs', { params })
export const getJobFilters = () => request.get('/jobs/meta/filters')
export const getJobDetail = (id) => request.get(`/jobs/${id}`)
export const toggleJobFavorite = (id) => request.post(`/jobs/${id}/favorite`)
export const applyJob = (id, message) => request.post(`/jobs/${id}/apply`, { message })
export const getMyApplications = () => request.get('/users/me/applications')
export const createInterview = (id, message) => request.post(`/jobs/${id}/ai-interview`, { message })
