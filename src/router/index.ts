import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
    },
    {
      path: '/contacts',
      name: 'contacts',
      component: () => import('../views/ContactsView.vue'),
    },

    {
      path: '/deals',
      name: 'deals',
      component: () => import('../views/DealsView.vue'),
    },
    {
      path: '/deals/:id',
      name: 'deal-detail',
      component: () => import('../views/DealDetailView.vue'),
      meta: { requiresAuth: true }
    },

    {
      path: '/users',
      name: 'users',
      component: () => import('../views/UsersView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ai',
      name: 'ai',
      component: () => import('../views/AIView.vue'),
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

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const isAuthRequired = to.matched.some(record => record.meta.requiresAuth || !record.meta.guest && !record.meta.requiresAuth) // assume default requires auth
  const isGuestOnly = to.matched.some(record => record.meta.guest)

  if (isGuestOnly) {
    next()
  } else if (isAuthRequired && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
