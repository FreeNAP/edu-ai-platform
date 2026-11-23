import request from './index'

// AI 学习助手
export const aiChat = (data) => request.post('/ai/chat', data)
export const getChatSessions = () => request.get('/ai/chat/sessions')
export const getChatSession = (id) => request.get(`/ai/chat/sessions/${id}`)
export const deleteChatSession = (id) => request.delete(`/ai/chat/sessions/${id}`)
export const getLearningPath = (data) => request.post('/ai/learning-path', data)
export const gradeCode = (data) => request.post('/ai/grade', data)
export const getReport = (period) => request.get('/ai/report', { params: { period } })
export const submitInterviewAnswers = (id, answers) =>
  request.post(`/ai/interview/${id}/answer`, { answers })
export const getInterview = (id) => request.get(`/ai/interview/${id}`)
export const getMyInterviews = () => request.get('/users/me/interviews')
export const getLearningPlans = () => request.get('/ai/learning-plans')
export const deleteLearningPlan = (id) => request.delete(`/ai/learning-plans/${id}`)
