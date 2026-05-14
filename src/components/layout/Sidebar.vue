<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const authStore = useAuthStore()
const { t } = useI18n()

const navItems = computed(() => {
  const elevated = ['admin', 'super_admin', 'manager'].includes(authStore.userRole)
  const items = [
    { to: '/', key: 'nav.dashboard', icon: 'chart-bar' },
    { to: '/contacts', key: 'nav.contacts', icon: 'users' },
    { to: '/deals', key: 'nav.deals', icon: 'currency' },
  ]
  if (elevated) {
    items.push({ to: '/companies', key: 'nav.companies', icon: 'currency' })
  }
  items.push(
    { to: '/analytics', key: 'nav.analytics', icon: 'chart-bar' },
    { to: '/messages', key: 'nav.messages', icon: 'chat' },
    { to: '/activities', key: 'nav.activities', icon: 'sparkles' },
  )
  if (authStore.userRole === 'admin' || authStore.userRole === 'super_admin' || authStore.userRole === 'manager') {
    items.push({ to: '/users', key: 'nav.team', icon: 'shield-check' })
  }
  return items
})

function isActive(to: string) {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}
</script>

<template>
  <aside class="w-64 bg-[#0f172a] flex flex-col shrink-0">
    <div class="h-16 flex items-center gap-3 px-6 border-b border-white/10">
      <div class="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center">
        <span class="text-white font-bold text-sm">C</span>
      </div>
      <span class="text-white font-semibold text-lg">Tiny CRM</span>
    </div>

    <nav class="flex-1 px-3 py-4 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'sidebar-link',
          isActive(item.to) ? 'sidebar-link-active' : 'sidebar-link-inactive',
        ]"
      >
        <!-- Chart Bar -->
        <svg v-if="item.icon === 'chart-bar'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <!-- Users -->
        <svg v-if="item.icon === 'users'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
        </svg>

        <!-- Currency -->
        <svg v-if="item.icon === 'currency'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>

        <!-- Sparkles -->
        <svg v-if="item.icon === 'sparkles'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
        <!-- Shield Check -->
        <svg v-if="item.icon === 'shield-check'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <!-- Chat / Telegram -->
        <svg v-if="item.icon === 'chat'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <span>{{ t(item.key) }}</span>
      </router-link>
    </nav>

    <div class="px-4 py-4 border-t border-white/10">
      <div class="text-xs text-gray-500">{{ t('common.version') }}</div>
    </div>
  </aside>
</template>
