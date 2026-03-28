<script setup lang="ts">
import { useDealsStore } from '../../stores/deals'
import type { Deal } from '../../types'

const dealsStore = useDealsStore()
const stages: Deal['stage'][] = ['New Request', 'Qualified', 'Discovery', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']

function onDragStart(event: DragEvent, deal: Deal) {
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('dealId', deal.id)
  }
}

function onDrop(event: DragEvent, stage: Deal['stage']) {
  const dealId = event.dataTransfer?.getData('dealId')
  if (dealId) {
    dealsStore.updateDealStage(dealId, stage)
  }
}

function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

function getStageColor(stage: string): string {
  switch (stage) {
    case 'New Request': return 'bg-cyan-100 text-cyan-700'
    case 'Qualified': return 'bg-teal-100 text-teal-700'
    case 'Discovery': return 'bg-blue-100 text-blue-700'
    case 'Proposal': return 'bg-purple-100 text-purple-700'
    case 'Negotiation': return 'bg-orange-100 text-orange-700'
    case 'Closed Won': return 'bg-green-100 text-green-700'
    case 'Closed Lost': return 'bg-red-100 text-red-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}
</script>

<template>
  <div class="flex gap-4 overflow-x-auto pb-4 h-[600px] w-full snap-x">
    <!-- Stage Column -->
    <div
      v-for="stage in stages"
      :key="stage"
      class="bg-gray-50 rounded-xl min-w-[300px] w-[300px] flex flex-col border border-gray-200 shadow-inner snap-center"
      @dragover.prevent
      @dragenter.prevent
      @drop="onDrop($event, stage)"
    >
      <!-- Column Header -->
      <div class="p-4 border-b border-gray-200 bg-white rounded-t-xl shrink-0 sticky top-0 z-10">
        <div class="flex items-center justify-between mb-1">
          <h3 class="font-semibold text-gray-800 text-sm">{{ stage }}</h3>
          <span class="text-xs font-bold px-2 py-0.5 rounded-full" :class="getStageColor(stage)">
            {{ dealsStore.deals.filter(d => d.stage === stage).length }}
          </span>
        </div>
        <div class="text-xs text-gray-500 font-medium tracking-wide">
          {{ formatCurrency(dealsStore.deals.filter(d => d.stage === stage).reduce((sum, d) => sum + d.value, 0)) }}
        </div>
      </div>

      <!-- Scrollable Cards Container -->
      <div class="flex-1 overflow-y-auto p-3 space-y-3">
        <!-- Draggable Card -->
        <div
          v-for="deal in dealsStore.deals.filter(d => d.stage === stage)"
          :key="deal.id"
          class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-move hover:shadow-md hover:border-indigo-300 transition-all active:cursor-grabbing active:scale-[0.98]"
          draggable="true"
          @dragstart="onDragStart($event, deal)"
        >
          <div class="flex justify-between items-start mb-2">
            <div class="font-medium text-gray-900 text-sm leading-tight">{{ deal.title }}</div>
            <div 
              class="w-6 h-6 bg-indigo-50 rounded-full flex items-center justify-center shrink-0 border border-indigo-100 ml-2"
              title="Seller ID"
            >
              <span class="text-[10px] font-bold text-indigo-700 uppercase">{{ deal.sellerId.charAt(0) }}</span>
            </div>
          </div>
          <div class="text-xs text-gray-500 mb-3 flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
            {{ deal.contactId }}
          </div>
          <div class="mt-auto pt-3 border-t border-gray-50 flex items-center justify-between">
            <span class="font-bold text-emerald-600 text-sm">{{ formatCurrency(deal.value) }}</span>
            <span class="text-[10px] text-gray-400 font-medium">{{ deal.closedAt ? new Date(deal.closedAt).toLocaleDateString() : 'Active' }}</span>
          </div>
        </div>

        <!-- Empty state placeholder -->
        <div v-if="dealsStore.deals.filter(d => d.stage === stage).length === 0" class="h-20 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center text-xs justify-center text-gray-400 font-medium">
          Drop deals right here
        </div>
      </div>
    </div>
  </div>
</template>
