<script setup lang="ts">
import type { Contact } from '../../types'

defineProps<{
  contact: Contact
}>()

defineEmits<{
  select: [id: string]
  analyze: [id: string]
}>()

const statusClass: Record<string, string> = {
  Active: 'badge-green',
  Inactive: 'badge-red',
  Prospect: 'badge-yellow',
}

function formatRevenue(val: number): string {
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}
</script>

<template>
  <tr
    class="hover:bg-gray-50 cursor-pointer transition-colors"
    @click="$emit('select', contact.id)"
  >
    <td class="px-4 py-3">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
          <span class="text-indigo-600 text-xs font-semibold">{{ contact.avatar }}</span>
        </div>
        <div>
          <div class="text-sm font-medium text-gray-900">{{ contact.name }}</div>
          <div class="text-xs text-gray-500">{{ contact.email }}</div>
        </div>
      </div>
    </td>
    <td class="px-4 py-3 text-sm text-gray-600">{{ contact.company }}</td>
    <td class="px-4 py-3 text-sm text-gray-600">{{ contact.role }}</td>
    <td class="px-4 py-3">
      <span class="badge" :class="statusClass[contact.status]">{{ contact.status }}</span>
    </td>
    <td class="px-4 py-3 text-sm font-medium text-gray-700">{{ formatRevenue(contact.revenue) }}</td>
    <td class="px-4 py-3 text-sm text-gray-500">{{ contact.lastContact }}</td>
    <td class="px-4 py-3">
      <button
        @click.stop="$emit('analyze', contact.id)"
        class="p-1.5 text-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
        title="AI Analysis"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
      </button>
    </td>
  </tr>
</template>
