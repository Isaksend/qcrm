import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Deal } from '../types'

const API_URL = 'http://127.0.0.1:8000/api'

export const useDealsStore = defineStore('deals', () => {
  const deals = ref<Deal[]>([])
  const sortField = ref<keyof Deal>('value')
  const sortDirection = ref<'asc' | 'desc'>('desc')
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const sortedDeals = computed(() => {
    return [...deals.value].sort((a, b) => {
      const aVal = a[sortField.value]
      const bVal = b[sortField.value]
      if (aVal == null && bVal == null) return 0
      if (aVal == null) return 1
      if (bVal == null) return -1
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0
      return sortDirection.value === 'asc' ? cmp : -cmp
    })
  })

  const totalValue = computed(() =>
    deals.value.reduce((sum, d) => sum + d.value, 0)
  )

  const wonValue = computed(() =>
    deals.value
      .filter((d) => d.stage === 'Closed Won')
      .reduce((sum, d) => sum + d.value, 0)
  )

  const lostValue = computed(() =>
    deals.value
      .filter((d) => d.stage === 'Closed Lost')
      .reduce((sum, d) => sum + d.value, 0)
  )

  const byStage = computed(() => {
    const stages = ['New Request', 'Qualified', 'Discovery', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    return stages.map((stage) => {
      const stageDeals = deals.value.filter((d) => d.stage === stage)
      return {
        stage,
        count: stageDeals.length,
        value: stageDeals.reduce((sum, d) => sum + d.value, 0),
      }
    })
  })

  async function fetchDeals() {
    isLoading.value = true
    error.value = null
    try {
      const response = await fetch(`${API_URL}/deals`)
      if (!response.ok) throw new Error('Failed to fetch deals')
      deals.value = await response.json()
    } catch (e: any) {
      error.value = e.message
      console.error(error.value)
    } finally {
      isLoading.value = false
    }
  }

  function setSort(field: keyof Deal) {
    if (sortField.value === field) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDirection.value = 'desc'
    }
  }

  async function addDeal(data: Omit<Deal, 'id'>) {
    // set safe defaults for pydantic backend
    const payload = {
      title: data.title,
      contactId: data.contactId || null,
      leadId: data.leadId || null,
      value: data.value || 0.0,
      stage: data.stage || 'New Request',
      sellerId: data.sellerId || "default_seller",
      closedAt: data.closedAt || null
    }
    
    try {
      const response = await fetch(`${API_URL}/deals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!response.ok) throw new Error('Failed to create deal')
      const newDeal = await response.json()
      deals.value.push(newDeal)
    } catch (e: any) {
      console.error('Error adding deal:', e.message)
    }
  }

  async function updateDealStage(id: string, stage: Deal['stage']) {
    // Optimistic UI update
    const deal = deals.value.find((d) => d.id === id)
    const oldStage = deal?.stage
    if (deal) deal.stage = stage

    try {
      const response = await fetch(`${API_URL}/deals/${id}/stage?stage=${encodeURIComponent(stage)}`, {
        method: 'PATCH'
      })
      if (!response.ok) {
        throw new Error('Failed to update stage on server')
      }
    } catch (e: any) {
      console.error(e)
      // Rollback optimistic update
      if (deal && oldStage) {
        deal.stage = oldStage
      }
    }
  }

  return {
    deals,
    sortField,
    sortDirection,
    isLoading,
    error,
    sortedDeals,
    totalValue,
    wonValue,
    lostValue,
    byStage,
    fetchDeals,
    setSort,
    addDeal,
    updateDealStage,
  }
})
