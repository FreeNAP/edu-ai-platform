import request from './index'

// 课程
export const getCourses = (params) => request.get('/courses', { params })
export const getCourseFilters = () => request.get('/courses/meta/filters')
export const getCourseDetail = (id) => request.get(`/courses/${id}`)
export const toggleCourseFavorite = (id) => request.post(`/courses/${id}/favorite`)
export const enrollCourse = (id) => request.post(`/courses/${id}/enroll`)
export const getCourseComments = (id) => request.get(`/courses/${id}/comments`)
export const postCourseComment = (id, data) => request.post(`/courses/${id}/comments`, data)
export const completeLesson = (id, studySeconds) =>
  request.post(`/lessons/${id}/complete`, { study_seconds: studySeconds })
export const getMyEnrollments = () => request.get('/users/me/enrollments')
export const getMyFavorites = () => request.get('/users/me/favorites')
