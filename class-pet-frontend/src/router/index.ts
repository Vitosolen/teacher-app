import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
  },
  {
    path: '/classes',
    name: 'classes',
    component: () => import('@/views/ClassesView.vue'),
  },
  {
    path: '/classes/:id',
    name: 'class-detail',
    component: () => import('@/views/ClassDetailView.vue'),
    props: true,
  },
  {
    path: '/classroom/:id',
    name: 'classroom',
    component: () => import('@/views/ClassroomView.vue'),
    props: true,
    meta: { hideHeader: true },
  },
  {
    path: '/students/:id',
    name: 'student-detail',
    component: () => import('@/views/StudentDetailView.vue'),
    props: true,
  },
  // 迭代 2 新增
  {
    path: '/subjects',
    name: 'subjects',
    component: () => import('@/views/SubjectsView.vue'),
  },
  {
    path: '/homeworks',
    name: 'homeworks',
    component: () => import('@/views/HomeworksView.vue'),
    props: { type: 'homework' },
  },
  {
    path: '/homeworks/:id',
    name: 'homework-detail',
    component: () => import('@/views/HomeworkDetailView.vue'),
    props: true,
  },
  {
    path: '/exams',
    name: 'exams',
    component: () => import('@/views/HomeworksView.vue'),
    props: { type: 'exam' },
  },
  {
    path: '/exams/:id',
    name: 'exam-detail',
    component: () => import('@/views/HomeworkDetailView.vue'),
    props: true,
  },
  {
    path: '/shop',
    name: 'shop',
    component: () => import('@/views/ShopView.vue'),
  },
  {
    path: '/settings/score-rules',
    name: 'score-rules',
    component: () => import('@/views/ScoreRulesView.vue'),
  },
  {
    path: '/settings/species',
    name: 'species-manage',
    component: () => import('@/views/SpeciesManageView.vue'),
  },
  {
    path: '/dictation',
    name: 'dictation',
    component: () => import('@/views/DictationView.vue'),
  },
  {
    path: '/dictation/:id',
    name: 'word-group-detail',
    component: () => import('@/views/WordGroupDetailView.vue'),
    props: true,
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return { name: 'login' }
  }
  if (to.name === 'login' && auth.isLoggedIn) {
    return { name: 'dashboard' }
  }
})
