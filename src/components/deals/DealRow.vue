<script setup lang="ts">
import type { Deal } from '../../types'
import { useContactsStore } from '../../stores/contacts'
import { useSellersStore } from '../../stores/sellers'
import { computed } from 'vue'

const props = defineProps<{
  deal: Deal
}>()

const contactsStore = useContactsStore()
const sellersStore = useSellersStore()

const contact = computed(() => contactsStore.getContact(props.deal.contactId))
const seller = computed(() => sellersStore.getSeller(props.deal.sellerId))

const stageClass: Record<string, string> = {
  Discovery: 'badge-blue',
  Proposal: 'badge-yellow',
  Negotiation: 'badge-yellow',
  'Closed Won': 'badge-green',
  'Closed Lost': 'badge-red',
}

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val)
}
</script>

<template>
  <tr class="hover:bg-gray-50 transition-colors">
    <td class="px-4 py-3">
      <div class="text-sm font-medium text-gray-900">{{ deal.title }}</div>
    </td>
    <td class="px-4 py-3 text-sm text-gray-600">{{ contact?.company ?? '—' }}</td>
    <td class="px-4 py-3 text-sm font-medium text-gray-700">{{ formatCurrency(deal.value) }}</td>
    <td class="px-4 py-3">
      <span class="badge" :class="stageClass[deal.stage]">{{ deal.stage }}</span>
    </td>
    <td class="px-4 py-3 text-sm text-gray-600">{{ seller?.name ?? '—' }}</td>
    <td class="px-4 py-3 text-sm text-gray-500">{{ deal.closedAt ?? 'Open' }}</td>
  </tr>
</template>
