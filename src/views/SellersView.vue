<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSellersStore } from '../stores/sellers'
import SellerGrid from '../components/sellers/SellerGrid.vue'
import SellerForm from '../components/sellers/SellerForm.vue'

const sellersStore = useSellersStore()
const showForm = ref(false)

onMounted(() => {
  sellersStore.fetchSellers()
})

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Sales Team</h1>
        <p class="text-sm text-gray-500 mt-1">Performance metrics and leaderboard.</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <div class="text-xs text-gray-500">Team Revenue</div>
          <div class="text-lg font-bold text-gray-900">{{ formatCurrency(sellersStore.totalTeamRevenue) }}</div>
        </div>
        <div class="text-right">
          <div class="text-xs text-gray-500">Avg Conversion</div>
          <div class="text-lg font-bold text-indigo-600">{{ sellersStore.avgConversionRate }}%</div>
        </div>
        <button @click="showForm = true" class="btn-primary">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
          New Seller
        </button>
      </div>
    </div>

    <!-- Leaderboard -->
    <div class="card mb-6">
      <h3 class="text-sm font-semibold text-gray-800 mb-3">Leaderboard</h3>
      <div class="space-y-2">
        <div
          v-for="(seller, idx) in sellersStore.rankedSellers"
          :key="seller.id"
          class="flex items-center gap-3 px-3 py-2 rounded-lg"
          :class="idx === 0 ? 'bg-yellow-50' : 'hover:bg-gray-50'"
        >
          <span class="text-sm font-bold w-6 text-center" :class="idx === 0 ? 'text-yellow-600' : 'text-gray-400'">#{{ idx + 1 }}</span>
          <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
            <span class="text-indigo-600 text-xs font-semibold">{{ seller.avatar }}</span>
          </div>
          <span class="text-sm font-medium text-gray-800 flex-1">{{ seller.name }}</span>
          <span class="text-sm font-semibold text-gray-700">{{ formatCurrency(seller.revenue) }}</span>
          <span class="text-xs text-gray-500 w-12 text-right">{{ seller.conversionRate }}%</span>
        </div>
      </div>
    </div>

    <SellerGrid />
    <SellerForm v-if="showForm" @close="showForm = false" />
  </div>
</template>
