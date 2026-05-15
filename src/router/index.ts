import { createRouter, createWebHistory } from 'vue-router'
import { normalizeStoredToken } from '../lib/authToken'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/contacts',
      name: 'contacts',
      component: () => import('../views/ContactsView.vue'),
      meta: { requiresAuth: true },
    },

    {
      path: '/deals',
      name: 'deals',
      component: () => import('../views/DealsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/my-tasks',
      name: 'my-deal-tasks',
      component: () => import('../views/MyDealTasksView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/companies',
      name: 'companies',
      component: () => import('../views/CompaniesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/activities',
      name: 'activities',
      component: () => import('../views/ActivitiesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/deals/:id',
      name: 'deal-detail',
      component: () => import('../views/DealDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/messages',
      name: 'messages',
      component: () => import('../views/MessagesView.vue'),
      meta: { requiresAuth: true }
    },

    {
      path: '/users',
      name: 'users',
      component: () => import('../views/UsersView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('../views/AnalyticsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guest: true }
    },
  ],
})

/** Страницы без входа (явный whitelist — остальные только с токеном). */
const PUBLIC_PATHS = new Set(['/login', '/register'])

router.beforeEach((to, _from, next) => {
  const token = normalizeStoredToken(localStorage.getItem('token'))
  const isPublic =
    PUBLIC_PATHS.has(to.path) || to.matched.some((r) => r.meta.guest === true)

  if (isPublic) {
    next()
    return
  }

  if (!token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
