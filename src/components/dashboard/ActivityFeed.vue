<script setup lang="ts">
import { activities } from '../../data/mock'

const typeIcons: Record<string, { color: string; bg: string }> = {
  call: { color: 'text-blue-600', bg: 'bg-blue-100' },
  email: { color: 'text-green-600', bg: 'bg-green-100' },
  meeting: { color: 'text-purple-600', bg: 'bg-purple-100' },
  deal_won: { color: 'text-emerald-600', bg: 'bg-emerald-100' },
  deal_lost: { color: 'text-red-600', bg: 'bg-red-100' },
  lead_created: { color: 'text-indigo-600', bg: 'bg-indigo-100' },
  note: { color: 'text-gray-600', bg: 'bg-gray-100' },
}

function formatTime(ts: string): string {
  const d = new Date(ts)
  const now = new Date()
  const diffHours = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60))
  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

function typeLabel(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<template>
  <div class="card">
    <h3 class="text-sm font-semibold text-gray-800 mb-4">Recent Activity</h3>
    <div class="space-y-3 max-h-80 overflow-y-auto">
      <div
        v-for="activity in activities"
        :key="activity.id"
        class="flex items-start gap-3"
      >
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5"
          :class="typeIcons[activity.type]?.bg ?? 'bg-gray-100'"
        >
          <!-- Call -->
          <svg v-if="activity.type === 'call'" class="w-4 h-4" :class="typeIcons[activity.type]?.color" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
          <!-- Email -->
          <svg v-if="activity.type === 'email'" class="w-4 h-4" :class="typeIcons[activity.type]?.color" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <!-- Meeting -->
          <svg v-if="activity.type === 'meeting'" class="w-4 h-4" :class="typeIcons[activity.type]?.color" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <!-- Deal Won -->
          <svg v-if="activity.type === 'deal_won'" class="w-4 h-4" :class="typeIcons[activity.type]?.color" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Deal Lost -->
          <svg v-if="activity.type === 'deal_lost'" class="w-4 h-4" :class="typeIcons[activity.type]?.color" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Lead Created -->
          <svg v-if="activity.type === 'lead_created'" class="w-4 h-4" :class="typeIcons[activity.type]?.color" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <!-- Note -->
          <svg v-if="activity.type === 'note'" class="w-4 h-4" :class="typeIcons[activity.type]?.color" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm text-gray-700 truncate">{{ activity.description }}</p>
          <div class="flex items-center gap-2 mt-0.5">
            <span class="badge badge-gray text-[10px]">{{ typeLabel(activity.type) }}</span>
            <span class="text-xs text-gray-400">{{ formatTime(activity.timestamp) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
