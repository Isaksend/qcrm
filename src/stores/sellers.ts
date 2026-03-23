import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Seller } from '../types'
import { sellers as mockSellers } from '../data/mock'

export const useSellersStore = defineStore('sellers', () => {
  const sellers = ref<Seller[]>(mockSellers)

  const rankedSellers = computed(() =>
    [...sellers.value].sort((a, b) => b.revenue - a.revenue)
  )

  const totalTeamRevenue = computed(() =>
    sellers.value.reduce((sum, s) => sum + s.revenue, 0)
  )

  const avgConversionRate = computed(() => {
    if (!sellers.value.length) return 0
    return Math.round(
      sellers.value.reduce((sum, s) => sum + s.conversionRate, 0) / sellers.value.length
    )
  })

  function getSeller(id: string) {
    return sellers.value.find((s) => s.id === id)
  }

  function addSeller(data: Omit<Seller, 'id' | 'avatar'>) {
    const id = `s${Date.now()}`
    const avatar = data.name
      .split(' ')
      .map((w) => w[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()
    sellers.value.push({ ...data, id, avatar })
  }

  return {
    sellers,
    rankedSellers,
    totalTeamRevenue,
    avgConversionRate,
    getSeller,
    addSeller,
  }
})
