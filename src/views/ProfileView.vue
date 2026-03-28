<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">User Profile</h1>
      <p class="text-sm text-gray-500 mt-1">Manage your account settings.</p>
    </div>

    <div class="card max-w-2xl">
      <div v-if="authStore.user" class="space-y-6">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 text-2xl font-bold">
            {{ authStore.user.name.charAt(0).toUpperCase() }}
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-900">{{ authStore.user.name }}</h2>
            <p class="text-gray-500">{{ authStore.user.role }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-6 border-t border-gray-100">
          <div>
            <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Email</label>
            <div class="text-gray-900 font-medium">{{ authStore.user.email }}</div>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Status</label>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-green-500"></span>
              <span class="text-sm text-gray-900 font-medium">Active</span>
            </div>
          </div>
        </div>

        <div class="pt-6 border-t border-gray-100 flex justify-end">
          <button @click="handleLogout" class="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors">
            Log out
          </button>
        </div>
      </div>
      <div v-else class="text-center py-8 text-gray-500">
        Loading profile data...
      </div>
    </div>
  </div>
</template>
