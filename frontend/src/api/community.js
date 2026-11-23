import request from './index'

// 社区问答
export const getQuestions = (params) => request.get('/community/questions', { params })
export const postQuestion = (data) => request.post('/community/questions', data)
export const getQuestionDetail = (id) => request.get(`/community/questions/${id}`)
export const postAnswer = (id, content) =>
  request.post(`/community/questions/${id}/answers`, { content })
export const deleteQuestion = (id) => request.delete(`/community/questions/${id}`)
export const deleteAnswer = (id) => request.delete(`/community/answers/${id}`)
