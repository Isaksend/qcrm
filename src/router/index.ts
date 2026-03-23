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
      path: '/leads',
      name: 'leads',
      component: () => import('../views/LeadsView.vue'),
    },
    {
      path: '/deals',
      name: 'deals',
      component: () => import('../views/DealsView.vue'),
    },
    {
      path: '/sellers',
      name: 'sellers',
      component: () => import('../views/SellersView.vue'),
    },
    {
      path: '/ai',
      name: 'ai',
      component: () => import('../views/AIView.vue'),
    },
  ],
})

export default router
