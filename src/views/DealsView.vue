<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDealsStore } from '../stores/deals'
import DealsTable from '../components/deals/DealsTable.vue'
import DealForm from '../components/deals/DealForm.vue'
import { monthlyRevenue } from '../data/mock'

const dealsStore = useDealsStore()
const showForm = ref(false)

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

const maxMonthly = computed(() => Math.max(...monthlyRevenue.map((m) => m.value)))
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Deals</h1>
        <p class="text-sm text-gray-500 mt-1">Overview of all your deals and revenue.</p>
      </div>
      <button @click="showForm = true" class="btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
        New Deal
      </button>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">Total Pipeline</div>
        <div class="text-xl font-bold text-gray-900">{{ formatCurrency(dealsStore.totalValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">{{ dealsStore.deals.length }} deals</div>
      </div>
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">Won Revenue</div>
        <div class="text-xl font-bold text-green-600">{{ formatCurrency(dealsStore.wonValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">{{ dealsStore.deals.filter(d => d.stage === 'Closed Won').length }} deals</div>
      </div>
      <div class="card">
        <div class="text-xs text-gray-500 mb-1">Lost Revenue</div>
        <div class="text-xl font-bold text-red-500">{{ formatCurrency(dealsStore.lostValue) }}</div>
        <div class="text-xs text-gray-400 mt-1">{{ dealsStore.deals.filter(d => d.stage === 'Closed Lost').length }} deals</div>
      </div>
    </div>

    <!-- Monthly Revenue Mini Chart -->
    <div class="card mb-6">
      <h3 class="text-sm font-semibold text-gray-800 mb-3">Monthly Revenue</h3>
      <div class="flex items-end gap-2 h-20">
        <div
          v-for="month in monthlyRevenue"
          :key="month.month"
          class="flex-1 flex flex-col items-center gap-1"
        >
          <div class="w-full bg-gray-100 rounded-t flex-1 flex items-end">
            <div
              class="w-full bg-indigo-400 rounded-t transition-all hover:bg-indigo-500"
              :style="{ height: `${(month.value / maxMonthly) * 100}%` }"
            ></div>
          </div>
          <span class="text-[10px] text-gray-400">{{ month.month }}</span>
        </div>
      </div>
    </div>

    <DealsTable />
    <DealForm v-if="showForm" @close="showForm = false" />
  </div>
</template>
