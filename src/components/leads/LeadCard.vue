<script setup lang="ts">
import type { Lead } from '../../types'
import { useContactsStore } from '../../stores/contacts'
import { useSellersStore } from '../../stores/sellers'
import { computed } from 'vue'

const props = defineProps<{
  lead: Lead
}>()

defineEmits<{
  analyze: [id: string]
}>()

const contactsStore = useContactsStore()
const sellersStore = useSellersStore()

const contact = computed(() => contactsStore.getContact(props.lead.contactId))
const seller = computed(() => sellersStore.getSeller(props.lead.assignedTo))

function formatCurrency(val: number): string {
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}
</script>

<template>
  <div class="bg-white rounded-lg border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
    <div class="flex items-start justify-between mb-2">
      <h4 class="text-sm font-medium text-gray-800 leading-tight">{{ lead.title }}</h4>
      <button
        @click.stop="$emit('analyze', lead.id)"
        class="p-1 text-indigo-400 hover:text-indigo-600 rounded shrink-0"
        title="AI Analysis"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
      </button>
    </div>

    <div class="text-lg font-bold text-gray-900 mb-2">{{ formatCurrency(lead.value) }}</div>

    <div class="flex items-center gap-2 mb-2">
      <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all"
          :class="lead.probability >= 70 ? 'bg-green-400' : lead.probability >= 40 ? 'bg-yellow-400' : 'bg-red-400'"
          :style="{ width: `${lead.probability}%` }"
        ></div>
      </div>
      <span class="text-xs font-medium text-gray-500">{{ lead.probability }}%</span>
    </div>

    <div class="flex items-center justify-between text-xs text-gray-500">
      <div class="flex items-center gap-1.5">
        <div class="w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center">
          <span class="text-[10px] font-medium text-gray-600">{{ contact?.avatar ?? '?' }}</span>
        </div>
        <span class="truncate max-w-[80px]">{{ contact?.name ?? 'Unknown' }}</span>
      </div>
      <span class="truncate max-w-[70px]">{{ seller?.name ?? 'Unassigned' }}</span>
    </div>
  </div>
</template>
