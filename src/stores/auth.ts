import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiUrl } from '../lib/api'

import { normalizeStoredToken } from '../lib/authToken'

const REFRESH_TOKEN_KEY = 'refresh_token'

export type LoginResult = 'ok' | 'bad_credentials' | 'profile_failed'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(normalizeStoredToken(localStorage.getItem('token')))
  const refreshToken = ref<string | null>(
    normalizeStoredToken(localStorage.getItem(REFRESH_TOKEN_KEY)),
  )
  const user = ref<any>(null)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!normalizeStoredToken(token.value))
  const userRole = computed(() => user.value?.role || 'user')

  function persistTokens(access: string, refresh?: string | null): boolean {
    if (!access) {
      console.error('persistTokens: missing access_token')
      return false
    }
    token.value = access
    localStorage.setItem('token', access)
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    } else {
      refreshToken.value = null
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }
    return true
  }

  function clearStoredAuth() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  async function refreshAccessToken(): Promise<boolean> {
    const stored = normalizeStoredToken(refreshToken.value || localStorage.getItem(REFRESH_TOKEN_KEY))
    if (!stored) return false
    try {
      const response = await fetch(apiUrl('/api/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: stored }),
      })
      if (!response.ok) return false
      const data = await response.json()
      if (!data?.access_token) return false
      persistTokens(data.access_token, data.refresh_token)
      return true
    } catch (e) {
      console.error(e)
      return false
    }
  }

  /**
   * @param explicitAccessToken from login JSON (avoids ref timing issues)
   * @param revokeOnFailure if false, no redirect on 401 (during login)
   */
  async function fetchCurrentUser(
    explicitAccessToken?: string,
    revokeOnFailure = true,
  ): Promise<boolean> {
    const bearer =
      explicitAccessToken ??
      normalizeStoredToken(token.value) ??
      normalizeStoredToken(localStorage.getItem('token'))
    if (!bearer) return false
    token.value = bearer
    try {
      const response = await fetch(apiUrl('/api/users/me'), {
        headers: { Authorization: `Bearer ${bearer}` },
      })
      if (response.ok) {
        user.value = await response.json()
        return true
      }
      if (response.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          const t2 = normalizeStoredToken(token.value) ?? normalizeStoredToken(localStorage.getItem('token'))
          if (!t2) return false
          const retry = await fetch(apiUrl('/api/users/me'), {
            headers: { Authorization: `Bearer ${t2}` },
          })
          if (retry.ok) {
            user.value = await retry.json()
            return true
          }
        }
        if (revokeOnFailure) {
          clearStoredAuth()
          window.location.href = '/login'
        }
        return false
      }
      console.warn('fetchCurrentUser: unexpected status', response.status)
      return false
    } catch (e) {
      console.error('Fetch user failed - likely network or crash', e)
      return false
    }
  }

  async function login(username: string, password: string): Promise<LoginResult> {
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
      if (!response.ok) return 'bad_credentials'

      let data: { access_token?: string; refresh_token?: string }
      try {
        data = await response.json()
      } catch {
        return 'bad_credentials'
      }
      if (!data?.access_token || typeof data.access_token !== 'string') {
        console.error('Login response missing access_token', data)
        return 'bad_credentials'
      }
      if (!persistTokens(data.access_token, data.refresh_token)) return 'bad_credentials'

      const profileOk = await fetchCurrentUser(data.access_token, false)
      if (!profileOk) {
        clearStoredAuth()
        return 'profile_failed'
      }
      return 'ok'
    } catch (e) {
      console.error(e)
      return 'bad_credentials'
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
      return (await login(email, password)) === 'ok'
    } catch (e) {
      console.error(e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    clearStoredAuth()
    window.location.href = '/login'
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
    fetchCurrentUser: () => fetchCurrentUser(undefined, true),
    refreshAccessToken,
    logout,
  }
})
