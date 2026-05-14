<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import Sidebar from './components/layout/Sidebar.vue'
import TopBar from './components/layout/TopBar.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isAuthRoute = computed(() => {
  return route.path === '/login' || route.path === '/register'
})

const isAppLoading = ref(true)

onMounted(async () => {
  await router.isReady()
  if (authStore.token) {
    await authStore.fetchCurrentUser()
  }
  isAppLoading.value = false
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">
    <div v-if="isAppLoading" class="w-full h-full flex items-center justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
    </div>
    
    <template v-else-if="!isAuthRoute">
      <Sidebar />
      <div class="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main class="flex-1 overflow-y-auto p-6 bg-gray-50">
          <router-view />
        </main>
      </div>
    </template>
    
    <template v-else>
      <main class="flex-1 w-full h-full overflow-y-auto">
        <router-view />
      </main>
    </template>
  </div>
</template>
