<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDealsStore } from '../../stores/deals'
import { usePeriodFilterStore } from '../../stores/periodFilter'

const { t } = useI18n()
const dealsStore = useDealsStore()
const periodFilter = usePeriodFilterStore()

const maxValue = computed(() =>
  Math.max(1, ...dealsStore.monthlyWonRevenue.map((m) => m.value)),
)

function barHeight(value: number): string {
  return `${(value / maxValue.value) * 100}%`
}

function formatValue(value: number): string {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`
  return `$${value}`
}
</script>

<template>
  <div class="card">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-sm font-semibold text-gray-800">{{ t('revenueChart.title') }}</h3>
      <span class="text-xs text-gray-400">{{ t('revenueChart.subtitle', { period: periodFilter.displayLabel }) }}</span>
    </div>
    <div class="flex items-end gap-3 h-48">
      <div
        v-for="month in dealsStore.monthlyWonRevenue"
        :key="month.key"
        class="flex-1 flex flex-col items-center gap-2"
      >
        <span class="text-xs font-medium text-gray-600">{{ formatValue(month.value) }}</span>
        <div class="w-full bg-gray-100 rounded-t-md relative flex-1 flex items-end">
          <div
            class="w-full rounded-t-md transition-all duration-500"
            :class="month.isSelected ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-indigo-500 hover:bg-indigo-600'"
            :style="{ height: barHeight(month.value) }"
          ></div>
        </div>
        <span class="text-[10px]" :class="month.isSelected ? 'text-indigo-700 font-semibold' : 'text-gray-500'">
          {{ month.label }}
        </span>
      </div>
    </div>
  </div>
</template>
