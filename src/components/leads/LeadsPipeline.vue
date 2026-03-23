<script setup lang="ts">
import { useLeadsStore } from '../../stores/leads'
import { useAI } from '../../composables/useAI'
import LeadColumn from './LeadColumn.vue'

const leadsStore = useLeadsStore()
const { analyze } = useAI()

const stageColors: Record<string, string> = {
  New: 'bg-blue-400',
  Qualified: 'bg-indigo-400',
  Proposal: 'bg-purple-400',
  Negotiation: 'bg-orange-400',
  Won: 'bg-green-400',
  Lost: 'bg-red-400',
}

function handleAnalyze(leadId: string) {
  const lead = leadsStore.getLead(leadId)
  if (lead) {
    analyze('lead', leadId, { ...lead })
  }
}
</script>

<template>
  <div class="flex gap-4 overflow-x-auto pb-4">
    <LeadColumn
      v-for="stage in leadsStore.stages"
      :key="stage"
      :stage="stage"
      :leads="leadsStore.leadsByStage[stage]"
      :color="stageColors[stage]"
      @analyze="handleAnalyze"
    />
  </div>
</template>
