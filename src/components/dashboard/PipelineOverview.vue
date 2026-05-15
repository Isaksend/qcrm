<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDealsStore } from '../../stores/deals'
import { dealStageLabel } from '../../i18n/stages'

const { t, locale } = useI18n()
const dealsStore = useDealsStore()

const funnelStages = computed(() => {
  const stages = ['New Request', 'Qualified', 'Discovery', 'Proposal', 'Negotiation', 'Closed Won']
  return stages.map((stage) => {
    const stageDeals = dealsStore.dealsInPeriod.filter((d) => d.stage === stage)
    const value = stageDeals.reduce((sum, d) => sum + d.value, 0)
    return { stage, count: stageDeals.length, value }
  })
})

const maxCount = computed(() => Math.max(...funnelStages.value.map((s) => s.count), 1))

const stageColors: Record<string, string> = {
  'New Request': 'bg-cyan-400',
  Qualified: 'bg-teal-400',
  Discovery: 'bg-blue-400',
  Proposal: 'bg-purple-400',
  Negotiation: 'bg-orange-400',
  'Closed Won': 'bg-green-400',
}

function formatValue(val: number): string {
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

function labelFor(stage: string) {
  locale.value
  return dealStageLabel(t, stage)
}
</script>

<template>
  <div class="card">
    <h3 class="text-sm font-semibold text-gray-800 mb-4">{{ t('pipeline.title') }}</h3>
    <div class="space-y-3">
      <div v-for="s in funnelStages" :key="s.stage" class="flex items-center gap-3">
        <span class="text-xs font-medium text-gray-500 w-24 shrink-0 truncate" :title="labelFor(s.stage)">{{ labelFor(s.stage) }}</span>
        <div class="flex-1 h-8 bg-gray-100 rounded-md overflow-hidden relative">
          <div
            class="h-full rounded-md transition-all duration-500"
            :class="stageColors[s.stage] ?? 'bg-gray-300'"
            :style="{ width: `${(s.count / maxCount) * 100}%` }"
          ></div>
        </div>
        <div class="text-xs text-gray-600 w-16 text-right shrink-0">{{ s.count }}</div>
        <div class="text-xs font-medium text-gray-700 w-14 text-right shrink-0">{{ formatValue(s.value) }}</div>
      </div>
    </div>
  </div>
</template>
