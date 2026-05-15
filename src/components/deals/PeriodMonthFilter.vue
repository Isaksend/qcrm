<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePeriodFilterStore } from '../../stores/periodFilter'

const { t, locale } = useI18n()
const period = usePeriodFilterStore()

const monthInput = computed({
  get: () => period.yearMonth,
  set: (v: string) => period.setYearMonth(v),
})
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <span class="text-xs font-medium text-gray-500">{{ t('periodFilter.label') }}</span>
    <button
      type="button"
      class="px-2 py-1 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
      :title="t('periodFilter.prev')"
      @click="period.shiftMonth(-1)"
    >
      ‹
    </button>
    <input
      :key="locale"
      v-model="monthInput"
      type="month"
      class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
      :aria-label="t('periodFilter.label')"
    />
    <button
      type="button"
      class="px-2 py-1 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
      :title="t('periodFilter.next')"
      @click="period.shiftMonth(1)"
    >
      ›
    </button>
    <span class="text-xs text-gray-500 hidden sm:inline">{{ period.displayLabel }}</span>
  </div>
</template>
