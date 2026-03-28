import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Seller } from '../types'
const API_URL = 'http://127.0.0.1:8000/api'

export const useSellersStore = defineStore('sellers', () => {
  const sellers = ref<Seller[]>([])
  const isLoading = ref(false)

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

  async function addSeller(data: Omit<Seller, 'id' | 'avatar'>) {
    const avatar = data.name
      .split(' ')
      .map((w) => w[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()
    
    const payload = { ...data, avatar }

    try {
      const response = await fetch(`${API_URL}/sellers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (response.ok) {
        const newSeller = await response.json()
        sellers.value.push(newSeller)
      } else {
        console.error('Failed to save seller via API')
      }
    } catch (e) {
      console.error(e)
    }
  }

  async function fetchSellers() {
    isLoading.value = true
    try {
      const response = await fetch(`${API_URL}/sellers`)
      if (response.ok) {
        sellers.value = await response.json()
      }
    } catch (e) {
      console.error(e)
    } finally {
      isLoading.value = false
    }
  }

  return {
    sellers,
    rankedSellers,
    totalTeamRevenue,
    avgConversionRate,
    isLoading,
    getSeller,
    addSeller,
    fetchSellers,
  }
})
