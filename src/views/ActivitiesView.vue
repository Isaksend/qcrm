<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../stores/contacts'
import { useDealsStore } from '../stores/deals'
import { useActivitiesStore } from '../stores/activities'
import ActivityTimeline from '../components/activities/ActivityTimeline.vue'
import ActivityEntityPicker from '../components/activities/ActivityEntityPicker.vue'
import type { ActivityItem } from '../types'

const { t } = useI18n()
const contactsStore = useContactsStore()
const dealsStore = useDealsStore()
const activitiesStore = useActivitiesStore()

const filterType = ref('')
const filterDays = ref<number | ''>('')
const filterMyOnly = ref(false)

const form = ref({
  type: 'call',
  entityType: 'contact' as 'contact' | 'deal',
  entityId: '',
  description: '',
})
const editing = ref<ActivityItem | null>(null)
const saving = ref(false)

async function load() {
  await activitiesStore.fetchList({
    limit: 200,
    type: filterType.value || undefined,
    days: filterDays.value === '' ? undefined : Number(filterDays.value),
    myOnly: filterMyOnly.value,
  })
}

async function add() {
  if (!form.value.entityId.trim() || !form.value.description.trim()) return
  saving.value = true
  try {
    await activitiesStore.create({
      type: form.value.type,
      entityType: form.value.entityType,
      entityId: form.value.entityId,
      description: form.value.description.trim(),
    })
    form.value.description = ''
    form.value.entityId = ''
    await load()
  } finally {
    saving.value = false
  }
}

async function saveEdit() {
  if (!editing.value) return
  saving.value = true
  try {
    await activitiesStore.update(editing.value.id, {
      type: editing.value.type,
      description: editing.value.description,
      timestamp: editing.value.timestamp,
    })
    editing.value = null
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(id: string) {
  if (!confirm(t('activities.confirmDelete'))) return
  await activitiesStore.remove(id)
  await load()
}

watch([filterType, filterDays, filterMyOnly], () => {
  void load()
})

onMounted(async () => {
  await Promise.all([contactsStore.fetchContacts(), dealsStore.fetchDeals(), load()])
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('activities.title') }}</h1>
    <p class="text-sm text-gray-500 mb-6">{{ t('activities.subtitle') }}</p>

    <div class="card mb-6 flex flex-wrap gap-3 items-end">
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ t('activities.filters.type') }}</label>
        <select v-model="filterType" class="px-3 py-2 border rounded-lg text-sm">
          <option value="">{{ t('activities.filters.allTypes') }}</option>
          <option value="call">{{ t('activities.types.call') }}</option>
          <option value="email">{{ t('activities.types.email') }}</option>
          <option value="meeting">{{ t('activities.types.meeting') }}</option>
          <option value="note">{{ t('activities.types.note') }}</option>
          <option value="stage_changed">{{ t('activityTypes.stage_changed') }}</option>
          <option value="deal_won">{{ t('activityTypes.deal_won') }}</option>
          <option value="deal_lost">{{ t('activityTypes.deal_lost') }}</option>
          <option value="deal_created">{{ t('activityTypes.deal_created') }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ t('activities.filters.period') }}</label>
        <select v-model="filterDays" class="px-3 py-2 border rounded-lg text-sm">
          <option value="">{{ t('activities.filters.allTime') }}</option>
          <option :value="7">{{ t('activities.filters.days7') }}</option>
          <option :value="30">{{ t('activities.filters.days30') }}</option>
          <option :value="90">{{ t('activities.filters.days90') }}</option>
        </select>
      </div>
      <label class="flex items-center gap-2 text-sm text-gray-700 pb-2">
        <input v-model="filterMyOnly" type="checkbox" class="rounded border-gray-300" />
        {{ t('activities.filters.myOnly') }}
      </label>
      <button type="button" class="btn-primary text-sm ml-auto" @click="load">
        {{ t('activities.refresh') }}
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="card lg:col-span-1 space-y-3 h-fit">
        <h3 class="text-sm font-semibold text-gray-800">{{ t('activities.new') }}</h3>
        <select v-model="form.type" class="w-full px-3 py-2 border rounded-lg text-sm">
          <option value="call">{{ t('activities.types.call') }}</option>
          <option value="email">{{ t('activities.types.email') }}</option>
          <option value="meeting">{{ t('activities.types.meeting') }}</option>
          <option value="note">{{ t('activities.types.note') }}</option>
        </select>
        <ActivityEntityPicker v-model="form.entityId" v-model:entity-type="form.entityType" />
        <textarea
          v-model="form.description"
          rows="3"
          class="w-full px-3 py-2 border rounded-lg text-sm"
          :placeholder="t('activities.description')"
        />
        <button type="button" class="btn-primary text-sm w-full" :disabled="saving" @click="add">
          {{ t('activities.add') }}
        </button>
      </div>

      <div class="card lg:col-span-2">
        <div v-if="activitiesStore.loading" class="text-sm text-gray-500 py-8 text-center">
          {{ t('common.loading') }}
        </div>
        <ActivityTimeline
          v-else
          :items="activitiesStore.items"
          :show-actions="true"
          @edit="editing = $event"
          @delete="remove"
        />
      </div>
    </div>

    <div v-if="editing" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl p-6 max-w-md w-full space-y-3">
        <h3 class="font-semibold">{{ t('activities.edit') }}</h3>
        <select v-model="editing.type" class="w-full px-3 py-2 border rounded-lg text-sm">
          <option value="call">{{ t('activities.types.call') }}</option>
          <option value="email">{{ t('activities.types.email') }}</option>
          <option value="meeting">{{ t('activities.types.meeting') }}</option>
          <option value="note">{{ t('activities.types.note') }}</option>
        </select>
        <textarea v-model="editing.description" class="w-full px-3 py-2 border rounded-lg text-sm" rows="3" />
        <input v-model="editing.timestamp" type="datetime-local" class="w-full px-3 py-2 border rounded-lg text-sm" />
        <div class="flex justify-end gap-2">
          <button type="button" class="text-gray-600" @click="editing = null">{{ t('common.cancel') }}</button>
          <button type="button" class="btn-primary text-sm" :disabled="saving" @click="saveEdit">
            {{ t('common.save') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
