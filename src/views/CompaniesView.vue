<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { apiUrl } from '../lib/api'
import { getSortedTimeZones } from '../lib/timezones'

const { t } = useI18n()
const authStore = useAuthStore()

type CompanyRow = {
  id: string
  name: string
  timezone?: string
  created_at?: string
}

const companies = ref<CompanyRow[]>([])
const editName = ref('')
const editTimezone = ref('UTC')
const tzFilter = ref('')
const editingId = ref<string | null>(null)
const error = ref('')

const allTimeZones = getSortedTimeZones()

const canEditCompanyTimezone = computed(
  () => authStore.userRole === 'admin' || authStore.userRole === 'super_admin',
)

const filteredTimezones = computed(() => {
  const q = tzFilter.value.trim().toLowerCase()
  if (!q) return allTimeZones
  return allTimeZones.filter((z) => z.toLowerCase().includes(q))
})

const selectTimezoneOptions = computed(() => {
  const cur = editTimezone.value
  const list = filteredTimezones.value
  if (cur && !list.includes(cur)) {
    return [cur, ...list].sort((a, b) => a.localeCompare(b))
  }
  return list
})

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

function startEdit(c: CompanyRow) {
  editingId.value = c.id
  editName.value = c.name
  editTimezone.value = (c.timezone && String(c.timezone).trim()) || 'UTC'
  tzFilter.value = ''
}

async function saveCompany(id: string) {
  const body: Record<string, string> = { name: editName.value }
  if (canEditCompanyTimezone.value) {
    body.timezone = editTimezone.value
  }
  const res = await fetch(apiUrl(`/api/companies/${id}`), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authStore.token}`,
    },
    body: JSON.stringify(body),
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
          <div class="text-xs text-gray-500 mt-0.5">
            {{ t('companies.timezoneLabel') }}: <span class="font-mono">{{ c.timezone || 'UTC' }}</span>
          </div>
          <div class="text-xs text-gray-400">ID: {{ c.id }}</div>
        </div>
        <div v-else class="flex-1 flex flex-col gap-3 min-w-0">
          <input v-model="editName" class="w-full px-3 py-2 border rounded-lg text-sm" />
          <template v-if="canEditCompanyTimezone">
            <label class="text-xs font-medium text-gray-600">{{ t('companies.timezoneLabel') }}</label>
            <input
              v-model="tzFilter"
              type="search"
              class="w-full px-3 py-2 border rounded-lg text-sm"
              :placeholder="t('companies.timezoneFilterPlaceholder')"
            />
            <select
              v-model="editTimezone"
              class="w-full px-3 py-2 border rounded-lg text-sm bg-white max-h-40"
            >
              <option v-for="z in selectTimezoneOptions" :key="z" :value="z">{{ z }}</option>
            </select>
            <p class="text-[11px] text-gray-500">{{ t('companies.timezoneHint') }}</p>
          </template>
          <div class="flex gap-2 flex-wrap">
            <button type="button" class="btn-primary text-sm px-3 py-2" @click="saveCompany(c.id)">{{ t('common.save') }}</button>
            <button type="button" class="text-sm text-gray-600 px-2" @click="editingId = null">{{ t('common.cancel') }}</button>
          </div>
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
