<script setup lang="ts">
import { ref } from 'vue'
import { useLeadsStore } from '../stores/leads'
import LeadsPipeline from '../components/leads/LeadsPipeline.vue'
import LeadForm from '../components/leads/LeadForm.vue'

const leadsStore = useLeadsStore()
const showForm = ref(false)

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Leads Pipeline</h1>
        <p class="text-sm text-gray-500 mt-1">Track and manage your sales pipeline.</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <div class="text-xs text-gray-500">Pipeline Value</div>
          <div class="text-lg font-bold text-gray-900">{{ formatCurrency(leadsStore.totalPipelineValue) }}</div>
        </div>
        <div class="text-right">
          <div class="text-xs text-gray-500">Weighted</div>
          <div class="text-lg font-bold text-indigo-600">{{ formatCurrency(leadsStore.weightedPipelineValue) }}</div>
        </div>
        <button @click="showForm = true" class="btn-primary">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/></svg>
          New Lead
        </button>
      </div>
    </div>

    <LeadsPipeline />
    <LeadForm v-if="showForm" @close="showForm = false" />
  </div>
</template>
