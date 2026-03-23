<script setup lang="ts">
import { useDealsStore } from '../../stores/deals'
import DealRow from './DealRow.vue'
import type { Deal } from '../../types'

const dealsStore = useDealsStore()

const columns: { key: keyof Deal; label: string }[] = [
  { key: 'title', label: 'Deal' },
  { key: 'contactId', label: 'Company' },
  { key: 'value', label: 'Value' },
  { key: 'stage', label: 'Stage' },
  { key: 'sellerId', label: 'Seller' },
  { key: 'closedAt', label: 'Closed' },
]
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <table class="w-full">
      <thead>
        <tr class="border-b border-gray-100">
          <th
            v-for="col in columns"
            :key="col.key"
            @click="dealsStore.setSort(col.key)"
            class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 select-none"
          >
            <div class="flex items-center gap-1">
              {{ col.label }}
              <svg
                v-if="dealsStore.sortField === col.key"
                class="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  :d="dealsStore.sortDirection === 'asc' ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'"
                />
              </svg>
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">
        <DealRow v-for="deal in dealsStore.sortedDeals" :key="deal.id" :deal="deal" />
      </tbody>
    </table>
  </div>
</template>
