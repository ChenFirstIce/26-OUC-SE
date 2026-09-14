import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
    { path: '/p/fill/:token', component: () => import('./views/patient/PatientPortal.vue'), meta: { public: true } },
    {
      path: '/', component: () => import('./layouts/StaffLayout.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: () => import('./views/DashboardView.vue') },
        { path: 'patients', component: () => import('./views/PatientsView.vue') },
        { path: 'patients/:id', component: () => import('./views/PatientDetailView.vue') },
        { path: 'assignments', component: () => import('./views/AssignmentsView.vue') },
        { path: 'assignments/create', component: () => import('./views/CreateAssignmentView.vue') },
        { path: 'questionnaires', component: () => import('./views/QuestionnairesView.vue') },
        { path: 'admin', component: () => import('./views/AdminCenterView.vue'), meta: { adminOnly: true } },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const auth = useAuthStore()
  if (!auth.loggedIn) return { path: '/login', query: { redirect: to.fullPath } }
  if (!auth.user?.permissions) {
    try { await auth.refresh() } catch { auth.logout(); return { path: '/login', query: { redirect: to.fullPath } } }
  }
  if (to.meta.adminOnly && auth.user?.role !== 'admin') return '/dashboard'
  return true
})

export default router
