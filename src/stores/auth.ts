import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiUrl } from '../lib/api'

const REFRESH_TOKEN_KEY = 'refresh_token'

function persistTokens(access: string, refresh: string) {
  token.value = access
  refreshToken.value = refresh
  localStorage.setItem('token', access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_TOKEN_KEY))
  const user = ref<any>(null)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || 'user')

  async function refreshAccessToken(): Promise<boolean> {
    const stored = refreshToken.value || localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!stored) return false
    try {
      const response = await fetch(apiUrl('/api/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: stored }),
      })
      if (!response.ok) return false
      const data = await response.json()
      persistTokens(data.access_token, data.refresh_token)
      return true
    } catch (e) {
      console.error(e)
      return false
    }
  }

  async function login(username: string, password: string) {
    isLoading.value = true
    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const response = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      })
      if (!response.ok) throw new Error('Login failed')
      const data = await response.json()
      persistTokens(data.access_token, data.refresh_token)
      await fetchCurrentUser()
      return true
    } catch (e) {
      console.error(e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function register(name: string, email: string, password: string, _role?: string) {
    isLoading.value = true
    try {
      const response = await fetch(apiUrl('/api/auth/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, role: 'sales_representative' }),
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
      const response = await fetch(apiUrl('/api/users/me'), {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      if (response.ok) {
        user.value = await response.json()
      } else if (response.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          await fetchCurrentUser()
          return
        }
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
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    window.location.href = '/login' // Force redirect to resolve any routing state
  }

  return {
    token,
    refreshToken,
    user,
    isLoading,
    isAuthenticated,
    userRole,
    login,
    register,
    fetchCurrentUser,
    refreshAccessToken,
    logout,
  }
})
