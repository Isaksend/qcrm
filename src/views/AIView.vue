<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAIStore } from '../stores/ai'
import AIInsightCard from '../components/ai/AIInsightCard.vue'

const { t, locale } = useI18n()
const aiStore = useAIStore()

onMounted(() => {
  aiStore.fetchInsights()
})

const filterOptions = computed(() => {
  locale.value
  return [
    { value: 'all', label: t('ai.filters.all') },
    { value: 'contact', label: t('ai.filters.contact') },
    { value: 'lead', label: t('ai.filters.lead') },
    { value: 'deal', label: t('ai.filters.deal') },
    { value: 'general', label: t('ai.filters.general') },
  ]
})
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ t('ai.title') }}</h1>
        <p class="text-sm text-gray-500 mt-1">{{ t('ai.subtitle') }}</p>
      </div>
      <span class="badge badge-indigo">{{ t('ai.insightsCount', { n: aiStore.filteredInsights.length }) }}</span>
    </div>

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

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <AIInsightCard v-for="insight in aiStore.filteredInsights" :key="insight.id" :insight="insight" />
    </div>

    <div v-if="aiStore.filteredInsights.length === 0" class="text-center py-16 text-sm text-gray-400">
      {{ t('ai.empty') }}
    </div>
  </div>
</template>
