<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import LanguageSwitcher from '../components/layout/LanguageSwitcher.vue'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()

const email = ref('')
const password = ref('')
const error = ref('')

async function handleSubmit() {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = t('auth.errors.fillAll')
    return
  }
  const success = await authStore.login(email.value, password.value)
  if (success) {
    router.push('/')
  } else {
    error.value = t('auth.errors.invalidCredentials')
  }
}
</script>

<template>
  <div class="h-full flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full p-8 bg-white rounded-xl shadow-sm border border-gray-100">
      <div class="text-center mb-8">
        <div class="w-12 h-12 bg-indigo-500 rounded-xl flex items-center justify-center mx-auto mb-4 text-white font-bold text-xl">C</div>
        <h2 class="text-2xl font-bold text-gray-900">{{ t('auth.signInTitle') }}</h2>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div v-if="error" class="p-3 bg-red-50 text-red-600 text-sm rounded-lg">{{ error }}</div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('auth.email') }}</label>
          <input v-model="email" type="email" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" placeholder="you@example.com" />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('auth.password') }}</label>
          <input v-model="password" type="password" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" placeholder="••••••••" />
        </div>

        <button type="submit" class="w-full btn-primary py-2.5 flex justify-center mt-6" :disabled="authStore.isLoading">
          <span v-if="authStore.isLoading">{{ t('auth.signingIn') }}</span>
          <span v-else>{{ t('auth.signIn') }}</span>
        </button>
      </form>

      <p class="text-center mt-6 text-sm text-gray-600">
        {{ t('auth.noAccount') }} <router-link to="/register" class="text-indigo-600 hover:text-indigo-500 font-medium">{{ t('auth.createOne') }}</router-link>
      </p>
      <div class="flex justify-center mt-4">
        <LanguageSwitcher />
      </div>
    </div>
  </div>
</template>
