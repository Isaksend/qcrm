<script setup lang="ts">
import type { AIInsight } from '../../types'

defineProps<{
  insight: AIInsight
}>()

const categoryConfig: Record<string, { label: string; class: string }> = {
  risk: { label: 'Risk', class: 'badge-red' },
  opportunity: { label: 'Opportunity', class: 'badge-green' },
  coaching: { label: 'Coaching', class: 'badge-blue' },
  prediction: { label: 'Prediction', class: 'badge-yellow' },
  analysis: { label: 'Analysis', class: 'badge-indigo' },
}

const entityLabels: Record<string, string> = {
  contact: 'Contact',
  lead: 'Lead',
  deal: 'Deal',
  user: 'User',
  general: 'General',
}
</script>

<template>
  <div class="card hover:shadow-md transition-shadow">
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="badge" :class="categoryConfig[insight.category]?.class ?? 'badge-gray'">
          {{ categoryConfig[insight.category]?.label ?? insight.category }}
        </span>
        <span class="badge badge-gray">{{ entityLabels[insight.entityType] ?? insight.entityType }}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <div class="w-12 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full"
            :class="insight.confidence >= 80 ? 'bg-green-400' : insight.confidence >= 60 ? 'bg-yellow-400' : 'bg-red-400'"
            :style="{ width: `${insight.confidence}%` }"
          ></div>
        </div>
        <span class="text-xs font-medium text-gray-500">{{ insight.confidence }}%</span>
      </div>
    </div>

    <h3 class="text-sm font-semibold text-gray-900 mb-2">{{ insight.title }}</h3>
    <p class="text-sm text-gray-600 leading-relaxed mb-3">{{ insight.content }}</p>

    <div v-if="insight.suggestions.length" class="border-t border-gray-100 pt-3">
      <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Suggested Actions</h4>
      <ul class="space-y-1.5">
        <li
          v-for="(suggestion, i) in insight.suggestions"
          :key="i"
          class="flex items-start gap-2 text-sm text-gray-600"
        >
          <svg class="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
          {{ suggestion }}
        </li>
      </ul>
    </div>
  </div>
</template>
