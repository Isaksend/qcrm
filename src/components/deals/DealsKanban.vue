<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDealsStore } from '../../stores/deals'
import { useContactsStore } from '../../stores/contacts'
import type { Deal } from '../../types'
import { apiUrl } from '../../lib/api'
import { dealStageLabel } from '../../i18n/stages'

const router = useRouter()
const { t, locale } = useI18n()
const dealsStore = useDealsStore()
const periodDeals = computed(() => dealsStore.dealsInPeriod)
const contactsStore = useContactsStore()
const stages: Deal['stage'][] = ['New Request', 'Qualified', 'Discovery', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']

const users = ref<any[]>([])
const userMap = computed(() => {
  const map: Record<string, string> = {}
  users.value.forEach(u => map[u.id] = u.name)
  return map
})

async function fetchUsers() {
  try {
    const res = await fetch(apiUrl('/api/users'), {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    if (res.ok) users.value = await res.json()
  } catch (e) { console.error(e) }
}

onMounted(() => {
  fetchUsers()
})

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

function stageTitle(stage: Deal['stage']): string {
  locale.value
  return dealStageLabel(t, stage)
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
    <div
      v-for="stage in stages"
      :key="stage"
      class="bg-gray-50 rounded-xl min-w-[300px] w-[300px] flex flex-col border border-gray-200 shadow-inner snap-center"
      @dragover.prevent
      @dragenter.prevent
      @drop="onDrop($event, stage)"
    >
      <div class="p-4 border-b border-gray-200 bg-white rounded-t-xl shrink-0 sticky top-0 z-10">
        <div class="flex items-center justify-between mb-1">
          <h3 class="font-semibold text-gray-800 text-sm">{{ stageTitle(stage) }}</h3>
          <span class="text-xs font-bold px-2 py-0.5 rounded-full" :class="getStageColor(stage)">
            {{ periodDeals.filter((d: Deal) => d.stage === stage).length }}
          </span>
        </div>
        <div class="text-xs text-gray-500 font-medium tracking-wide">
          {{ formatCurrency(periodDeals.filter((d: Deal) => d.stage === stage).reduce((sum: number, d: Deal) => sum + d.value, 0)) }}
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-3 space-y-3">
        <div
          v-for="deal in periodDeals.filter((d: Deal) => d.stage === stage)"
          :key="deal.id"
          class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 hover:shadow-md hover:border-indigo-300 transition-all active:scale-[0.98]"
          draggable="true"
          @dragstart="onDragStart($event, deal)"
        >
          <div class="flex items-start justify-between gap-2 mb-2">
            <div class="font-medium text-gray-900 text-sm leading-tight flex-1 min-w-0 line-clamp-2">
              {{ deal.title }}
            </div>
            <div class="flex items-center gap-1 shrink-0">
              <div
                class="flex items-center gap-1.5 px-2 py-0.5 bg-indigo-50 rounded-full border border-indigo-100 max-w-[88px]"
                :title="'Assigned to: ' + (deal.userId && userMap[deal.userId] ? userMap[deal.userId] : 'Unassigned')"
              >
                <div class="w-4 h-4 rounded-full bg-indigo-600 flex items-center justify-center text-[8px] text-white font-bold shrink-0">
                  {{ deal.userId && userMap[deal.userId] ? userMap[deal.userId].charAt(0) : 'U' }}
                </div>
                <span class="text-[10px] font-bold text-indigo-700 truncate">
                  {{ (deal.userId && userMap[deal.userId]) || '—' }}
                </span>
              </div>
              <button
                type="button"
                class="p-1 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
                :title="t('deals.openDetail')"
                @click.stop="router.push(`/deals/${deal.id}`)"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </button>
            </div>
          </div>
          <div class="text-xs text-indigo-600 font-bold mb-3 flex items-center gap-1.5 bg-indigo-50/50 py-1 px-2 rounded-lg border border-dashed border-indigo-100 italic">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
            {{ contactsStore.getContact(deal.contactId)?.name || 'Loading contact...' }}
          </div>
          <div class="mt-auto pt-3 border-t border-gray-50 flex items-center justify-between">
            <span class="font-bold text-emerald-600 text-sm">{{ formatCurrency(deal.value) }}</span>
            <span class="text-[10px] text-gray-400 font-medium">{{ deal.closedAt ? new Date(deal.closedAt).toLocaleDateString() : 'Active' }}</span>
          </div>
        </div>

        <div
          v-if="periodDeals.filter((d: Deal) => d.stage === stage).length === 0"
          class="h-20 border-2 border-dashed border-gray-200 rounded-lg flex items-center justify-center text-xs text-gray-400 font-medium"
        >
          {{ t('deals.kanbanEmpty') }}
        </div>
      </div>
    </div>
  </div>
</template>
