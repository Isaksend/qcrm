<script setup lang="ts">
import { useAIStore } from '../stores/ai'
import AIInsightCard from '../components/ai/AIInsightCard.vue'
import { onMounted } from 'vue'

const aiStore = useAIStore()

onMounted(() => {
  aiStore.fetchInsights()
})

const filterOptions = [
  { value: 'all', label: 'All' },
  { value: 'contact', label: 'Contacts' },
  { value: 'lead', label: 'Leads' },
  { value: 'deal', label: 'Deals' },
  { value: 'general', label: 'General' },
]
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">AI Insights</h1>
        <p class="text-sm text-gray-500 mt-1">AI-generated analysis and recommendations across your CRM.</p>
      </div>
      <span class="badge badge-indigo">{{ aiStore.filteredInsights.length }} insights</span>
    </div>

    <!-- Filters -->
    <div class="flex items-center gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
      <button
        v-for="opt in filterOptions"
        :key="opt.value"
        @click="aiStore.filterType = opt.value"
        class="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
        :class="aiStore.filterType === opt.value ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Insights Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <AIInsightCard
        v-for="insight in aiStore.filteredInsights"
        :key="insight.id"
        :insight="insight"
      />
    </div>

    <div v-if="aiStore.filteredInsights.length === 0" class="text-center py-16 text-sm text-gray-400">
      No insights found for the selected filter.
    </div>
  </div>
</template>
