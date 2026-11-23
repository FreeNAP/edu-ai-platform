import request from './index'

// 教师工作台
export const teacherOverview = () => request.get('/teacher/overview')
export const teacherCourses = () => request.get('/teacher/courses')
export const teacherCreateCourse = (data) => request.post('/teacher/courses', data)
export const teacherUpdateCourse = (id, data) => request.put(`/teacher/courses/${id}`, data)
export const teacherGetOutline = (id) => request.get(`/teacher/courses/${id}/outline`)
export const teacherSaveOutline = (id, chapters) => request.put(`/teacher/courses/${id}/outline`, chapters)
export const teacherStudents = (id) => request.get(`/teacher/courses/${id}/students`)
export const teacherQuizzes = (id) => request.get(`/teacher/courses/${id}/quizzes`)
export const teacherCreateQuiz = (courseId, data) => request.post(`/teacher/courses/${courseId}/quizzes`, data)
export const teacherUpdateQuiz = (id, data) => request.put(`/teacher/quizzes/${id}`, data)
export const teacherDeleteQuiz = (id) => request.delete(`/teacher/quizzes/${id}`)
