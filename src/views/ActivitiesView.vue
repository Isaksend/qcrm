<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { apiUrl } from '../lib/api'
import type { Activity } from '../types'

const { t } = useI18n()
const authStore = useAuthStore()
const items = ref<Activity[]>([])
const form = ref({ type: 'call', entityType: 'contact' as const, entityId: '', description: '', timestamp: '' })
const editing = ref<Activity | null>(null)

async function load() {
  const res = await fetch(apiUrl('/api/activities'), {
    headers: { Authorization: `Bearer ${authStore.token}` },
  })
  if (res.ok) items.value = await res.json()
}

async function add() {
  if (!form.value.entityId.trim()) return
  const ts = form.value.timestamp || new Date().toISOString()
  const res = await fetch(apiUrl('/api/activities'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authStore.token}`,
    },
    body: JSON.stringify({ ...form.value, timestamp: ts }),
  })
  if (res.ok) {
    form.value = { type: 'call', entityType: 'contact', entityId: '', description: '', timestamp: '' }
    await load()
  }
}

async function saveEdit() {
  if (!editing.value) return
  const res = await fetch(apiUrl(`/api/activities/${editing.value.id}`), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authStore.token}`,
    },
    body: JSON.stringify({
      type: editing.value.type,
      description: editing.value.description,
      timestamp: editing.value.timestamp,
    }),
  })
  if (res.ok) {
    editing.value = null
    await load()
  }
}

async function remove(id: string) {
  if (!confirm(t('activities.confirmDelete'))) return
  await fetch(apiUrl(`/api/activities/${id}`), {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${authStore.token}` },
  })
  await load()
}

onMounted(() => {
  form.value.timestamp = new Date().toISOString()
  load()
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('activities.title') }}</h1>
    <p class="text-sm text-gray-500 mb-6">{{ t('activities.subtitle') }}</p>

    <div class="card mb-6 space-y-3">
      <h3 class="text-sm font-semibold text-gray-800">{{ t('activities.new') }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <select v-model="form.type" class="px-3 py-2 border rounded-lg text-sm">
          <option value="call">{{ t('activities.types.call') }}</option>
          <option value="email">{{ t('activities.types.email') }}</option>
          <option value="meeting">{{ t('activities.types.meeting') }}</option>
          <option value="note">{{ t('activities.types.note') }}</option>
        </select>
        <select v-model="form.entityType" class="px-3 py-2 border rounded-lg text-sm">
          <option value="contact">contact</option>
          <option value="deal">deal</option>
        </select>
        <input v-model="form.entityId" class="px-3 py-2 border rounded-lg text-sm" :placeholder="t('activities.entityId')" />
        <input v-model="form.description" class="px-3 py-2 border rounded-lg text-sm" :placeholder="t('activities.description')" />
      </div>
      <button type="button" class="btn-primary text-sm" @click="add">{{ t('activities.add') }}</button>
    </div>

    <div class="card overflow-hidden !p-0">
      <table class="w-full text-left text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="py-2 px-3">{{ t('activities.col.type') }}</th>
            <th class="py-2 px-3">{{ t('activities.col.entity') }}</th>
            <th class="py-2 px-3">{{ t('activities.col.description') }}</th>
            <th class="py-2 px-3 w-28"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in items" :key="a.id" class="border-t border-gray-100">
            <td class="py-2 px-3">{{ a.type }}</td>
            <td class="py-2 px-3">{{ a.entityType }} / {{ a.entityId.slice(0, 8) }}…</td>
            <td class="py-2 px-3">{{ a.description }}</td>
            <td class="py-2 px-3 text-right space-x-2">
              <button type="button" class="text-indigo-600" @click="editing = { ...a }">{{ t('companies.edit') }}</button>
              <button type="button" class="text-red-600" @click="remove(a.id)">{{ t('common.delete') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="editing" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl p-6 max-w-md w-full space-y-3">
        <h3 class="font-semibold">{{ t('activities.edit') }}</h3>
        <input v-model="editing.type" class="w-full px-3 py-2 border rounded-lg text-sm" />
        <textarea v-model="editing.description" class="w-full px-3 py-2 border rounded-lg text-sm" rows="3" />
        <input v-model="editing.timestamp" class="w-full px-3 py-2 border rounded-lg text-sm" />
        <div class="flex justify-end gap-2">
          <button type="button" class="text-gray-600" @click="editing = null">{{ t('common.cancel') }}</button>
          <button type="button" class="btn-primary text-sm" @click="saveEdit">{{ t('common.save') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
