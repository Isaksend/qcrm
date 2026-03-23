<script setup lang="ts">
import { computed } from 'vue'
import { monthlyRevenue } from '../../data/mock'

const maxValue = computed(() => Math.max(...monthlyRevenue.map((m) => m.value)))

function barHeight(value: number): string {
  return `${(value / maxValue.value) * 100}%`
}

function formatValue(value: number): string {
  return `$${(value / 1000).toFixed(0)}K`
}
</script>

<template>
  <div class="card">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-sm font-semibold text-gray-800">Revenue Trend</h3>
      <span class="text-xs text-gray-400">Last 6 months</span>
    </div>
    <div class="flex items-end gap-3 h-48">
      <div
        v-for="month in monthlyRevenue"
        :key="month.month"
        class="flex-1 flex flex-col items-center gap-2"
      >
        <span class="text-xs font-medium text-gray-600">{{ formatValue(month.value) }}</span>
        <div class="w-full bg-gray-100 rounded-t-md relative flex-1 flex items-end">
          <div
            class="w-full bg-indigo-500 rounded-t-md transition-all duration-500 hover:bg-indigo-600"
            :style="{ height: barHeight(month.value) }"
          ></div>
        </div>
        <span class="text-xs text-gray-500">{{ month.month }}</span>
      </div>
    </div>
  </div>
</template>
