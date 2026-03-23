import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Deal } from '../types'
import { deals as mockDeals } from '../data/mock'

export const useDealsStore = defineStore('deals', () => {
  const deals = ref<Deal[]>(mockDeals)
  const sortField = ref<keyof Deal>('value')
  const sortDirection = ref<'asc' | 'desc'>('desc')

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
    const stages = ['Discovery', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    return stages.map((stage) => {
      const stageDeals = deals.value.filter((d) => d.stage === stage)
      return {
        stage,
        count: stageDeals.length,
        value: stageDeals.reduce((sum, d) => sum + d.value, 0),
      }
    })
  })

  function setSort(field: keyof Deal) {
    if (sortField.value === field) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDirection.value = 'desc'
    }
  }

  function addDeal(data: Omit<Deal, 'id'>) {
    const id = `d${Date.now()}`
    deals.value.push({ ...data, id })
  }

  return {
    deals,
    sortField,
    sortDirection,
    sortedDeals,
    totalValue,
    wonValue,
    lostValue,
    byStage,
    setSort,
    addDeal,
  }
})
