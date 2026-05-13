<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import GlobalSearch from './GlobalSearch.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
import { useAuthStore } from '../../stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const isSearchOpen = ref(false)
const authStore = useAuthStore()

const userInitial = computed(() => {
  if (authStore.user?.name) {
    return authStore.user.name.charAt(0).toUpperCase()
  }
  return 'U'
})

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    isSearchOpen.value = true
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0 relative z-40">
    <div class="flex items-center gap-4 flex-1">
      <h1 class="text-lg font-bold text-gray-900 mr-4 hidden sm:block tracking-tight">
        <router-link to="/" class="hover:text-indigo-600 transition-colors">{{ t('topbar.brand') }}</router-link>
      </h1>
      
      <!-- Search Input Trigger -->
      <button 
        @click="isSearchOpen = true"
        class="flex-1 max-w-md flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-400 hover:bg-white hover:border-gray-300 hover:shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/20 group"
      >
        <svg class="w-4 h-4 text-gray-400 group-hover:text-indigo-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        <span class="flex-1 text-left hidden sm:inline text-gray-500">{{ t('topbar.searchPlaceholder') }}</span>
        <span class="flex-1 text-left sm:hidden text-gray-500">{{ t('topbar.searchShort') }}</span>
        <div class="hidden sm:flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-white border border-gray-200 shadow-sm text-gray-500">
          <span class="font-sans">⌘</span>
          <span>K</span>
        </div>
      </button>
    </div>

    <div class="flex items-center gap-3 ml-4">
      <LanguageSwitcher />
      <!-- Avatar -->
      <router-link to="/profile" class="w-8 h-8 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-full flex items-center justify-center cursor-pointer shadow-sm ring-2 ring-white hover:ring-indigo-100 transition-all">
        <span class="text-white text-xs font-bold">{{ userInitial }}</span>
      </router-link>
    </div>
  </header>

  <GlobalSearch v-model="isSearchOpen" />
</template>
