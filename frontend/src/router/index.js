import { getToken, getUserInfo } from '@/utils/auth'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/manager/home' },
    {
      path: '/manager',
      name: 'Layout',
      component: () => import('@/layouts/Layout.vue'),
      children: [
        { path: 'home', name: 'Home', component: () => import('@/views/Home.vue') },
        // 课程助手：管理员和学生都可以使用
        { path: 'chat', name: 'Chat', component: () => import('@/views/Chat.vue') },
        // 课程页面：管理员可维护，学生只读
        { path: 'course', name: 'Course', component: () => import('@/views/Course.vue') },
        // 课表管理：仅管理员
        {
          path: 'schedule',
          name: 'ScheduleManage',
          component: () => import('@/views/ScheduleManage.vue'),
          meta: { role: 'admin' }
        },
        // 资料管理：仅管理员
        {
          path: 'course-docs',
          name: 'CourseDocs',
          component: () => import('@/views/CourseDocs.vue'),
          meta: { role: 'admin' }
        },
        // 课程课表：学生端查询
        {
          path: 'timetable',
          name: 'Timetable',
          component: () => import('@/views/Timetable.vue'),
          meta: { role: 'student' }
        },
        // 学习计划：学生端
        {
          path: 'study-plan',
          name: 'StudyPlan',
          component: () => import('@/views/StudyPlan.vue'),
          meta: { role: 'student' }
        },
        { path: 'profile', name: 'Profile', component: () => import('@/views/Profile.vue') },
        { path: 'password', name: 'Password', component: () => import('@/views/Password.vue') },
        {
          path: 'user',
          name: 'User',
          component: () => import('@/views/User.vue'),
          meta: { role: 'admin' }
        },
      ]
    },
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
    { path: '/register', name: 'Register', component: () => import('@/views/Register.vue') }
  ]
})

// 路由守卫：除了校验 token，也校验页面要求的角色
router.beforeEach((to) => {
  const token = getToken()

  if (to.path === '/login' || to.path === '/register') {
    return true
  }
  if (!token) {
    return '/login'
  }

  const userInfo = getUserInfo()
  if (to.meta.role && userInfo?.role !== to.meta.role) {
    return '/manager/home'
  }
  return true
})

export default router
