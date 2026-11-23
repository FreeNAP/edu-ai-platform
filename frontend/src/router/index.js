import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/auth/AuthView.vue'),
    meta: { public: true, authMode: 'login' }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/auth/AuthView.vue'),
    meta: { public: true, authMode: 'register' }
  },
  {
    path: '/reset',
    name: 'reset',
    component: () => import('../views/auth/AuthView.vue'),
    meta: { public: true, authMode: 'reset' }
  },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/courses/theory',
    children: [
      {
        path: 'courses/:category',
        name: 'courses',
        component: () => import('../views/course/CourseList.vue'),
        meta: { title: '课程中心' }
      },
      {
        path: 'course/:id',
        name: 'course-detail',
        component: () => import('../views/course/CourseDetail.vue'),
        meta: { title: '课程详情' }
      },
      {
        path: 'learn/:courseId',
        name: 'learn',
        component: () => import('../views/course/LearnPage.vue'),
        meta: { title: '课程学习' }
      },
      {
        path: 'jobs',
        name: 'jobs',
        component: () => import('../views/job/JobList.vue'),
        meta: { title: '实习就业' }
      },
      {
        path: 'job/:id',
        name: 'job-detail',
        component: () => import('../views/job/JobDetail.vue'),
        meta: { title: '职位详情' }
      },
      {
        path: 'interview/:id',
        name: 'interview',
        component: () => import('../views/job/InterviewPage.vue'),
        meta: { title: 'AI 面试' }
      },
      {
        path: 'quiz/:id',
        name: 'quiz',
        component: () => import('../views/quiz/QuizPage.vue'),
        meta: { title: '测验' }
      },
      {
        path: 'teacher',
        name: 'teacher',
        component: () => import('../views/teacher/TeacherConsole.vue'),
        meta: { title: '教师工作台', teacher: true }
      },
      {
        path: 'ai',
        name: 'ai',
        component: () => import('../views/ai/AiAssistant.vue'),
        meta: { title: 'AI 学习助手' }
      },
      {
        path: 'me',
        name: 'me',
        component: () => import('../views/me/ProfileView.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('../views/notification/NotificationView.vue'),
        meta: { title: '通知中心' }
      },
      {
        path: 'community',
        name: 'community',
        component: () => import('../views/community/CommunityList.vue'),
        meta: { title: '问答社区' }
      },
      {
        path: 'community/:id',
        name: 'question-detail',
        component: () => import('../views/community/QuestionDetail.vue'),
        meta: { title: '问题详情' }
      },
      {
        path: 'admin',
        component: () => import('../views/admin/AdminLayout.vue'),
        meta: { admin: true },
        redirect: '/admin/dashboard',
        children: [
          { path: 'dashboard', name: 'admin-dashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { title: '数据看板' } },
          { path: 'users', name: 'admin-users', component: () => import('../views/admin/AdminUsers.vue'), meta: { title: '用户管理' } },
          { path: 'courses', name: 'admin-courses', component: () => import('../views/admin/AdminCourses.vue'), meta: { title: '课程管理' } },
          { path: 'lecturers', name: 'admin-lecturers', component: () => import('../views/admin/AdminLecturers.vue'), meta: { title: '讲师管理' } },
          { path: 'jobs', name: 'admin-jobs', component: () => import('../views/admin/AdminJobs.vue'), meta: { title: '职位管理' } },
          { path: 'orders', name: 'admin-orders', component: () => import('../views/admin/AdminOrders.vue'), meta: { title: '订单管理' } },
          { path: 'applications', name: 'admin-applications', component: () => import('../views/admin/AdminApplications.vue'), meta: { title: '申请管理' } },
          { path: 'audit', name: 'admin-audit', component: () => import('../views/admin/AdminAudit.vue'), meta: { title: '操作日志' } },
          { path: 'community', name: 'admin-community', component: () => import('../views/admin/AdminCommunity.vue'), meta: { title: '社区管理' } }
        ]
      }
    ]
  },
  {
    path: '/certificate/:no',
    name: 'certificate',
    component: () => import('../views/quiz/CertificatePage.vue'),
    meta: { public: true, title: '证书查验' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFound.vue'),
    meta: { public: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  // 未登录访问非白名单页 → 登录
  if (!to.meta.public && !token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  // 已登录访问登录/注册页 → 首页
  if ((to.name === 'login' || to.name === 'register') && token) {
    return { path: '/' }
  }
  // 教师工作台：教师或管理员
  if (to.matched.some((r) => r.meta.teacher)) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || 'null')
      if (!['teacher', 'admin'].includes(user?.role)) return { path: '/' }
    } catch {
      return { path: '/' }
    }
  }
  // admin 页面校验角色
  if (to.matched.some((r) => r.meta.admin)) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || 'null')
      if (user?.role !== 'admin') return { path: '/' }
    } catch {
      return { path: '/' }
    }
  }
  return true
})

router.afterEach((to) => {
  const base = '智慧教育平台'
  document.title = to.meta.title ? `${to.meta.title} - ${base}` : base
})

export default router
