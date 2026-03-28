import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_URL = 'http://127.0.0.1:8000/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || 'user')

  async function login(username: string, password: string) {
    isLoading.value = true
    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      })
      if (!response.ok) throw new Error('Login failed')
      const data = await response.json()
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      await fetchCurrentUser()
      return true
    } catch (e) {
      console.error(e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function register(name: string, email: string, password: string, role: string = 'user') {
    isLoading.value = true
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, role }),
      })
      if (!response.ok) throw new Error('Registration failed')
      return await login(email, password)
    } catch (e) {
      console.error(e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return
    try {
      const response = await fetch(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      if (response.ok) {
        user.value = await response.json()
      } else if (response.status === 401) {
        // Only logout if token is actually invalid
        logout()
      } else {
        console.warn('Server error, but keeping token to retry later.', response.status)
      }
    } catch (e) {
      console.error('Fetch user failed - likely network or crash', e)
      // Do NOT call logout here to prevent redirect loops when backend crashes mid-session
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    window.location.href = '/login' // Force redirect to resolve any routing state
  }

  return { token, user, isLoading, isAuthenticated, userRole, login, register, fetchCurrentUser, logout }
})
