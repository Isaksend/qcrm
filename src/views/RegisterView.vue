<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const name = ref('')
const email = ref('')
const password = ref('')
const error = ref('')

async function handleSubmit() {
  error.value = ''
  if (!name.value || !email.value || !password.value) {
    error.value = 'Please fill in all fields'
    return
  }
  const success = await authStore.register(name.value, email.value, password.value)
  if (success) {
    router.push('/')
  } else {
    error.value = 'Registration failed. Email might be taken.'
  }
}
</script>

<template>
  <div class="h-full flex items-center justify-center bg-gray-50">
    <div class="max-w-md w-full p-8 bg-white rounded-xl shadow-sm border border-gray-100">
      <div class="text-center mb-8">
        <h2 class="text-2xl font-bold text-gray-900">Create an Account</h2>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div v-if="error" class="p-3 bg-red-50 text-red-600 text-sm rounded-lg">{{ error }}</div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
          <input v-model="name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" placeholder="John Doe" />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input v-model="email" type="email" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" placeholder="you@example.com" />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input v-model="password" type="password" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" placeholder="••••••••" />
        </div>

        <button type="submit" class="w-full btn-primary py-2.5 flex justify-center mt-6" :disabled="authStore.isLoading">
          <span v-if="authStore.isLoading">Creating account...</span>
          <span v-else>Register</span>
        </button>
      </form>
      
      <p class="text-center mt-6 text-sm text-gray-600">
        Already have an account? <router-link to="/login" class="text-indigo-600 hover:text-indigo-500 font-medium">Sign in</router-link>
      </p>
    </div>
  </div>
</template>
