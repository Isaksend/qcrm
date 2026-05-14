<script setup lang="ts">
import type { Contact } from '../../types'

defineProps<{
  contact: Contact
}>()

defineEmits<{
  select: [id: string]
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
  </tr>
</template>
