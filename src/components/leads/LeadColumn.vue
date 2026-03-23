<script setup lang="ts">
import type { Lead } from '../../types'
import LeadCard from './LeadCard.vue'

defineProps<{
  stage: string
  leads: Lead[]
  color: string
}>()

defineEmits<{
  analyze: [id: string]
}>()

function formatTotal(leads: Lead[]): string {
  const total = leads.reduce((sum, l) => sum + l.value, 0)
  if (total >= 1000) return `$${(total / 1000).toFixed(0)}K`
  return `$${total}`
}
</script>

<template>
  <div class="flex flex-col min-w-[260px] w-[260px]">
    <div class="flex items-center justify-between mb-3 px-1">
      <div class="flex items-center gap-2">
        <div class="w-2.5 h-2.5 rounded-full" :class="color"></div>
        <h3 class="text-sm font-semibold text-gray-700">{{ stage }}</h3>
        <span class="text-xs text-gray-400 bg-gray-100 rounded-full px-2 py-0.5">{{ leads.length }}</span>
      </div>
      <span class="text-xs font-medium text-gray-500">{{ formatTotal(leads) }}</span>
    </div>
    <div class="flex-1 space-y-2 overflow-y-auto pb-4">
      <LeadCard
        v-for="lead in leads"
        :key="lead.id"
        :lead="lead"
        @analyze="$emit('analyze', $event)"
      />
      <div v-if="leads.length === 0" class="text-center py-8 text-xs text-gray-400">
        No leads
      </div>
    </div>
  </div>
</template>
