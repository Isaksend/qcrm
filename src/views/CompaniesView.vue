<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { apiUrl } from '../lib/api'

const { t } = useI18n()
const authStore = useAuthStore()
const companies = ref<{ id: string; name: string; created_at?: string }[]>([])
const editName = ref('')
const editingId = ref<string | null>(null)
const error = ref('')

async function load() {
  error.value = ''
  try {
    const res = await fetch(apiUrl('/api/companies'), {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!res.ok) {
      error.value = t('companies.loadError')
      return
    }
    companies.value = await res.json()
  } catch {
    error.value = t('companies.loadError')
  }
}

function startEdit(c: { id: string; name: string }) {
  editingId.value = c.id
  editName.value = c.name
}

async function saveCompany(id: string) {
  const res = await fetch(apiUrl(`/api/companies/${id}`), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authStore.token}`,
    },
    body: JSON.stringify({ name: editName.value }),
  })
  if (res.ok) {
    editingId.value = null
    await load()
  }
}

async function removeCompany(id: string) {
  if (!confirm(t('companies.confirmDelete'))) return
  const res = await fetch(apiUrl(`/api/companies/${id}`), {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${authStore.token}` },
  })
  if (res.ok) await load()
}

onMounted(load)
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ t('companies.title') }}</h1>
    <p class="text-sm text-gray-500 mb-6">{{ t('companies.subtitle') }}</p>
    <p v-if="error" class="text-sm text-red-600 mb-4">{{ error }}</p>
    <div class="space-y-3">
      <div v-for="c in companies" :key="c.id" class="card flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div v-if="editingId !== c.id" class="flex-1">
          <div class="font-semibold text-gray-900">{{ c.name }}</div>
          <div class="text-xs text-gray-400">ID: {{ c.id }}</div>
        </div>
        <div v-else class="flex-1 flex gap-2 items-center">
          <input v-model="editName" class="flex-1 px-3 py-2 border rounded-lg text-sm" />
          <button type="button" class="btn-primary text-sm px-3 py-2" @click="saveCompany(c.id)">{{ t('common.save') }}</button>
          <button type="button" class="text-sm text-gray-600 px-2" @click="editingId = null">{{ t('common.cancel') }}</button>
        </div>
        <div class="flex gap-2">
          <button v-if="editingId !== c.id" type="button" class="text-sm text-indigo-600 font-medium" @click="startEdit(c)">
            {{ t('companies.edit') }}
          </button>
          <button
            v-if="authStore.userRole === 'super_admin' && editingId !== c.id"
            type="button"
            class="text-sm text-red-600 font-medium"
            @click="removeCompany(c.id)"
          >
            {{ t('common.delete') }}
          </button>
        </div>
      </div>
      <p v-if="!companies.length && !error" class="text-sm text-gray-500">{{ t('companies.empty') }}</p>
    </div>
  </div>
</template>
