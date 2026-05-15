<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import type { ActivityItem } from '../../types'

withDefaults(
  defineProps<{
    items: ActivityItem[]
    compact?: boolean
    showEntity?: boolean
    showActions?: boolean
  }>(),
  { compact: false, showEntity: true, showActions: false },
)

const emit = defineEmits<{
  edit: [item: ActivityItem]
  delete: [id: string]
}>()

const { t, locale } = useI18n()
const router = useRouter()

const typeIcons: Record<string, { bg: string; dot: string }> = {
  call: { bg: 'bg-blue-100', dot: 'bg-blue-600' },
  email: { bg: 'bg-green-100', dot: 'bg-green-600' },
  meeting: { bg: 'bg-purple-100', dot: 'bg-purple-600' },
  deal_won: { bg: 'bg-emerald-100', dot: 'bg-emerald-600' },
  deal_lost: { bg: 'bg-red-100', dot: 'bg-red-600' },
  deal_created: { bg: 'bg-indigo-100', dot: 'bg-indigo-600' },
  stage_changed: { bg: 'bg-amber-100', dot: 'bg-amber-600' },
  lead_created: { bg: 'bg-indigo-100', dot: 'bg-indigo-600' },
  note: { bg: 'bg-gray-100', dot: 'bg-gray-600' },
}

function iconStyle(type: string) {
  return typeIcons[type] ?? { bg: 'bg-gray-100', dot: 'bg-gray-500' }
}

function formatTime(ts: string): string {
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ts
  const now = new Date()
  const diffHours = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60))
  locale.value
  if (diffHours < 1) return t('activity.justNow')
  if (diffHours < 24) return t('activity.hoursAgo', { n: diffHours })
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return t('activity.daysAgo', { n: diffDays })
  return d.toLocaleString()
}

function typeLabel(type: string): string {
  locale.value
  const key = `activityTypes.${type}`
  const translated = t(key)
  if (translated === key) {
    return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
  }
  return translated
}

function goToEntity(item: ActivityItem) {
  if (!item.entityLink) return
  router.push(item.entityLink)
}
</script>

<template>
  <div v-if="items.length === 0" class="text-sm text-gray-500 py-8 text-center">
    {{ t('activities.empty') }}
  </div>
  <ul v-else class="space-y-0">
    <li
      v-for="(activity, index) in items"
      :key="activity.id"
      class="relative flex gap-3"
      :class="compact ? 'pb-3' : 'pb-6'"
    >
      <div
        v-if="index < items.length - 1"
        class="absolute left-4 top-9 bottom-0 w-px bg-gray-200"
        aria-hidden="true"
      />
      <div
        class="relative z-10 w-8 h-8 rounded-full flex items-center justify-center shrink-0"
        :class="iconStyle(activity.type).bg"
      >
        <span class="w-2 h-2 rounded-full" :class="iconStyle(activity.type).dot" />
      </div>
      <div class="flex-1 min-w-0 pt-0.5">
        <p class="text-sm text-gray-800" :class="{ 'line-clamp-2': compact }">
          {{ activity.description }}
        </p>
        <div class="flex flex-wrap items-center gap-2 mt-1">
          <span class="badge badge-gray text-[10px]">{{ typeLabel(activity.type) }}</span>
          <span v-if="activity.isSystem" class="badge bg-amber-50 text-amber-800 text-[10px]">
            {{ t('activities.systemBadge') }}
          </span>
          <span class="text-xs text-gray-400">{{ formatTime(activity.timestamp) }}</span>
        </div>
        <button
          v-if="showEntity && activity.entityLabel"
          type="button"
          class="text-xs text-indigo-600 hover:underline mt-1 text-left"
          @click="goToEntity(activity)"
        >
          {{ activity.entityType === 'deal' ? t('globalSearch.types.deal') : t('globalSearch.types.contact') }}:
          {{ activity.entityLabel }}
        </button>
        <div v-if="showActions && !activity.isSystem" class="flex gap-2 mt-2">
          <button type="button" class="text-xs text-indigo-600" @click="emit('edit', activity)">
            {{ t('activities.edit') }}
          </button>
          <button type="button" class="text-xs text-red-600" @click="emit('delete', activity.id)">
            {{ t('common.delete') }}
          </button>
        </div>
      </div>
    </li>
  </ul>
</template>
