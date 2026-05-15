import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiUrl } from '../lib/api'
import { normalizeStoredToken } from '../lib/authToken'
import type { ActivityItem } from '../types'

export interface ActivityListParams {
  limit?: number
  skip?: number
  type?: string
  entityType?: string
  entityId?: string
  days?: number
  myOnly?: boolean
}

function authHeaders(): Record<string, string> {
  const token = normalizeStoredToken(localStorage.getItem('token'))
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const useActivitiesStore = defineStore('activities', () => {
  const items = ref<ActivityItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchList(params: ActivityListParams = {}) {
    loading.value = true
    error.value = null
    try {
      const qs = new URLSearchParams()
      if (params.limit != null) qs.set('limit', String(params.limit))
      if (params.skip != null) qs.set('skip', String(params.skip))
      if (params.type) qs.set('type', params.type)
      if (params.entityType) qs.set('entityType', params.entityType)
      if (params.entityId) qs.set('entityId', params.entityId)
      if (params.days != null) qs.set('days', String(params.days))
      if (params.myOnly) qs.set('myOnly', 'true')

      const url = apiUrl(`/api/activities${qs.toString() ? `?${qs}` : ''}`)
      const res = await fetch(url, { headers: authHeaders() })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      items.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load activities'
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function create(payload: {
    type: string
    entityType: string
    entityId: string
    description: string
    timestamp?: string
  }) {
    const res = await fetch(apiUrl('/api/activities'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        ...payload,
        timestamp: payload.timestamp || new Date().toISOString(),
      }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return (await res.json()) as ActivityItem
  }

  async function update(
    id: string,
    body: Partial<{ type: string; description: string; timestamp: string }>,
  ) {
    const res = await fetch(apiUrl(`/api/activities/${id}`), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return (await res.json()) as ActivityItem
  }

  async function remove(id: string) {
    const res = await fetch(apiUrl(`/api/activities/${id}`), {
      method: 'DELETE',
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
  }

  return { items, loading, error, fetchList, create, update, remove }
})
