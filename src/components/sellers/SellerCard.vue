<script setup lang="ts">
import type { Seller } from '../../types'

defineProps<{
  seller: Seller
  rank: number
}>()

defineEmits<{
  analyze: [id: string]
}>()

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val)
}

const rankColors = ['bg-yellow-400', 'bg-gray-300', 'bg-orange-400']
</script>

<template>
  <div class="card hover:shadow-md transition-shadow">
    <div class="flex items-start justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="relative">
          <div class="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center">
            <span class="text-indigo-600 font-semibold">{{ seller.avatar }}</span>
          </div>
          <div
            v-if="rank <= 3"
            class="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
            :class="rankColors[rank - 1]"
          >
            {{ rank }}
          </div>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-gray-900">{{ seller.name }}</h3>
          <p class="text-xs text-gray-500">{{ seller.role }}</p>
        </div>
      </div>
      <button
        @click="$emit('analyze', seller.id)"
        class="p-1.5 text-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
        title="AI Coaching"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
      </button>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div class="bg-gray-50 rounded-lg p-3">
        <div class="text-xs text-gray-500 mb-0.5">Revenue</div>
        <div class="text-sm font-bold text-gray-900">{{ formatCurrency(seller.revenue) }}</div>
      </div>
      <div class="bg-gray-50 rounded-lg p-3">
        <div class="text-xs text-gray-500 mb-0.5">Conversion</div>
        <div class="text-sm font-bold text-gray-900">{{ seller.conversionRate }}%</div>
      </div>
      <div class="bg-gray-50 rounded-lg p-3">
        <div class="text-xs text-gray-500 mb-0.5">Deals Won</div>
        <div class="text-sm font-bold text-gray-900">{{ seller.dealsWon }} / {{ seller.dealsClosed }}</div>
      </div>
      <div class="bg-gray-50 rounded-lg p-3">
        <div class="text-xs text-gray-500 mb-0.5">Active Leads</div>
        <div class="text-sm font-bold text-gray-900">{{ seller.activeLeads }}</div>
      </div>
    </div>
  </div>
</template>
