import request from './index'

// 测验、考试与证书
export const getCourseQuizzes = (courseId) => request.get(`/courses/${courseId}/quizzes`)
export const getQuiz = (id) => request.get(`/quizzes/${id}`)
export const submitQuiz = (id, answers) => request.post(`/quizzes/${id}/submit`, { answers })
export const getMyCertificates = () => request.get('/users/me/certificates')
export const verifyCertificate = (no) => request.get(`/certificates/${encodeURIComponent(no)}`)
