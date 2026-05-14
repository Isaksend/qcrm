import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiUrl } from '../lib/api'
import { useAuthStore } from './auth'
import type { MyDealTaskItem } from '../types'

export const useMyDealTasksStore = defineStore('myDealTasks', () => {
  const openCount = ref(0)
  const items = ref<MyDealTaskItem[]>([])
  const loading = ref(false)

  async function refresh(limit = 80) {
    const auth = useAuthStore()
    const token = auth.token || localStorage.getItem('token')
    if (!token) {
      openCount.value = 0
      items.value = []
      return
    }
    loading.value = true
    try {
      const res = await fetch(apiUrl(`/api/users/me/deal-tasks?limit=${limit}`), {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('deal-tasks')
      const data = (await res.json()) as { openCount?: number; items?: MyDealTaskItem[] }
      openCount.value = Number(data.openCount) || 0
      items.value = Array.isArray(data.items) ? data.items : []
    } catch {
      openCount.value = 0
      items.value = []
    } finally {
      loading.value = false
    }
  }

  return { openCount, items, loading, refresh }
})
