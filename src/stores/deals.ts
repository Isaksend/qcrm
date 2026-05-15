import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'
import { i18n } from '../i18n'
import { formatMonthShort } from '../i18n/dates'
import { usePeriodFilterStore, isDealInYearMonth } from './periodFilter'
import type { Deal } from '../types'
import { apiUrl } from '../lib/api'

export const useDealsStore = defineStore('deals', () => {
  const deals = ref<Deal[]>([])
  const sortField = ref<keyof Deal>('value')
  const sortDirection = ref<'asc' | 'desc'>('desc')
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const authStore = useAuthStore()
  const periodFilter = usePeriodFilterStore()

  const dealsInPeriod = computed(() =>
    deals.value.filter((d) => isDealInYearMonth(d, periodFilter.year, periodFilter.month)),
  )

  const sortedDeals = computed(() => {
    return [...dealsInPeriod.value].sort((a, b) => {
      const aVal = a[sortField.value]
      const bVal = b[sortField.value]
      if (aVal == null && bVal == null) return 0
      if (aVal == null) return 1
      if (bVal == null) return -1
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0
      return sortDirection.value === 'asc' ? cmp : -cmp
    })
  })

  const totalValue = computed(() => dealsInPeriod.value.reduce((sum, d) => sum + d.value, 0))

  const wonValue = computed(() =>
    dealsInPeriod.value.filter((d) => d.stage === 'Closed Won').reduce((sum, d) => sum + d.value, 0),
  )

  const lostValue = computed(() =>
    dealsInPeriod.value.filter((d) => d.stage === 'Closed Lost').reduce((sum, d) => sum + d.value, 0),
  )

  const byStage = computed(() => {
    const stages = ['New Request', 'Qualified', 'Discovery', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    return stages.map((stage) => {
      const stageDeals = dealsInPeriod.value.filter((d) => d.stage === stage)
      return {
        stage,
        count: stageDeals.length,
        value: stageDeals.reduce((sum, d) => sum + d.value, 0),
      }
    })
  })

  /** Won revenue grouped by calendar month (last 6 months ending at selected period). */
  const monthlyWonRevenue = computed(() => {
    const loc = i18n.global.locale.value
    const { year, month } = periodFilter
    const anchor = new Date(year, month - 1, 1)
    const buckets: { key: string; label: string; value: number; isSelected: boolean }[] = []
    for (let i = 5; i >= 0; i--) {
      const d = new Date(anchor.getFullYear(), anchor.getMonth() - i, 1)
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      const key = `${y}-${String(m).padStart(2, '0')}`
      const label = formatMonthShort(d, loc)
      const value = deals.value
        .filter(
          (deal) =>
            deal.stage === 'Closed Won' &&
            isDealInYearMonth(deal, y, m),
        )
        .reduce((sum, deal) => sum + deal.value, 0)
      buckets.push({
        key,
        label,
        value,
        isSelected: y === year && m === month,
      })
    }
    return buckets
  })

  async function fetchDeals() {
    isLoading.value = true
    error.value = null
    try {
      const response = await fetch(apiUrl('/api/deals'), {
        headers: { Authorization: `Bearer ${authStore.token}` },
      })
      if (!response.ok) throw new Error('Failed to fetch deals')
      const rows = (await response.json()) as Deal[]
      deals.value = rows.map((d) => ({
        ...d,
        createdAt: d.createdAt ?? d.closedAt ?? undefined,
      }))
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch deals'
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

  async function addDeal(
    data: Omit<Deal, 'id'> & { companyId?: string | null },
  ): Promise<{ ok: true; deal: Deal } | { ok: false; error: string }> {
    try {
      const isSuper = authStore.userRole === 'super_admin'
      const resolvedCompanyId = isSuper ? (data.companyId ?? null) : (authStore.user?.company_id ?? null)
      const response = await fetch(apiUrl('/api/deals'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authStore.token}`,
        },
        body: JSON.stringify({
          ...data,
          leadId: data.leadId?.trim() ? data.leadId : null,
          contactId: data.contactId?.trim() ? data.contactId : null,
          companyId: resolvedCompanyId,
          userId: data.userId?.trim() ? data.userId : null,
        }),
      })
      if (!response.ok) {
        let detail = 'Не удалось создать сделку'
        try {
          const err = await response.json()
          if (err.detail) detail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)
        } catch {
          /* ignore */
        }
        return { ok: false, error: detail }
      }
      const newDeal = (await response.json()) as Deal
      if (!newDeal.createdAt) {
        newDeal.createdAt = new Date().toISOString()
      }
      deals.value.push(newDeal)
      return { ok: true, deal: newDeal }
    } catch (e: unknown) {
      console.error('Error adding deal:', e)
      return { ok: false, error: e instanceof Error ? e.message : 'Ошибка сети при создании сделки' }
    }
  }

  async function updateDealStage(id: string, stage: Deal['stage']) {
    const deal = deals.value.find((d) => d.id === id)
    const oldStage = deal?.stage
    if (deal) deal.stage = stage

    try {
      const response = await fetch(apiUrl(`/api/deals/${id}/stage?stage=${encodeURIComponent(stage)}`), {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${authStore.token}` },
      })
      if (!response.ok) {
        throw new Error('Failed to update stage on server')
      }
      const updated = (await response.json()) as Deal
      const i = deals.value.findIndex((d) => d.id === id)
      if (i >= 0) deals.value[i] = { ...deals.value[i], ...updated }
    } catch (e: unknown) {
      console.error(e)
      if (deal && oldStage) {
        deal.stage = oldStage
      }
    }
  }

  async function updateDeal(id: string, patch: Partial<Deal>) {
    error.value = null
    try {
      const response = await fetch(apiUrl(`/api/deals/${id}`), {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authStore.token}`,
        },
        body: JSON.stringify(patch),
      })
      if (!response.ok) throw new Error('Failed to update deal')
      const updated = (await response.json()) as Deal
      const i = deals.value.findIndex((d) => d.id === id)
      if (i >= 0) deals.value[i] = updated
      return updated
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to update deal'
      console.error(e)
      return null
    }
  }

  async function deleteDeal(id: string) {
    error.value = null
    try {
      const response = await fetch(apiUrl(`/api/deals/${id}`), {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${authStore.token}` },
      })
      if (!response.ok) throw new Error('Failed to delete deal')
      deals.value = deals.value.filter((d) => d.id !== id)
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to delete deal'
      console.error(e)
      return false
    }
  }

  return {
    deals,
    dealsInPeriod,
    sortField,
    sortDirection,
    isLoading,
    error,
    sortedDeals,
    totalValue,
    wonValue,
    lostValue,
    byStage,
    monthlyWonRevenue,
    fetchDeals,
    setSort,
    addDeal,
    updateDealStage,
    updateDeal,
    deleteDeal,
  }
})
