<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useContactsStore } from '../../stores/contacts'
import { useDealsStore } from '../../stores/deals'
import { getCountryByIso2 } from '../../lib/countries'
import { dealStageLabel } from '../../i18n/stages'
import type { Contact } from '../../types'

const { t, locale } = useI18n()
const contactsStore = useContactsStore()
const dealsStore = useDealsStore()

const editOpen = ref(false)
const editForm = ref({
  name: '',
  email: '',
  phone: '',
  company: '',
  status: 'Active' as Contact['status'],
})

watch(
  () => contactsStore.selectedContact,
  (c) => {
    if (!c) return
    editForm.value = {
      name: c.name,
      email: c.email,
      phone: c.phone,
      company: c.company,
      status: c.status,
    }
  },
  { immediate: true },
)

async function saveEdits() {
  const c = contact.value
  if (!c) return
  await contactsStore.updateContact(c.id, { ...editForm.value })
  editOpen.value = false
}

async function removeContact() {
  const c = contact.value
  if (!c || !confirm(t('contactDetail.confirmDelete'))) return
  await contactsStore.deleteContact(c.id)
  await dealsStore.fetchDeals()
}

const contact = computed(() => contactsStore.selectedContact)

const locationLine = computed(() => {
  const c = contact.value
  if (!c) return ''
  const parts: string[] = []
  if (c.city) parts.push(c.city)
  if (c.country_iso2) {
    parts.push(getCountryByIso2(c.country_iso2)?.name || c.country_iso2)
  }
  return parts.join(', ')
})

const contactDeals = computed(() => {
  if (!contact.value) return []
  return dealsStore.deals.filter((d) => d.contactId === contact.value!.id)
})

const statusClass: Record<string, string> = {
  Active: 'badge-green',
  Inactive: 'badge-red',
  Prospect: 'badge-yellow',
}

const stageClass: Record<string, string> = {
  'New Request': 'badge-blue',
  Qualified: 'badge-indigo',
  Discovery: 'badge-blue',
  Proposal: 'badge-yellow',
  Negotiation: 'badge-yellow',
  'Closed Won': 'badge-green',
  'Closed Lost': 'badge-red',
}

function formatCurrency(val: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val)
}

function contactStatusLabel(status: string) {
  locale.value
  const k = status.toLowerCase() as 'active' | 'inactive' | 'prospect'
  return t(`contactStatus.${k}`)
}

function roleCompanyLine(c: { role: string; company: string }) {
  return t('contactDetail.roleCompanyLine', { role: c.role, company: c.company })
}

function dealStage(s: string) {
  return dealStageLabel(t, s)
}
</script>

<template>
  <div v-if="contact" class="fixed inset-0 z-30 flex justify-end">
    <div class="absolute inset-0 bg-black/20" @click="contactsStore.selectedContactId = null"></div>
    <div class="relative w-full max-w-lg bg-white shadow-xl overflow-y-auto animate-slide-in">
      <div class="p-6">
        <div class="flex items-start justify-between gap-3 mb-6">
          <div class="flex items-center gap-4 min-w-0">
            <div class="w-14 h-14 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
              <span class="text-indigo-600 text-lg font-semibold">{{ contact.avatar }}</span>
            </div>
            <div class="min-w-0">
              <h2 class="text-lg font-semibold text-gray-900">{{ contact.name }}</h2>
              <p class="text-sm text-gray-500">{{ roleCompanyLine(contact) }}</p>
              <span class="badge mt-1" :class="statusClass[contact.status]">{{ contactStatusLabel(contact.status) }}</span>
            </div>
          </div>
          <div class="flex items-start gap-2 shrink-0">
            <button
              type="button"
              class="text-xs font-medium text-indigo-600 px-2 py-1 rounded-lg hover:bg-indigo-50"
              @click="editOpen = true"
            >
              {{ t('contactDetail.edit') }}
            </button>
            <button
              type="button"
              class="text-xs font-medium text-red-600 px-2 py-1 rounded-lg hover:bg-red-50"
              @click="removeContact"
            >
              {{ t('contactDetail.delete') }}
            </button>
            <button
              @click="contactsStore.selectedContactId = null"
              class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="space-y-3 mb-6">
          <div class="flex items-center gap-3 text-sm">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span class="text-gray-600">{{ contact.email }}</span>
          </div>
          <div class="flex items-center gap-3 text-sm">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span class="text-gray-600">{{ contact.phone }}</span>
          </div>
          <div v-if="locationLine" class="flex items-center gap-3 text-sm">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span class="text-gray-600">{{ locationLine }}</span>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4 mb-6">
          <div class="bg-gray-50 rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-1">{{ t('contactDetail.totalRevenue') }}</div>
            <div class="text-lg font-semibold text-gray-900">{{ formatCurrency(contact.revenue) }}</div>
          </div>
          <div class="bg-gray-50 rounded-lg p-3">
            <div class="text-xs text-gray-500 mb-1">{{ t('contactDetail.lastContact') }}</div>
            <div class="text-lg font-semibold text-gray-900">{{ contact.lastContact }}</div>
          </div>
        </div>

        <div class="mb-6">
          <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{{ t('contactDetail.tags') }}</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in contact.tags" :key="tag" class="badge badge-indigo">{{ tag }}</span>
          </div>
        </div>

        <div class="mb-6">
          <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{{ t('contactDetail.relatedDeals') }}</h3>
          <div v-if="contactDeals.length" class="space-y-2">
            <div v-for="deal in contactDeals" :key="deal.id" class="flex items-center justify-between bg-gray-50 rounded-lg p-3">
              <div>
                <div class="text-sm font-medium text-gray-800">{{ deal.title }}</div>
                <span class="badge mt-1" :class="stageClass[deal.stage]">{{ dealStage(deal.stage) }}</span>
              </div>
              <div class="text-sm font-semibold text-gray-700">{{ formatCurrency(deal.value) }}</div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">{{ t('contactDetail.noDeals') }}</p>
        </div>

        <div v-if="editOpen" class="border border-gray-200 rounded-xl p-4 mb-6 space-y-3 bg-gray-50">
          <h3 class="text-sm font-semibold text-gray-800">{{ t('contactDetail.editTitle') }}</h3>
          <input v-model="editForm.name" class="w-full px-3 py-2 border rounded-lg text-sm" />
          <input v-model="editForm.email" class="w-full px-3 py-2 border rounded-lg text-sm" />
          <input v-model="editForm.phone" class="w-full px-3 py-2 border rounded-lg text-sm" />
          <input v-model="editForm.company" class="w-full px-3 py-2 border rounded-lg text-sm" />
          <select v-model="editForm.status" class="w-full px-3 py-2 border rounded-lg text-sm">
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
            <option value="Prospect">Prospect</option>
          </select>
          <div class="flex gap-2 justify-end">
            <button type="button" class="text-sm text-gray-600" @click="editOpen = false">{{ t('common.cancel') }}</button>
            <button type="button" class="btn-primary text-sm" @click="saveEdits">{{ t('contactDetail.saveEdits') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.25s ease-out;
}
@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}
</style>
